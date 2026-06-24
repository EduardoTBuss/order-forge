import os
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BlobBaseInput(BaseModel):
    path: str = Field(
        ...,
        description="Path to the blob storage resource",
        examples=["/path/to/blob.pdf"],
    )

    @field_validator("path")
    def validate_extension(cls, value: str) -> str:
        _, extension = os.path.splitext(value)

        if not extension:
            raise ValueError("File extension is required")

        if not re.match(r"^(?!.*//)(?!/)[\w\-./]+(?<!/)$", value):
            raise ValueError(
                "Invalid blob path. Should match: ^(?!.*//)(?!/)[\\w\\-./]+(?<!/)$"
            )

        return value


class UploadInput(BlobBaseInput):
    overwrite: bool = Field(
        default=False,
        description="Flag that determines whether to overwrite blobs",
    )

    hash_suffix: bool = Field(
        default=True,
        description="Whether to add a random hash suffix to the filename to avoid name collisions",
    )


class UploadOutput(BaseModel):
    path: str = Field(description="Path of the uploaded blob")
    media_type: str = Field(description="Media type of the uploaded file")
    size_mb: float = Field(description="Size of the file in megabytes")
    blob_url: str = Field(description="Direct URL to the blob in Azure Storage")


class UploadUrlOutput(BaseModel):
    upload_url: str = Field(
        description="SAS URL for uploading the file directly to Azure Blob Storage"
    )
    expires_utc: datetime = Field(description="UTC timestamp when the SAS URL expires")


class ListInput(BaseModel):
    path: str = Field(
        ...,
        description="Directory path prefix in the blob container (use '/' or '' for root)",
        examples=["folder/subfolder", "/"],
    )
    recursive: bool = Field(
        default=False, description="Whether to list all files recursively"
    )

    @field_validator("path")
    def validate_directory(cls, value: str) -> str:
        # Normalize root directory inputs like '/' to empty prefix
        if value in {"/", ""}:
            return ""
        if value.endswith("/"):
            value = value.rstrip("/")
        if not re.match(r"^(?!.*//)(?!/)[\w\-./]+(?<!/)$", value):
            raise ValueError(
                "Invalid directory path. Should match: ^(?!.*//)(?!/)[\\w\\-./]+(?<!/)$"
            )
        return value


class ListOutput(BaseModel):
    items: list[str] = Field(
        description="Combined list of directory prefixes and files under the specified directory"
    )


class DeleteInput(BlobBaseInput):
    pass
