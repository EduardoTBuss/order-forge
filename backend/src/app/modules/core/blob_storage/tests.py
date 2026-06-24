"""
Integration tests for Blob Storage module.

These tests run against a real Azurite instance (Azure Blob Storage emulator).
Test files are created in the test-artifacts/ prefix and cleaned up after tests.
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.app.modules.core.blob_storage.logic.main import FileTooLargeError

# Mark all tests in this module as requiring blob storage
pytestmark = [pytest.mark.blobstorage, pytest.mark.integration]

TEST_BLOB_DIR = "test-artifacts"


@pytest.mark.asyncio
async def test_upload_url_get_success(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /upload-url returns a valid SAS upload URL and expiry timestamp."""
    path = f"{TEST_BLOB_DIR}/test.txt"
    params = {
        "path": path,
        "overwrite": "false",
        "hash_suffix": "true",
    }

    response = await async_client.get(
        f"{api_prefix}/upload-url", params=params, headers=headers
    )

    assert response.status_code == 200
    assert "upload_url" in response.json()
    assert "expires_utc" in response.json()


@patch(
    "src.app.modules.core.blob_storage.routes.BlobStorageServiceDefault.generate_sas_url",
    side_effect=Exception("Unexpected SAS error"),
)
@pytest.mark.asyncio
async def test_upload_url_unexpected_exception(
    mock_sas,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /upload-url returns 500 if generate_sas_url raises unexpected exception."""
    path = (f"{TEST_BLOB_DIR}/error.txt",)
    params = {
        "path": path,
        "overwrite": "false",
        "hash_suffix": "true",
    }

    response = await async_client.get(
        f"{api_prefix}/upload-url", params=params, headers=headers
    )

    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_blob_upload_success(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /upload uploads file and returns metadata."""
    file_content = io.BytesIO(b"This is a test file (DO NOT DELETE, DO NOT MODIFY)")
    file_name = "test.txt"
    path = f"{TEST_BLOB_DIR}/{file_name}"

    files = {"file": (file_name, file_content, "text/plain")}
    data = {"path": path, "overwrite": "true", "hash_suffix": "false"}

    response = await async_client.post(
        f"{api_prefix}/upload",
        files=files,
        data=data,
        headers=headers,
    )

    assert response.status_code == 201
    assert "path" in response.json()
    assert "blob_url" in response.json()


@pytest.mark.asyncio
async def test_blob_upload_conflict(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /upload returns 409 if blob exists and overwrite=False."""
    file_content = io.BytesIO(b"test_blob_upload_conflict")
    file_name = "test.txt"
    path = f"{TEST_BLOB_DIR}/{file_name}"

    files = {"file": (file_name, file_content, "text/plain")}
    data = {"path": path, "overwrite": "false", "hash_suffix": "false"}

    response = await async_client.post(
        f"{api_prefix}/upload",
        files=files,
        data=data,
        headers=headers,
    )

    assert response.status_code == 409
    assert "already exists" in response.json().get("detail")


@pytest.mark.asyncio
@patch(
    "src.app.modules.core.blob_storage.routes.read_file_in_chunks",
    new_callable=AsyncMock,
)
async def test_blob_upload_file_too_large(
    mock_read_chunks,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /upload returns 413 if file exceeds max allowed size."""
    mock_read_chunks.side_effect = FileTooLargeError("File exceeds the limit")

    file_content = io.BytesIO(b"fake content")
    file_name = "fake_file.pdf"
    path = f"{TEST_BLOB_DIR}/{file_name}"

    files = {"file": (file_name, file_content, "application/pdf")}
    data = {"path": path}

    response = await async_client.post(
        f"{api_prefix}/upload", files=files, data=data, headers=headers
    )

    assert response.status_code == 413
    assert "use the /upload-url endpoint" in response.json()["detail"]


@pytest.mark.asyncio
async def test_blob_upload_validation_error(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /upload returns 422 when path is invalid."""
    file_content = io.BytesIO(b"some content")
    invalid_file_name = "testfile"
    invalid_path = "invalid//path"

    files = {"file": (invalid_file_name, file_content, "text/plain")}
    data = {"path": invalid_path, "overwrite": "false", "hash_suffix": "true"}

    response = await async_client.post(
        f"{api_prefix}/upload", files=files, data=data, headers=headers
    )

    assert response.status_code == 422
    assert (
        "Invalid blob path" in response.text
        or "File extension is required" in response.text
    )


@pytest.mark.asyncio
async def test_blob_upload_invalid_path_validation(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /upload returns 422 when path fails validation."""
    file_content = io.BytesIO(b"test")
    file_name = "test.txt"
    invalid_path = f"/invalid//path/{file_name}"

    files = {"file": (file_name, file_content, "text/plain")}
    data = {"path": invalid_path, "overwrite": "true", "hash_suffix": "false"}

    response = await async_client.post(
        f"{api_prefix}/upload",
        files=files,
        data=data,
        headers=headers,
    )

    assert response.status_code == 422
    assert "Invalid blob path" in response.text


@patch(
    "src.app.modules.core.blob_storage.routes.read_file_in_chunks",
    new_callable=AsyncMock,
)
@patch(
    "src.app.modules.core.blob_storage.routes.BlobStorageServiceDefault.upload",
    side_effect=Exception("Unexpected crash"),
)
@pytest.mark.asyncio
async def test_blob_upload_unexpected_exception(
    mock_upload,
    mock_read_chunks,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /upload returns 500 on unexpected failure."""
    mock_read_chunks.return_value = (b"fake file", 100)

    file_content = io.BytesIO(b"fake content")
    file_name = "fake_file.pdf"
    path = f"{TEST_BLOB_DIR}/{file_name}"

    files = {"file": (file_name, file_content, "application/pdf")}
    data = {"path": path}

    response = await async_client.post(
        f"{api_prefix}/upload", files=files, data=data, headers=headers
    )

    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_blob_download_success(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /download downloads file with correct media type."""
    path = f"{TEST_BLOB_DIR}/test.txt"
    params = {"path": path}

    response = await async_client.get(
        f"{api_prefix}/download", params=params, headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert isinstance(response.content, bytes)
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_blob_download_not_found(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /download returns 404 if blob doesn't exist."""
    no_existent_path = f"{TEST_BLOB_DIR}/nonexistent.txt"
    params = {"path": no_existent_path}

    response = await async_client.get(
        f"{api_prefix}/download", params=params, headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
@patch(
    "src.app.modules.core.blob_storage.routes.get_content_type",
    side_effect=Exception("MIME error"),
)
async def test_blob_download_get_content_type_exception(
    mock_content_type,
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Test /download returns 500 if get_content_type raises error."""
    path = f"{TEST_BLOB_DIR}/test.txt"
    params = {"path": path}

    response = await async_client.get(
        f"{api_prefix}/download", params=params, headers=headers
    )

    assert response.status_code == 500
    assert "Unexpected error: MIME error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_blob_list_success(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /list returns list of blobs."""
    params = {"path": TEST_BLOB_DIR}

    response = await async_client.get(
        f"{api_prefix}/list", params=params, headers=headers
    )

    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_blob_delete_not_found(
    async_client: AsyncClient, api_prefix: str, headers: dict[str, str]
) -> None:
    """Test /delete returns 404 for non-existent blob."""
    params = {"path": f"{TEST_BLOB_DIR}/nonexistent_file_to_delete.txt"}

    response = await async_client.delete(
        f"{api_prefix}/delete", params=params, headers=headers
    )

    assert response.status_code == 404
