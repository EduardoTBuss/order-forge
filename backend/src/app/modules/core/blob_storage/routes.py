from urllib.parse import urlparse

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import ValidationError

from src.app.modules.core.blob_storage.logic.main import (
    FileTooLargeError,
    get_content_type,
    parse_upload_params,
    read_file_in_chunks,
)
from src.app.modules.core.blob_storage.schemas.io import (
    BlobBaseInput,
    DeleteInput,
    ListInput,
    ListOutput,
    UploadInput,
    UploadOutput,
    UploadUrlOutput,
)
from src.app.services.blob_storage import BlobStorageServiceDefault

router = APIRouter(tags=["blob_storage"])


@router.get("/download")
def blob_download(req: BlobBaseInput = Depends()) -> Response:
    """
    Download a blob from Azure Blob Storage and return its binary content
      as a response with the appropriate media type.
    """
    try:
        content = BlobStorageServiceDefault.download(req.path)
        content_type = get_content_type(req.path)

        return Response(content=content, media_type=content_type)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Blob '{req.path}' does not exist.",
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/list")
def blob_list(req: ListInput = Depends()) -> ListOutput:
    """
    List blobs under a directory path in Azure Blob Storage.
    """
    try:
        items = BlobStorageServiceDefault.list_contents(
            req.path, recursive=req.recursive
        )
        return ListOutput(items=items)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/upload", status_code=201)
async def blob_upload(
    file: UploadFile = File(...),
    req: UploadInput = Depends(parse_upload_params),
) -> UploadOutput:
    """
    Upload a binary file to the specified `path` in Azure Blob Storage
    and returns the file path in blob storage and its metadata.
    """
    try:
        file_bytes, size = await read_file_in_chunks(file)
        blob_url = BlobStorageServiceDefault.upload(
            req.path,
            file_bytes,
            overwrite=req.overwrite,
            hash_suffix=req.hash_suffix,
        )
        parsed_url = urlparse(blob_url)
        path_parts = parsed_url.path.lstrip("/").split("/")
        container_name = BlobStorageServiceDefault.container_name
        if container_name in path_parts:
            stored_path = "/".join(path_parts[path_parts.index(container_name) + 1 :])
        else:
            stored_path = req.path

        media_type = get_content_type(stored_path)
        size_mb = round((size / (1024**2)), 2)

        return UploadOutput(
            path=stored_path,
            media_type=media_type,
            size_mb=size_mb,
            blob_url=blob_url,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ResourceExistsError:
        raise HTTPException(
            status_code=409,
            detail=f"Blob '{req.path}' already exists.",
        )
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=413,
            detail=(
                f"{str(e)}. For files that large, use the /upload-url endpoint, "
                "which generates a SAS to upload files directly"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/upload-url")
def upload_url_get(req: UploadInput = Depends()) -> UploadUrlOutput:
    """
    Generate a Shared Access Signature (SAS) URL for uploading a file directly
      to Azure Blob Storage to the specified blob path without going through this API.
    """
    try:
        sas_url, expiry_time = BlobStorageServiceDefault.generate_sas_url(
            req.path,
            permission=["write", "create"],
            hash_suffix=req.hash_suffix,
        )

        return UploadUrlOutput(upload_url=sas_url, expires_utc=expiry_time)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/delete", status_code=204)
def blob_delete(req: DeleteInput = Depends()) -> Response:
    """
    Delete a blob at the given path in Azure Blob Storage.
    """
    try:
        BlobStorageServiceDefault.delete(req.path)
        return Response(status_code=204)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Blob '{req.path}' does not exist.",
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
