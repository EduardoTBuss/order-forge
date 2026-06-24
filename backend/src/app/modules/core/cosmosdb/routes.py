from fastapi import APIRouter, Depends, HTTPException

from src.app.modules.core.cosmosdb.schemas.io import (
    CollectionInput,
    CollectionListOutput,
    CosmosItemsPaginated,
    CreateDatabaseInput,
    CreateDatabaseOutput,
    CreateItemInput,
    CreateItemOutput,
    DatabaseInput,
    DatabaseListOutput,
    DeleteItemsInput,
    DeleteItemsOutput,
    QueryItemsInput,
    ReadItemInput,
    UpdateItemInput,
)
from src.app.services.cosmosdb import CosmosDBService
from src.app.services.cosmosdb.schemas import CosmosItem

router = APIRouter(tags=["cosmosdb"])


@router.get("/databases")
async def cosmos_databases_list() -> DatabaseListOutput:
    """
    Lists all databases in the CosmosDB instance.
    """
    try:
        databases = await CosmosDBService.get_db_names()

        return DatabaseListOutput(databases=databases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/databases", status_code=201)
async def cosmos_database_create(req: CreateDatabaseInput) -> CreateDatabaseOutput:
    """
    Creates a new database with the specified collections.
    """
    try:
        await CosmosDBService.create_db_and_collections(req.db_name, req.coll_names)

        return CreateDatabaseOutput(db=req.db_name, collections=req.coll_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/collections/reset", status_code=200)
async def cosmos_collection_reset(req: CollectionInput) -> dict:
    """
    Drops the given collection (if it exists) and recreates it with the same name.

    This is a non-idempotent, action-style endpoint. Use with care.
    """
    try:
        await CosmosDBService.reset_collection(req.db_name, req.coll_name)

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/collections")
async def cosmos_collection_list(
    req: DatabaseInput = Depends(),
) -> CollectionListOutput:
    """
    Lists all collections in the specified database.
    """
    try:
        collections = await CosmosDBService.get_collection_names(req.db_name)

        return CollectionListOutput(collections=collections)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/items", status_code=201)
async def cosmos_item_create(req: CreateItemInput) -> CreateItemOutput:
    """
    Creates a new item in the specified collection.
    """
    try:
        if req.create_if_not_exists:
            cosmos_service = await CosmosDBService.build_or_create(
                req.db_name, req.coll_name
            )
        else:
            cosmos_service = await CosmosDBService.build(req.db_name, req.coll_name)
        item_id = await cosmos_service.create_item(req.item)

        return CreateItemOutput(item_id=item_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/get-item")
async def cosmos_item_read(req: ReadItemInput) -> CosmosItem:
    """
    Finds and returns a single item matching the specified filters.
    """
    try:
        if req.create_if_not_exists:
            cosmos_service = await CosmosDBService.build_or_create(
                req.db_name, req.coll_name
            )
        else:
            cosmos_service = await CosmosDBService.build(req.db_name, req.coll_name)
        item = await cosmos_service.read_item(req.filters)

        return item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.put("/items")
async def cosmos_item_update(req: UpdateItemInput) -> CosmosItem:
    """
    Updates an item and returns the updated version.
    """
    try:
        if req.create_if_not_exists:
            cosmos_service = await CosmosDBService.build_or_create(
                req.db_name, req.coll_name
            )
        else:
            cosmos_service = await CosmosDBService.build(req.db_name, req.coll_name)
        item = await cosmos_service.update_item(req.filters, req.update)

        return item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.delete("/items")
async def cosmos_items_delete(req: DeleteItemsInput) -> DeleteItemsOutput:
    """
    Deletes items matching the specified filters.
    """
    try:
        if req.create_if_not_exists:
            cosmos_service = await CosmosDBService.build_or_create(
                req.db_name, req.coll_name
            )
        else:
            cosmos_service = await CosmosDBService.build(req.db_name, req.coll_name)
        deleted_count = await cosmos_service.delete_items(req.filters)

        return DeleteItemsOutput(deleted_count=deleted_count)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/query-items")
async def cosmos_items_query(req: QueryItemsInput) -> CosmosItemsPaginated:
    """
    Retrieves a page of documents from the collection.

    Uses `block_id` (the _id of the last document from the previous page)
    to fetch the next page. If `block_id` is None, returns the first page.
    """
    try:
        if req.create_if_not_exists:
            cosmos_service = await CosmosDBService.build_or_create(
                req.db_name, req.coll_name
            )
        else:
            cosmos_service = await CosmosDBService.build(req.db_name, req.coll_name)
        result = await cosmos_service.query_items(
            req.filters, req.projection, req.limit, req.block_id
        )

        items = result.items
        count = len(items)
        next_block_id = items[-1]["_id"] if count == req.limit else None

        return CosmosItemsPaginated(
            items=items, count=count, next_block_id=next_block_id
        )
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")
