from typing import Any

from pydantic import BaseModel, Field

from src.app.services.cosmosdb.schemas import CosmosItemsList


class DatabaseInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )


class CollectionInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users", "products"]
    )


class CreateDatabaseInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database to create", examples=["my_database"]
    )
    coll_names: list[str] = Field(
        ...,
        description="List of collection names to create",
        examples=[["users", "products", "orders"]],
    )


class CreateItemInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users"]
    )
    item: dict[str, Any] = Field(
        ...,
        description="Item data to insert",
        examples=[{"name": "John Doe", "email": "john@example.com", "age": 30}],
    )
    create_if_not_exists: bool = Field(
        default=True,
        description="If True, automatically creates the database and collection if they don't exist",
    )


class ReadItemInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users"]
    )
    filters: dict[str, Any] = Field(
        ...,
        description="Filters to find the item",
        examples=[{"_id": "507f1f77bcf86cd799439011"}, {"email": "john@example.com"}],
    )
    create_if_not_exists: bool = Field(
        default=True,
        description="If True, automatically creates the database and collection if they don't exist",
    )


class UpdateItemInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users"]
    )
    filters: dict[str, Any] = Field(
        ...,
        description="Filters to find the item to update",
        examples=[{"_id": "507f1f77bcf86cd799439011"}, {"email": "john@example.com"}],
    )
    update: dict[str, Any] = Field(
        ...,
        description="Update data to apply",
        examples=[{"$set": {"age": 31, "last_updated": "2024-01-01"}}],
    )
    create_if_not_exists: bool = Field(
        default=True,
        description="If True, automatically creates the database and collection if they don't exist",
    )


class DeleteItemsInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users"]
    )
    filters: dict[str, Any] = Field(
        ...,
        description="Filters to find items to delete",
        examples=[{"_id": "507f1f77bcf86cd799439011"}, {"status": "inactive"}],
    )
    create_if_not_exists: bool = Field(
        default=True,
        description="If True, automatically creates the database and collection if they don't exist",
    )


class QueryItemsInput(BaseModel):
    db_name: str = Field(
        ..., description="Name of the database", examples=["my_database"]
    )
    coll_name: str = Field(
        ..., description="Name of the collection", examples=["users"]
    )
    filters: dict[str, Any] = Field(
        default={},
        description="Filters to apply to the query",
        examples=[{"age": {"$gte": 18}}, {"status": "active"}],
    )
    projection: dict[str, int] = Field(
        default={},
        description=(
            "Fields to include (1) / exclude (0) in the results. You "
            "cannot include and exclude fields at the same time; you "
            "must choose either to include or to exclude"
        ),
        examples=[{"password": 0, "email": 0}],
    )
    limit: int = Field(
        default=50,
        description="Maximum number of items to return",
        ge=1,
    )
    block_id: str | None = Field(
        default=None,
        description=(
            "ID of the last document from the previous page. "
            "Use this to fetch the next page. "
            "Set to None (or omit) for the first page."
        ),
        examples=["507f1f77bcf86cd799439011"],
    )
    create_if_not_exists: bool = Field(
        default=True,
        description="If True, automatically creates the database and collection if they don't exist",
    )


class DatabaseListOutput(BaseModel):
    databases: list[str] = Field(description="List of database names")


class CollectionListOutput(BaseModel):
    collections: list[str] = Field(description="List of collection names")


class CreateDatabaseOutput(BaseModel):
    db: str = Field(description="Name of the created database")
    collections: list[str] = Field(description="List of created collection names")


class CreateItemOutput(BaseModel):
    item_id: str = Field(description="ID of the created item")


class DeleteItemsOutput(BaseModel):
    deleted_count: int = Field(description="Number of items deleted")


class CosmosItemsPaginated(CosmosItemsList):
    count: int = Field(description="Number of items returned")
    next_block_id: str | None = Field(
        default=None,
        description=(
            "ID to use in the next request to continue pagination, "
            "or None if no more pages."
        ),
        examples=["507f1f77bcf86cd799439011", None],
    )
