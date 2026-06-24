"""
Integration tests for PostgreSQL module.

These tests run against a real PostgreSQL database (postgres_test).
The test database is created automatically by the test fixtures.
"""

import pytest
from httpx import AsyncClient

# Mark all tests in this module as requiring PostgreSQL
pytestmark = [pytest.mark.postgresql, pytest.mark.integration]


@pytest.mark.asyncio
async def test_get_database_name_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /database returns the current database name."""
    response = await async_client.get(f"{api_prefix}/database", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "database_name" in data
    # In test environment, should be one of the valid test database names
    assert data["database_name"] in ["postgres_test", "postgres", "app_test", "app"]


@pytest.mark.asyncio
async def test_get_allowed_tables_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /tables/allowed returns list of tables in the database."""
    response = await async_client.get(f"{api_prefix}/tables/allowed", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert isinstance(data["tables"], list)


@pytest.mark.asyncio
async def test_get_disabled_tables_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /tables/disabled returns list of disabled tables (may be empty)."""
    response = await async_client.get(f"{api_prefix}/tables/disabled", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "disabled_tables" in data
    assert isinstance(data["disabled_tables"], list)


@pytest.mark.asyncio
async def test_add_disabled_table_nonexistent_table(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test POST /tables/disabled returns 404 for non-existent table."""
    payload = {"table_name": "nonexistent_table_xyz", "disabled_columns": []}

    response = await async_client.post(
        f"{api_prefix}/tables/disabled", json=payload, headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_nonexistent_table(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test POST /query returns 404 for non-existent table."""
    payload = {
        "table_name": "nonexistent_table_xyz",
        "query": {},
    }

    response = await async_client.post(
        f"{api_prefix}/query", json=payload, headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_item_nonexistent_table(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test POST /items returns 400 for non-existent table."""
    payload = {
        "table_name": "nonexistent_table_xyz",
        "item": {"name": "test"},
    }

    response = await async_client.post(
        f"{api_prefix}/items", json=payload, headers=headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_items_nonexistent_table(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test PUT /items returns 400 for non-existent table."""
    payload = {
        "table_name": "nonexistent_table_xyz",
        "filters": {"id": 1},
        "update": {"name": "updated"},
    }

    response = await async_client.put(
        f"{api_prefix}/items", json=payload, headers=headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_items_nonexistent_table(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test DELETE /items returns 400 for non-existent table."""
    payload = {
        "table_name": "nonexistent_table_xyz",
        "filters": {"id": 1},
    }

    response = await async_client.request(
        "DELETE", f"{api_prefix}/items", json=payload, headers=headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_unauthorized_request(
    async_client: AsyncClient,
    api_prefix: str,
) -> None:
    """Test requests without authorization header return 401/403."""
    response = await async_client.get(f"{api_prefix}/database")

    assert response.status_code in [401, 403]
