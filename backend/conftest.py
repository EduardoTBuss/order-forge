"""
Pytest configuration and fixtures for integration testing.

This conftest provides fixtures for testing against real services:
- PostgreSQL (test database: app_test)
- Azure Blob Storage (Azurite with test- prefix)
- CosmosDB/MongoDB (test database)

Usage:
    # Run all tests
    docker compose --profile test run --rm backend-test

    # Run specific test file
    docker compose --profile test run --rm backend-test \
        pytest src/app/modules/core/blob_storage/tests.py
"""

import base64
import os
from collections.abc import AsyncGenerator
from pathlib import Path

import psycopg2
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.app.services.blob_storage.service import BlobStorageService
from src.asgi import app
from src.settings import settings

# Check if running in test mode (set by docker-compose test profile or CI)
IS_TEST_ENV = os.getenv("IS_TEST_ENVIRONMENT", "false").lower() == "true"

# =============================================================================
# TEST DATABASE MANAGEMENT
# =============================================================================


def get_admin_db_connection():
    """Get connection to postgres database for admin operations."""
    return psycopg2.connect(
        host=settings.postgres_host,
        port=int(settings.postgres_port),
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        database="postgres",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-scoped fixture to ensure test database exists and has migrations.
    Only runs when IS_TEST_ENVIRONMENT is true.
    """
    if not IS_TEST_ENV:
        yield
        return

    conn = get_admin_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    test_db = settings.postgres_db

    # Check if test database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (test_db,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{test_db}"')
        print(f"\n✓ Created test database: {test_db}")
    else:
        print(f"\n✓ Test database exists: {test_db}")

    cur.close()
    conn.close()

    yield


# =============================================================================
# BLOB STORAGE CLEANUP
# =============================================================================

TEST_BLOB_PREFIX = "test-artifacts"
TEST_BLOB_CONTAINER = "test-container"


@pytest.fixture(scope="session")
def blob_service():
    """Provide blob storage service for tests."""
    return BlobStorageService(container_name=TEST_BLOB_CONTAINER)


@pytest.fixture(scope="session", autouse=True)
def setup_blob_container(blob_service):
    """Ensure blob container exists for tests."""
    try:
        # Container is auto-created on first upload, but we can ensure it exists
        blob_service._ensure_container_exists()
        yield
    finally:
        # Clean up test blobs after all tests
        if IS_TEST_ENV:
            try:
                blobs = blob_service.list_contents(TEST_BLOB_PREFIX, recursive=True)
                for blob in blobs:
                    try:
                        blob_service.delete(blob)
                    except Exception:
                        pass
                print(f"\n✓ Cleaned up test blobs with prefix: {TEST_BLOB_PREFIX}")
            except Exception as e:
                print(f"\n⚠ Could not clean up test blobs: {e}")


# =============================================================================
# HTTP CLIENT FIXTURES
# =============================================================================


@pytest.fixture()
def api_prefix(request) -> str:
    """Dynamically constructs the full endpoint prefix from the test module path."""
    test_path = Path(request.fspath)
    module_dir = test_path.parent

    parts = module_dir.parts
    if "core" in parts:
        core_index = parts.index("core")
        module_name = parts[core_index + 1]
        return f"/core/{module_name}".replace("_", "-")
    elif "custom" in parts:
        custom_index = parts.index("custom")
        module_name = parts[custom_index + 1]
        return f"/custom/{module_name}".replace("_", "-")
    else:
        module_name = module_dir.name
        return f"/{module_name}".replace("_", "-")


@pytest.fixture()
def headers():
    """Provides default HTTP headers with Authorization bearer token."""
    return {"Authorization": f"Bearer {settings.api_key.get_secret_value()}"}


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous HTTP client for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def example_image_base64() -> str:
    """Returns base64-encoded PNG image (for convert-to-pdf test)."""
    with open("assets/example_image.png", "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# =============================================================================
# COSMOSDB FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def cosmosdb_available() -> bool:
    """Check if CosmosDB/MongoDB is configured and accessible."""
    if not settings.azure_cosmosdb_connection_string:
        return False
    try:
        from pymongo import MongoClient

        client = MongoClient(
            settings.azure_cosmosdb_connection_string, serverSelectionTimeoutMS=2000
        )
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


@pytest.fixture()
def skip_if_no_cosmosdb(cosmosdb_available):
    """Skip test if CosmosDB is not available."""
    if not cosmosdb_available:
        pytest.skip("CosmosDB/MongoDB not available")


@pytest.fixture(scope="session", autouse=True)
def cleanup_cosmosdb(cosmosdb_available):
    """
    Clean up all test databases after all tests.

    In TEST mode, all databases are prefixed with the configured prefix
    (e.g., 'test_'). This fixture drops all databases with that prefix
    after tests complete, ensuring complete test isolation.
    """
    yield
    if cosmosdb_available and IS_TEST_ENV:
        try:
            from pymongo import MongoClient

            prefix = settings.cosmosdb_db_prefix
            if not prefix:
                print("\n⚠ No CosmosDB prefix configured, skipping cleanup")
                return

            client = MongoClient(settings.azure_cosmosdb_connection_string)
            db_names = client.list_database_names()

            # Drop all databases with the test prefix
            dropped = []
            for db_name in db_names:
                if db_name.startswith(prefix):
                    client.drop_database(db_name)
                    dropped.append(db_name)

            client.close()

            if dropped:
                print(f"\n✓ Cleaned up CosmosDB test databases: {dropped}")
            else:
                print(f"\n✓ No CosmosDB databases with prefix '{prefix}' to clean up")
        except Exception as e:
            print(f"\n⚠ Could not clean up CosmosDB: {e}")


# =============================================================================
# POSTGRESQL TRANSACTION FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def db_transaction():
    """
    Provides a database transaction that rolls back after the test.
    Use for tests that modify database state.
    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password.get_secret_value()}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()

    await engine.dispose()
