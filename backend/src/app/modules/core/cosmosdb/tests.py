"""
Integration tests for CosmosDB module.

These tests run against a real MongoDB instance (CosmosDB Mongo API emulator).
Tests are automatically skipped if MongoDB is not available.
"""

import pytest
from httpx import AsyncClient
from pymongo import MongoClient

from src.settings import settings

# Mark all tests in this module as requiring CosmosDB
pytestmark = [pytest.mark.cosmosdb, pytest.mark.integration]

TEST_DB_NAME = "test_integration_db"
TEST_COLL_NAME = "test_collection"


def cosmosdb_available() -> bool:
    """Check if CosmosDB/MongoDB is configured and accessible."""
    if not settings.azure_cosmosdb_connection_string:
        return False
    try:
        client = MongoClient(
            settings.azure_cosmosdb_connection_string, serverSelectionTimeoutMS=2000
        )
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


# Skip all tests if CosmosDB is not available
if not cosmosdb_available():
    pytestmark.append(
        pytest.mark.skip(reason="CosmosDB/MongoDB not available or not configured")
    )


@pytest.mark.asyncio
async def test_databases_list_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /databases returns list of databases."""
    response = await async_client.get(f"{api_prefix}/databases", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "databases" in data
    assert isinstance(data["databases"], list)


@pytest.mark.asyncio
async def test_database_create_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test POST /databases creates a new database with collections."""
    payload = {"db_name": TEST_DB_NAME, "coll_names": ["coll1", "coll2"]}

    response = await async_client.post(
        f"{api_prefix}/databases", json=payload, headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["db"] == TEST_DB_NAME
    assert "coll1" in data["collections"]
    assert "coll2" in data["collections"]


@pytest.mark.asyncio
async def test_collection_list_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test GET /collections returns list of collections in a database."""
    # First ensure database exists
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": [TEST_COLL_NAME]},
        headers=headers,
    )

    params = {"db_name": TEST_DB_NAME}
    response = await async_client.get(
        f"{api_prefix}/collections", params=params, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "collections" in data
    assert isinstance(data["collections"], list)


@pytest.mark.asyncio
async def test_collection_list_nonexistent_database(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test GET /collections returns 404 for non-existent database."""
    params = {"db_name": "nonexistent_db_xyz"}

    response = await async_client.get(
        f"{api_prefix}/collections", params=params, headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_item_create_and_read(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test creating and reading an item in CosmosDB."""
    # Ensure database/collection exists
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": [TEST_COLL_NAME]},
        headers=headers,
    )

    # Create item
    test_item = {"name": "Integration Test Item", "value": 42, "active": True}
    create_payload = {
        "db_name": TEST_DB_NAME,
        "coll_name": TEST_COLL_NAME,
        "item": test_item,
    }

    create_response = await async_client.post(
        f"{api_prefix}/items", json=create_payload, headers=headers
    )

    assert create_response.status_code == 201
    created_data = create_response.json()
    assert "item_id" in created_data

    # Read item back
    read_payload = {
        "db_name": TEST_DB_NAME,
        "coll_name": TEST_COLL_NAME,
        "filters": {"name": "Integration Test Item"},
    }

    read_response = await async_client.post(
        f"{api_prefix}/get-item", json=read_payload, headers=headers
    )

    assert read_response.status_code == 200
    read_data = read_response.json()
    assert read_data["item"]["name"] == "Integration Test Item"
    assert read_data["item"]["value"] == 42


@pytest.mark.asyncio
async def test_item_update(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test updating an item in CosmosDB."""
    # Ensure database/collection exists and create item
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": [TEST_COLL_NAME]},
        headers=headers,
    )

    test_item = {"name": "Update Test Item", "status": "pending"}
    await async_client.post(
        f"{api_prefix}/items",
        json={"db_name": TEST_DB_NAME, "coll_name": TEST_COLL_NAME, "item": test_item},
        headers=headers,
    )

    # Update item (MongoDB requires $set operator for field updates)
    update_payload = {
        "db_name": TEST_DB_NAME,
        "coll_name": TEST_COLL_NAME,
        "filters": {"name": "Update Test Item"},
        "update": {"$set": {"status": "completed"}},
    }

    response = await async_client.put(
        f"{api_prefix}/items", json=update_payload, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["item"]["status"] == "completed"


@pytest.mark.asyncio
async def test_items_delete(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test deleting items from CosmosDB."""
    # Ensure database/collection exists and create items
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": [TEST_COLL_NAME]},
        headers=headers,
    )

    # Create items to delete
    for i in range(3):
        await async_client.post(
            f"{api_prefix}/items",
            json={
                "db_name": TEST_DB_NAME,
                "coll_name": TEST_COLL_NAME,
                "item": {"name": f"Delete Test {i}", "to_delete": True},
            },
            headers=headers,
        )

    # Delete items
    delete_payload = {
        "db_name": TEST_DB_NAME,
        "coll_name": TEST_COLL_NAME,
        "filters": {"to_delete": True},
    }

    response = await async_client.request(
        "DELETE", f"{api_prefix}/items", json=delete_payload, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] >= 3


@pytest.mark.asyncio
async def test_items_query(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test querying items with filters and pagination."""
    # Ensure database/collection exists
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": [TEST_COLL_NAME]},
        headers=headers,
    )

    # Create test items
    for i in range(5):
        await async_client.post(
            f"{api_prefix}/items",
            json={
                "db_name": TEST_DB_NAME,
                "coll_name": TEST_COLL_NAME,
                "item": {"name": f"Query Test {i}", "category": "test_query"},
            },
            headers=headers,
        )

    # Query items
    query_payload = {
        "db_name": TEST_DB_NAME,
        "coll_name": TEST_COLL_NAME,
        "filters": {"category": "test_query"},
        "projection": {},
        "limit": 10,
        "block_id": None,
    }

    response = await async_client.post(
        f"{api_prefix}/query-items", json=query_payload, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "count" in data
    assert len(data["items"]) >= 5


@pytest.mark.asyncio
async def test_collection_reset(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test resetting (clearing) a collection."""
    # Ensure database/collection exists with items
    await async_client.post(
        f"{api_prefix}/databases",
        json={"db_name": TEST_DB_NAME, "coll_names": ["reset_test_coll"]},
        headers=headers,
    )

    await async_client.post(
        f"{api_prefix}/items",
        json={
            "db_name": TEST_DB_NAME,
            "coll_name": "reset_test_coll",
            "item": {"name": "To be reset"},
        },
        headers=headers,
    )

    # Reset collection
    reset_payload = {"db_name": TEST_DB_NAME, "coll_name": "reset_test_coll"}

    response = await async_client.post(
        f"{api_prefix}/collections/reset", json=reset_payload, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_unauthorized_request(
    async_client: AsyncClient,
    api_prefix: str,
) -> None:
    """Test requests without authorization header return 401/403."""
    response = await async_client.get(f"{api_prefix}/databases")

    assert response.status_code in [401, 403]
