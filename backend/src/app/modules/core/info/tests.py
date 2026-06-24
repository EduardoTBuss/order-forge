from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from src.app.modules.core.info.schemas.io import ServerHealthOutput
from src.app.modules.core.info.schemas.server_status import ServerStatus


@pytest.mark.asyncio
async def test_health_check_success(async_client: AsyncClient, api_prefix: str) -> None:
    """Test that /health returns 200 OK with valid ServerHealthOutput schema."""
    response = await async_client.get(f"{api_prefix}/health")

    assert response.status_code == 200

    output = ServerHealthOutput.model_validate(response.json())

    assert ServerStatus(output.status) in ServerStatus


@pytest.mark.asyncio
@patch(
    "src.app.modules.core.info.routes.get_server_health",
    side_effect=Exception("mocked error"),
)
async def test_health_check_exception(
    mock_health: MagicMock, async_client: AsyncClient, api_prefix: str
) -> None:
    """Test that /health returns 500 when get_server_health raises an exception."""
    response = await async_client.get(f"{api_prefix}/health")

    assert mock_health.called
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error."


@pytest.mark.asyncio
async def test_swagger2_endpoint_returns_valid_structure(
    async_client: AsyncClient, api_prefix: str
) -> None:
    """Test that /swagger returns a valid Swagger 2.0 specification."""
    response = await async_client.get(f"{api_prefix}/swagger")

    assert response.status_code == 200

    data = response.json()

    assert data["swagger"] == "2.0"
    assert "info" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_run_tests_requires_auth(
    async_client: AsyncClient, api_prefix: str
) -> None:
    """Test that /tests/run requires authentication."""
    response = await async_client.post(f"{api_prefix}/tests/run")

    # 401 when no credentials provided
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("src.app.modules.core.info.routes.trigger_test_run", return_value=True)
async def test_run_tests_success(
    mock_trigger: MagicMock,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/run triggers a test run successfully."""
    response = await async_client.post(f"{api_prefix}/tests/run", headers=headers)

    assert response.status_code == 200
    assert response.json()["triggered"] is True
    assert "started" in response.json()["message"].lower()


@pytest.mark.asyncio
@patch("src.app.modules.core.info.routes.trigger_test_run", return_value=False)
async def test_run_tests_already_running(
    mock_trigger: MagicMock,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/run returns appropriate message when tests already running."""
    response = await async_client.post(f"{api_prefix}/tests/run", headers=headers)

    assert response.status_code == 200
    assert response.json()["triggered"] is False
    assert "already running" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_tests_status_requires_auth(
    async_client: AsyncClient, api_prefix: str
) -> None:
    """Test that /tests/status requires authentication."""
    response = await async_client.get(f"{api_prefix}/tests/status")

    # 401 when no credentials provided
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("src.app.modules.core.info.routes.get_test_status")
async def test_tests_status_success(
    mock_status: MagicMock,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/status returns test run status."""
    mock_status.return_value = MagicMock(
        is_running=False,
        started_at=None,
        finished_at=None,
        exit_code=None,
        report_path="/static/test-report.html",
        module=None,
    )

    response = await async_client.get(f"{api_prefix}/tests/status", headers=headers)

    assert response.status_code == 200
    assert "is_running" in response.json()
    assert "report_path" in response.json()
    assert "module" in response.json()


@pytest.mark.asyncio
async def test_tests_modules_requires_auth(
    async_client: AsyncClient, api_prefix: str
) -> None:
    """Test that /tests/modules requires authentication."""
    response = await async_client.get(f"{api_prefix}/tests/modules")

    # 401 when no credentials provided
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tests_modules_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/modules returns list of available modules."""
    response = await async_client.get(f"{api_prefix}/tests/modules", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert isinstance(data["modules"], list)
    assert "postgresql" in data["modules"]
    assert "cosmosdb" in data["modules"]


@pytest.mark.asyncio
@patch("src.app.modules.core.info.routes.trigger_test_run", return_value=True)
async def test_run_tests_with_module_filter(
    mock_trigger: MagicMock,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/run accepts module filter parameter."""
    response = await async_client.post(
        f"{api_prefix}/tests/run?module=postgresql", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["triggered"] is True
    assert response.json()["module"] == "postgresql"
    assert "postgresql" in response.json()["message"]
    mock_trigger.assert_called_once_with(module="postgresql")


@pytest.mark.asyncio
async def test_run_tests_invalid_module(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test that /tests/run rejects invalid module names."""
    response = await async_client.post(
        f"{api_prefix}/tests/run?module=nonexistent_module", headers=headers
    )

    assert response.status_code == 400
    assert "Invalid module" in response.json()["detail"]
