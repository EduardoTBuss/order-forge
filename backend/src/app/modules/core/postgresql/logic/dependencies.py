from fastapi import HTTPException, Request

from src.app.modules.core.postgresql.logic.main import get_allowed_tables
from src.app.modules.core.postgresql.logic.utils import allowed_tables_to_map


async def validate_tables_and_columns_enabled(request: Request):
    """
    Validates that the table and columns in the request body are enabled for operations.
    """
    body = await request.json()
    table = body.get("table_name")
    columns = body.get("columns")  # used in SELECT / filters
    columns_to_update = body.get("update")  # used in UPDATEs

    allowed_tables = await get_allowed_tables()
    allowed_tables_map = allowed_tables_to_map(allowed_tables)

    if not table or table not in allowed_tables_map:
        raise HTTPException(status_code=400, detail=f"Table '{table}' is not allowed")

    keys_to_check: set[str] = set()

    if isinstance(columns, dict):  # filters
        keys_to_check.update(columns.keys())
    elif isinstance(columns, list):
        keys_to_check.update(columns)
    elif columns is not None:
        raise HTTPException(
            status_code=400, detail="Invalid column format for 'columns'"
        )

    if isinstance(columns_to_update, dict):  # updates
        keys_to_check.update(columns_to_update.keys())
    elif columns_to_update is not None:
        raise HTTPException(
            status_code=400, detail="Invalid column format for 'update'"
        )

    if not keys_to_check:
        return

    invalid_cols = keys_to_check - set(allowed_tables_map[table])
    if invalid_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Columns not allowed for table '{table}': {', '.join(invalid_cols)}",
        )
