from fastapi import APIRouter, Body, Depends, HTTPException

from src.app.modules.core.postgresql.logic.dependencies import (
    validate_tables_and_columns_enabled,
)
from src.app.modules.core.postgresql.logic.errors import (
    ColumnNotFoundError,
    ForbiddenUpdateError,
    ItemNotFoundError,
    TableNotFoundError,
)
from src.app.modules.core.postgresql.logic.main import (
    add_or_update_disabled_table,
    create_item,
    delete_items,
    get_allowed_tables,
    get_database_name,
    get_disabled_tables,
    get_items,
    update_items,
)
from src.app.modules.core.postgresql.schemas.io import (
    AddOrUpdateDisabledTableInput,
    CreateItemInput,
    CreateItemOutput,
    DatabaseNameOutput,
    DeleteItemsInput,
    DeleteItemsOutput,
    DisabledTableListOutput,
    ItemsPaginatedOutput,
    QueryItemsInput,
    TableListOutput,
    UpdateItemInput,
    UpdateItemsOutput,
)

router = APIRouter(tags=["postgresql"])


@router.get("/database")
async def postgresql_get_database_name() -> DatabaseNameOutput:
    try:
        database_name = await get_database_name()

        return DatabaseNameOutput(database_name=database_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.get("/tables/allowed")
async def postgresql_get_allowed_tables() -> TableListOutput:
    try:
        tables = await get_allowed_tables()

        return TableListOutput(tables=tables)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.get("/tables/disabled")
async def postgresql_get_disabled_tables() -> DisabledTableListOutput:
    try:
        disabled_tables = await get_disabled_tables()

        return DisabledTableListOutput(disabled_tables=disabled_tables)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.post("/tables/disabled")
async def postgresql_add_or_update_disabled_table(
    req: AddOrUpdateDisabledTableInput,
) -> dict[str, str]:
    try:
        await add_or_update_disabled_table(req)

        return {"message": "Disabled table updated successfully."}

    except ColumnNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TableNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenUpdateError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.post("/get-items")
async def postgresql_get_items(
    req: QueryItemsInput = Body(...),
    _=Depends(validate_tables_and_columns_enabled),
) -> ItemsPaginatedOutput:
    try:
        return await get_items(req)

    except ColumnNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TableNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.post("/items", status_code=201)
async def postgresql_create_item(
    req: CreateItemInput = Body(...),
    _=Depends(validate_tables_and_columns_enabled),
) -> CreateItemOutput:
    try:
        return await create_item(req)

    except ColumnNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TableNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.put("/items")
async def postgresql_update_items(
    req: UpdateItemInput = Body(...),
    _=Depends(validate_tables_and_columns_enabled),
) -> UpdateItemsOutput:
    try:
        return await update_items(req)

    except ColumnNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ItemNotFoundError, TableNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.delete("/items")
async def postgresql_delete_items(
    req: DeleteItemsInput = Body(...),
    _=Depends(validate_tables_and_columns_enabled),
) -> DeleteItemsOutput:
    try:
        return await delete_items(req)

    except ColumnNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ItemNotFoundError, TableNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")
