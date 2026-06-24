import os
import uuid
from datetime import datetime, timedelta, timezone

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

from src.settings import settings


class BlobStorageService:
    def __init__(self, container_name: str) -> None:
        """
        Initialize the Blob Storage Service with connection to the specified container.
        """
        if not container_name:
            raise ValueError("The container name must be specified")

        self.__blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.__container_client = self.__blob_service_client.get_container_client(
            container_name
        )
        self.__container_name = container_name
        self.__container_initialized = False

    @property
    def container_name(self) -> str:
        """
        Returns the configured container name.
        """
        return self.__container_name

    def _ensure_container_exists(self) -> None:
        """
        Ensures the configured container exists, creating it if needed.
        """
        if self.__container_initialized:
            return

        try:
            self.__container_client.create_container()
        except ResourceExistsError:
            pass

        self.__container_initialized = True

    def download(self, path: str) -> bytes:
        """
        Checks if the blob exists and downloads its content as bytes.
        """
        self._ensure_container_exists()
        blob_client = self.__container_client.get_blob_client(path)
        downloader = blob_client.download_blob(encoding=None)
        bytes_content = downloader.readall()
        if isinstance(bytes_content, str):
            bytes_content = bytes_content.encode()
        return bytes_content

    def _apply_hash_suffix(self, path: str, hash_suffix: bool) -> str:
        """
        Return *path* with a random hash inserted before the extension if *hash_suffix* is True.
        This helps avoid name collisions when multiple uploads share the same base filename.
        """
        if not hash_suffix:
            return path

        base, ext = os.path.splitext(path)
        suffix = uuid.uuid4().hex[:8]
        return f"{base}-{suffix}{ext}"

    def upload(
        self,
        path: str,
        content: bytes,
        overwrite: bool = False,
        hash_suffix: bool = True,
    ) -> str:
        """
        Upload *content* to *path* in the configured container.

        If *hash_suffix* is True (default), a random eight-character hash is appended to the
        filename (before the extension) to mitigate name collisions.

        Returns the URL of the uploaded blob.
        """
        self._ensure_container_exists()
        final_path = self._apply_hash_suffix(path, hash_suffix)

        blob_client = self.__container_client.get_blob_client(final_path)
        blob_client.upload_blob(content, overwrite=overwrite)

        return self.get_blob_url(final_path)

    def exists(self, path: str) -> bool:
        """
        Check if a blob exists in the container.
        """
        self._ensure_container_exists()
        blob_client = self.__container_client.get_blob_client(path)
        return blob_client.exists()

    def list_contents(self, directory: str, recursive: bool = False) -> list[str]:
        """
        Return a combined list of items (directories first with trailing '/', then files)
        under the given directory prefix. When recursive is True, returns all files.
        """
        self._ensure_container_exists()
        # Normalize root
        if directory in {"", "/"}:
            prefix = ""
        else:
            prefix = directory if directory.endswith("/") else f"{directory}/"

        if recursive:
            return [
                b.name
                for b in self.__container_client.list_blobs(name_starts_with=prefix)
            ]

        items: list[str] = []
        for item in self.__container_client.walk_blobs(
            name_starts_with=prefix, delimiter="/"
        ):
            name = getattr(item, "name", None)
            if name:
                items.append(name)

        return items

    def get_blob_url(self, path: str) -> str:
        """
        Get the direct URL to a blob without SAS token.
        """
        normalized_path = path.lstrip("/")
        return f"{self.__container_client.url}/{normalized_path}"

    def delete(self, path: str) -> None:
        """
        Delete the blob at the given path from the configured container.
        """
        self._ensure_container_exists()
        blob_client = self.__container_client.get_blob_client(path)
        blob_client.delete_blob()

    def generate_sas_url(
        self,
        path: str,
        expiry_minutes: int = 60,
        permission: list[str] | None = None,
        hash_suffix: bool = False,
    ) -> tuple[str, datetime]:
        """
        Generate a SAS URL for accessing *path*.

        When *hash_suffix* is True, the same hash-suffix logic applied in *upload* will be applied
        to the blob name before generating the SAS token. This ensures consistency between the
        SAS URL and the actual stored blob when uploads were done with *hash_suffix=True*.
        """
        self._ensure_container_exists()
        if permission is None:
            permission = [""]

        if hash_suffix:
            final_path = self._apply_hash_suffix(path, hash_suffix)
        else:
            final_path = path

        write = "write" in permission
        create = "create" in permission
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

        sas_token = generate_blob_sas(
            account_name=str(self.__blob_service_client.account_name),
            container_name=self.__container_name,
            blob_name=final_path,
            account_key=self.__blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True, write=write, create=create),
            expiry=expiry_time,
        )
        sas_url = f"{self.get_blob_url(final_path)}?{sas_token}"

        return sas_url, expiry_time


#################
### SINGLETON ###
################
BlobStorageServiceDefault = BlobStorageService(container_name="default")
