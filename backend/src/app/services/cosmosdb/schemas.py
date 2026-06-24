from typing import Any

from pydantic import BaseModel, Field


class CosmosItem(BaseModel):
    item: dict[str, Any] = Field(description="Cosmos DB item")


class CosmosItemsList(BaseModel):
    items: list[dict[str, Any]] = Field(description="List of Cosmos DB items")
