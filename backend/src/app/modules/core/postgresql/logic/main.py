from typing import Any

from src.app.modules.core.postgresql.db import queries
from src.app.modules.core.postgresql.logic.constants import HARD_DISABLED_TABLES
from src.app.modules.core.postgresql.logic.errors import (
    ColumnNotFoundError,
    ForbiddenUpdateError,
    ItemNotFoundError,
    TableNotFoundError,
)
from src.app.modules.core.postgresql.logic.utils import (
    build_order_clause,
    build_set_clause,
    build_where_clause_with_types,
    cast_input_values,
    normalize_row,
)
from src.app.modules.core.postgresql.schemas.io import (
    AddOrUpdateDisabledTableInput,
    CreateItemInput,
    CreateItemOutput,
    DeleteItemsInput,
    DeleteItemsOutput,
    DisabledTable,
    ItemsPaginatedOutput,
    QueryItemsInput,
    Table,
    UpdateItemInput,
    UpdateItemsOutput,
)
from src.settings import settings


async def get_database_name() -> str:
    """
    Returns the name of the configured PostgreSQL database.
    """
    return settings.postgres_db


async def get_allowed_tables() -> list[Table]:
    """
    Returns a list of tables and columns allowed for operations, excluding disabled ones.
    """
    tables = await queries.get_tables_with_columns()
    disabled_rules = await queries.get_disabled_tables()

    disabled_map: dict[str, DisabledTable] = {}

    for rule in disabled_rules:
        disabled_map[rule.table_name] = rule

    for table_name, hard_cols in HARD_DISABLED_TABLES.items():
        soft_rule = disabled_map.get(table_name)
        combined_cols = set(hard_cols)

        if soft_rule:
            combined_cols.update(soft_rule.disabled_columns)
            is_fully_disabled = soft_rule.is_fully_disabled or not combined_cols
        else:
            is_fully_disabled = not combined_cols

        disabled_map[table_name] = DisabledTable(
            table_name=table_name,
            disabled_columns=list(combined_cols),
            is_fully_disabled=is_fully_disabled,
        )

    allowed_tables: list[Table] = []
    for table in tables:
        disabled_rule = disabled_map.get(table.table_name)

        if disabled_rule and disabled_rule.is_fully_disabled:
            continue

        disabled_cols = set(disabled_rule.disabled_columns) if disabled_rule else set()
        enabled_cols = [c for c in table.columns if c not in disabled_cols]

        if enabled_cols:
            allowed_tables.append(
                Table(table_name=table.table_name, columns=enabled_cols)
            )

    return allowed_tables


async def get_disabled_tables() -> list[DisabledTable]:
    """
    Returns the list of disabled tables and columns from the database.
    """
    return await queries.get_disabled_tables()


async def add_or_update_disabled_table(
    input_data: AddOrUpdateDisabledTableInput,
) -> None:
    """
    Adds or updates a disabled table rule, validating existence and columns.
    """
    table = await queries.get_table_by_name(input_data.table_name)
    if table is None:
        raise TableNotFoundError(input_data.table_name)

    valid_columns = set(table.columns)
    invalid_cols = [c for c in input_data.disabled_columns if c not in valid_columns]
    if invalid_cols:
        raise ColumnNotFoundError(input_data.table_name, invalid_cols)

    existing = await queries.get_disabled_table_by_name(input_data.table_name)
    if existing is None:
        await queries.insert_disabled_table(
            table_name=input_data.table_name,
            columns=input_data.disabled_columns,
            is_fully_disabled=bool(input_data.is_fully_disabled),
        )
        return

    if existing.is_fully_disabled:
        raise ForbiddenUpdateError("Cannot modify a fully disabled table.")

    already_disabled = next(
        (
            col
            for col in existing.disabled_columns
            if col in input_data.disabled_columns
        ),
        None,
    )
    if already_disabled:
        raise ForbiddenUpdateError(
            f"The column '{already_disabled}' is already disabled and cannot be re-disabled."
        )

    updated_columns = list(set(existing.disabled_columns + input_data.disabled_columns))
    await queries.update_disabled_table(
        table_name=input_data.table_name,
        columns=updated_columns,
        is_fully_disabled=bool(
            input_data.is_fully_disabled or existing.is_fully_disabled
        ),
    )


async def get_items(input_data: QueryItemsInput) -> ItemsPaginatedOutput:
    """
    Fetches items from a table with filters, ordering, and pagination.
    """
    table_name = input_data.table_name
    filters = input_data.filters or {}

    where_sql = ""
    filter_values: dict[str, Any] = {}

    if filters:
        where_sql, filter_values = await build_where_clause_with_types(
            table_name, filters
        )

    order_sql = build_order_clause(input_data.order_by)

    rows: ItemsPaginatedOutput = await queries.get_items(
        table_name=table_name,
        columns=input_data.columns,
        where_sql=where_sql,
        filter_values=filter_values,
        order_sql=order_sql,
        limit=input_data.limit,
        offset=input_data.offset,
    )
    normalized_items = [normalize_row(item) for item in rows.items]

    return ItemsPaginatedOutput(
        items=normalized_items, count=rows.count, next_offset=rows.next_offset
    )


async def create_item(input_data: CreateItemInput) -> CreateItemOutput:
    """
    Inserts a new item into a table and returns its ID.
    """
    column_types = await queries.get_column_types(input_data.table_name)
    columns = cast_input_values(input_data.columns, column_types)

    return await queries.insert_item(input_data.table_name, columns)


async def update_items(input_data: UpdateItemInput) -> UpdateItemsOutput:
    """
    Updates items in a table based on filters and returns the updated ID.
    """
    table_name = input_data.table_name

    column_types = await queries.get_column_types(table_name)

    set_clauses, set_values = build_set_clause(
        input_data.update, column_types=column_types
    )
    if not set_clauses:
        raise ValueError("No valid fields to update.")

    where_sql, where_values = await build_where_clause_with_types(
        table_name,
        input_data.filters,
        key_prefix="w",
        column_types=column_types,
    )

    return await queries.update_items(
        table_name=table_name,
        set_clauses=set_clauses,
        set_values=set_values,
        where_sql=where_sql or "",
        where_values=where_values,
    )


async def delete_items(input_data: DeleteItemsInput) -> DeleteItemsOutput:
    """
    Deletes items from a table based on filters and returns the count of deleted rows.
    """
    table_name = input_data.table_name

    where_sql, where_values = await build_where_clause_with_types(
        table_name, input_data.filters, key_prefix="val"
    )

    deleted_count = await queries.delete_items(
        table_name=table_name,
        where_sql=where_sql or "",
        values=where_values,
    )

    if deleted_count == 0:
        raise ItemNotFoundError()

    return DeleteItemsOutput(deleted_count=deleted_count)
