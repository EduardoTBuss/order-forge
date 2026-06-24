import mimetypes

from fastapi import Form, HTTPException, UploadFile
from pydantic import ValidationError

from src.app.modules.core.blob_storage.schemas.io import UploadInput


class FileTooLargeError(Exception):
    """Se lanza cuando el fichero excede el tamaño máximo permitido."""

    pass


def get_content_type(path: str) -> str:
    """
    Infers the MIME type of a file based on its path.

    Uses the standard library to guess the content type from the file extension.
    Defaults to 'application/octet-stream' if the type cannot be determined.
    """
    content_type, _ = mimetypes.guess_type(path)

    return content_type or "application/octet-stream"


def parse_upload_params(
    path: str = Form(...),
    overwrite: bool = Form(False),
    hash_suffix: bool = Form(True),
) -> UploadInput:
    """
    Parses multipart/form-data fields into a Pydantic model.

    This function enables the use of Pydantic models with multipart/form-data
    by manually extracting form fields and converting them into an UploadInput instance.

    It is intended to be used as a FastAPI dependency in endpoints
    that receive file uploads along with additional form fields.
    """
    try:
        return UploadInput(path=path, overwrite=overwrite, hash_suffix=hash_suffix)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


async def read_file_in_chunks(
    file: UploadFile,
    max_size: int = (1024**3),  # 1GB
    chunk_size: int = (1024**2),  # 1MB
) -> tuple[bytes, int]:
    """
    Reads an UploadFile in chunks and ensures it does not exceed the maximum allowed size.
    Raises FileTooLargeError if it goes over the limit.
    """
    total_read = 0
    buffer = bytearray()

    while chunk := await file.read(chunk_size):
        total_read += len(chunk)
        if total_read > max_size:
            raise FileTooLargeError(
                f"File exceeds the {max_size // (1024**3)}GB size limit."
            )
        buffer.extend(chunk)

    return bytes(buffer), total_read
