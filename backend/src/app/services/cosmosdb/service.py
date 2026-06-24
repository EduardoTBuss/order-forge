import asyncio
from typing import Any

from bson import ObjectId
from pymongo import AsyncMongoClient, ReturnDocument

from src.app.services.cosmosdb.schemas import CosmosItem, CosmosItemsList
from src.settings import settings


class CosmosDBService:
    """
    Async service to perform CRUD operations on Azure Cosmos DB using the MongoDB API.

    In TEST mode (when cosmosdb_db_prefix is set), all database names are
    automatically prefixed to ensure test isolation. This prevents test data
    from polluting production/development databases.
    """

    __client: AsyncMongoClient | None = None
    __client_loop_id: int | None = None

    @classmethod
    def _apply_db_prefix(cls, db_name: str) -> str:
        """Apply database prefix for test isolation if configured."""
        prefix = settings.cosmosdb_db_prefix
        if prefix and not db_name.startswith(prefix):
            return f"{prefix}{db_name}"
        return db_name

    @classmethod
    def get_db_prefix(cls) -> str:
        """Return the configured database prefix (for cleanup purposes)."""
        return settings.cosmosdb_db_prefix

    @classmethod
    def _get_client(cls) -> AsyncMongoClient:
        """
        Lazy initialization of the MongoDB client.
        Creates the client on first access and recreates if event loop changes.
        This ensures proper event loop binding in test environments.
        """
        try:
            current_loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            current_loop_id = None

        # Recreate client if event loop changed (happens in tests)
        if cls.__client is not None and cls.__client_loop_id != current_loop_id:
            cls.__client = None

        if cls.__client is None:
            cls.__client = AsyncMongoClient(settings.azure_cosmosdb_connection_string)
            cls.__client_loop_id = current_loop_id

        return cls.__client

    # ---------------- static helpers ----------------
    @classmethod
    async def get_db_names(cls) -> list[str]:
        """
        Retrieve all database names from the Cosmos DB instance.

        Note: Returns raw database names without stripping prefix.
        """
        return await cls._get_client().list_database_names()

    @classmethod
    async def raise_if_db_not_exist(cls, db_name: str) -> None:
        """Check if database exists, applying prefix if configured."""
        prefixed_name = cls._apply_db_prefix(db_name)
        if prefixed_name in await cls.get_db_names():
            return
        raise RuntimeError(f"Database '{db_name}' not found")

    @classmethod
    async def get_collection_names(cls, db_name: str) -> list[str]:
        """Retrieve all collection names from the specified database."""
        await cls.raise_if_db_not_exist(db_name)
        prefixed_name = cls._apply_db_prefix(db_name)
        return await cls._get_client()[prefixed_name].list_collection_names()

    @classmethod
    async def create_db_and_collections(
        cls, db_name: str, coll_names: list[str]
    ) -> None:
        """
        Create a database and its collections.

        In TEST mode, the database name is automatically prefixed for isolation.
        """
        prefixed_name = cls._apply_db_prefix(db_name)
        db = cls._get_client()[prefixed_name]

        for coll in coll_names:
            await db[coll].insert_one({"_init": True})
            await db[coll].delete_one({"_init": True})

    @classmethod
    async def reset_collection(cls, db_name: str, coll_name: str) -> None:
        """Reset the collection by dropping and recreating it."""
        await cls.raise_if_db_not_exist(db_name)
        prefixed_name = cls._apply_db_prefix(db_name)
        db = cls._get_client()[prefixed_name]

        await db[coll_name].drop()
        await db[coll_name].insert_one({"_init": True})
        await db[coll_name].delete_one({"_init": True})

    # ---------------- validated constructor ----------------
    def __init__(self, db_name: str, coll_name: str):
        """Initialize the service with database and collection names."""
        prefixed_name = self._apply_db_prefix(db_name)
        self.collection = self._get_client()[prefixed_name][coll_name]

    @classmethod
    async def build(cls, db_name: str, coll_name: str) -> "CosmosDBService":
        """Create a validated instance by checking if database and collection exist."""
        await cls.raise_if_db_not_exist(db_name)

        if coll_name not in await cls.get_collection_names(db_name):
            raise RuntimeError(f"Collection '{coll_name}' not found inside '{db_name}'")

        return cls(db_name, coll_name)

    @classmethod
    async def build_or_create(cls, db_name: str, coll_name: str) -> "CosmosDBService":
        """
        Create an instance, automatically creating the database and collection if they don't exist.

        This is the recommended method for most use cases as it ensures the infrastructure
        exists before performing operations.
        """
        # Check if database exists, create if not
        existing_dbs = await cls.get_db_names()
        if db_name not in existing_dbs:
            await cls.create_db_and_collections(db_name, [coll_name])
        else:
            # Database exists, check if collection exists
            existing_colls = await cls.get_collection_names(db_name)
            if coll_name not in existing_colls:
                # Create the collection by inserting and deleting a dummy document
                prefixed_name = cls._apply_db_prefix(db_name)
                db = cls._get_client()[prefixed_name]
                await db[coll_name].insert_one({"_init": True})
                await db[coll_name].delete_one({"_init": True})

        return cls(db_name, coll_name)

    # ---------------- Instance Methods ---------------------

    def __serialize_item_id(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Serialize Item id by converting ObjectIds to strings.
        """
        if "_id" in item:
            item["_id"] = str(item["_id"])

        return item

    def __deserialize_item_id(self, filters: dict[str, Any]) -> dict[str, Any]:
        """
        Serialize Item id by converting ObjectIds to strings.
        """
        if "_id" in filters:
            filters["_id"] = ObjectId(filters["_id"])

        return filters

    async def create_item(self, item: dict[str, Any]) -> str:
        """
        Insert a new Item and return its generated _id.
        """
        result = await self.collection.insert_one(item)

        return str(result.inserted_id)

    async def read_item(self, filters: dict[str, Any]) -> CosmosItem:
        """
        Find a single Item matching the filters.
        Example filters: {"_id": ObjectId("…")} or {"userId": "xyz"}.
        """
        result = await self.collection.find_one(self.__deserialize_item_id(filters))

        if result is None:
            raise ValueError("Item not found")

        return CosmosItem(item=self.__serialize_item_id(result))

    async def update_item(
        self, filters: dict[str, Any], update: dict[str, Any]
    ) -> CosmosItem:
        """
        Update a Item and return the updated Item.
        """
        result = await self.collection.find_one_and_update(
            filters, update, return_document=ReturnDocument.AFTER
        )

        if result is None:
            raise ValueError("Item not found")

        return CosmosItem(item=self.__serialize_item_id(result))

    async def delete_items(self, filters: dict[str, Any]) -> int:
        """
        Delete documents matching the filters.
        Returns the count of deleted documents.
        """
        result = await self.collection.delete_many(filters)

        return result.deleted_count

    async def query_items(
        self,
        filters: dict[str, Any] = {},
        projection: dict[str, int] = {},
        limit: int = 50,
        after_id: str | None = None,
    ) -> CosmosItemsList:
        """
        Returns a list of documents matching the filters,
        using efficient cursor-based pagination (_id).

        If after_id is provided, only documents with _id
        greater than after_id are returned.

        This technique is recommended for paginating in CosmosDB/Mongo,
        as it avoids the performance issues of skip/limit with large datasets.
        """
        filters = self.__deserialize_item_id(filters)

        if after_id is not None:
            filters["_id"] = {"$gt": ObjectId(after_id)}

        cursor = self.collection.find(filters, projection)
        cursor = cursor.sort("_id", 1)
        cursor = cursor.limit(limit)

        results = await cursor.to_list(length=limit)
        items = [self.__serialize_item_id(item) for item in results]

        return CosmosItemsList(items=items)
