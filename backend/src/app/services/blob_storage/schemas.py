import base64
import builtins
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from assets.pdf_sample import PDF_SAMPLE
from src.app.services.blob_storage import BlobStorageServiceDefault


class B64BlobFile(BaseModel):
    """Represents a file either as base-64 string or blob path."""

    source: Literal["base64", "blob"] = Field(
        description="Indicates whether *content* is base-64 (inline) or a blob path.",
        examples=["base64"],
    )
    content: str = Field(
        description="Base-64 string or Azure Blob Storage path to the file content.",
        examples=[
            PDF_SAMPLE,
        ],
    )

    @classmethod
    def from_bytes(cls: type["B64BlobFile"], data: builtins.bytes) -> "B64BlobFile":
        return cls(content=base64.b64encode(data).decode(), source="base64")

    def base64(self: "B64BlobFile") -> str:
        if self.source == "base64":
            return self.content
        else:
            blob_bytes: bytes = BlobStorageServiceDefault.download(self.content)
            return base64.b64encode(blob_bytes).decode()

    def bytes(self: "B64BlobFile") -> builtins.bytes:
        if self.source == "base64":
            return base64.b64decode(self.content)
        else:
            return BlobStorageServiceDefault.download(self.content)

    def blob_path(self: "B64BlobFile", path: None | str = None) -> str:
        if self.source == "blob":
            return self.content
        else:
            if path is None:
                raise ValueError("Path is required for uploading bytes")
            blob_url = BlobStorageServiceDefault.upload(path, self.bytes())
            return blob_url

    @model_validator(mode="after")
    def _validate_content(self: "B64BlobFile") -> "B64BlobFile":
        src: str = self.source
        if src == "base64":
            try:
                base64.b64decode(self.content, validate=True)
            except Exception as exc:
                raise ValueError("Invalid base-64 data.") from exc
        else:
            if not re.match(r"^(?!.*//)(?!/)[\w\-./]+(?<!/)$", self.content):
                raise ValueError(
                    "Invalid blob path. Should match: ^(?!.*//)(?!/)[\\w\\-./]+(?<!/)$"
                )
            if not BlobStorageServiceDefault.exists(self.content):
                raise ValueError(f"Blob does not exist: {self.content}")
        return self
