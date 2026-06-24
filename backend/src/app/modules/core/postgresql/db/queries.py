from typing import Any

from sqlalchemy import insert, select, text, update

from src.app.modules.core.postgresql.db.models import (
    DisabledTable as DisabledTableModel,
)
from src.app.modules.core.postgresql.logic.errors import ItemNotFoundError
from src.app.modules.core.postgresql.schemas.io import (
    CreateItemOutput,
    DisabledTable,
    ItemsPaginatedOutput,
    Table,
    UpdateItemsOutput,
)
from src.app.services.postgresql.service import Database


async def get_tables_with_columns() -> list[Table]:
    """
    Returns all tables and their columns from the public schema.
    """
    async with Database.get_async_db() as session:
        result = await session.execute(
            text(
                """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
            )
        )
        rows = result.fetchall()

        # Group columns by table
        table_columns: dict[str, list[str]] = {}
        for table_name, column_name in rows:
            table_columns.setdefault(table_name, []).append(column_name)

        return [
            Table(table_name=table, columns=cols)
            for table, cols in table_columns.items()
        ]


async def get_table_by_name(table_name: str) -> Table | None:
    """
    Returns a single table and its columns if it exists.
    """
    async with Database.get_async_db() as session:
        result = await session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        )
        columns = [row[0] for row in result.fetchall()]
        return Table(table_name=table_name, columns=columns) if columns else None


async def get_disabled_tables() -> list[DisabledTable]:
    """
    Returns all disabled tables with their disabled columns.
    """
    async with Database.get_async_db() as session:
        result = await session.execute(select(DisabledTableModel))
        records = result.scalars().all()

        return [
            DisabledTable(
                table_name=str(record.table_name),
                disabled_columns=list(record.disabled_columns),
                is_fully_disabled=bool(record.is_fully_disabled),
            )
            for record in records
        ]


async def get_disabled_table_by_name(table_name: str) -> DisabledTable | None:
    """
    Returns a disabled table by name, if it exists.
    """
    async with Database.get_async_db() as session:
        stmt = select(DisabledTableModel).where(
            DisabledTableModel.table_name == table_name
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return None

        return DisabledTable(
            table_name=str(record.table_name),
            disabled_columns=list(record.disabled_columns or []),
            is_fully_disabled=bool(record.is_fully_disabled),
        )


async def insert_disabled_table(
    table_name: str, columns: list[str], is_fully_disabled: bool
) -> None:
    """
    Inserts a new disabled table rule into the database.
    """
    async with Database.get_async_db() as session:
        stmt = insert(DisabledTableModel).values(
            table_name=table_name,
            disabled_columns=columns,
            is_fully_disabled=is_fully_disabled,
        )
        await session.execute(stmt)


async def update_disabled_table(
    table_name: str, columns: list[str], is_fully_disabled: bool
) -> None:
    """
    Updates an existing disabled table rule.
    """
    async with Database.get_async_db() as session:
        stmt = (
            update(DisabledTableModel)
            .where(DisabledTableModel.table_name == table_name)
            .values(
                disabled_columns=columns,
                is_fully_disabled=is_fully_disabled,
            )
        )
        await session.execute(stmt)


async def get_column_types(table_name: str) -> dict[str, str]:
    """
    Returns a mapping of column names to their PostgreSQL data types
    for a specific table.
    """
    async with Database.get_async_db() as session:
        result = await session.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        )
        rows = result.fetchall()
        return {column: dtype for column, dtype in rows}


async def get_items(
    table_name: str,
    columns: list[str],
    where_sql: str,
    filter_values: dict,
    order_sql: str,
    limit: int,
    offset: int,
) -> ItemsPaginatedOutput:
    """
    Returns items from a table with filtering, ordering and pagination.
    """
    sql = f"""
        SELECT {", ".join(columns)}
        FROM {table_name}
        {where_sql}
        {order_sql}
        LIMIT :limit OFFSET :offset
    """

    filter_values["limit"] = limit
    filter_values["offset"] = offset

    async with Database.get_async_db() as db:
        result = await db.execute(text(sql), filter_values)
        rows = [dict(row) for row in result.mappings().all()]
        next_offset = offset + len(rows) if len(rows) == limit else None

        return ItemsPaginatedOutput(
            items=rows, count=len(rows), next_offset=next_offset
        )


async def insert_item(
    table_name: str, data: dict[str, str | int | float]
) -> CreateItemOutput:
    """
    Inserts a new item into the specified table.
    """
    fields = list(data.keys())
    columns_str = ", ".join(fields)
    values_str = ", ".join([f":{f}" for f in fields])
    sql = f"""
        INSERT INTO {table_name}
        ({columns_str}) VALUES ({values_str})
        RETURNING *
    """

    async with Database.get_async_db() as db:
        result = await db.execute(text(sql), data)
        row = result.mappings().fetchone()

        if row is None:
            raise ValueError("Insert operation did not return any row.")

        return CreateItemOutput(item_created=dict(row))


async def update_items(
    table_name: str,
    set_clauses: list[str],
    set_values: dict,
    where_sql: str,
    where_values: dict,
) -> UpdateItemsOutput:
    """
    Updates an item in the specified table.
    """
    sql = f"""
        UPDATE {table_name}
        SET {", ".join(set_clauses)}
        {where_sql}
        RETURNING *
    """
    params = {**set_values, **where_values}

    async with Database.get_async_db() as db:
        result = await db.execute(text(sql), params)
        rows = result.mappings().fetchall()

        if not rows:
            raise ItemNotFoundError()

        updated_items = [dict(row) for row in rows]

        return UpdateItemsOutput(updated_items=updated_items)


async def delete_items(table_name: str, where_sql: str, values: dict[str, Any]) -> int:
    """
    Deletes items from a table and returns the number of rows deleted.
    """
    sql = f"""
        WITH deleted AS (
            DELETE FROM {table_name}
            {where_sql}
            RETURNING 1
        )
        SELECT COUNT(*) AS num_deleted FROM deleted
    """
    async with Database.get_async_db() as db:
        result = await db.execute(text(sql), values)
        return int(result.scalar_one())
