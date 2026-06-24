import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.app.modules.core.postgresql.db import queries
from src.app.modules.core.postgresql.logic.enums import FilterOperator
from src.app.modules.core.postgresql.schemas.io import Table


def allowed_tables_to_map(tables: list[Table]) -> dict[str, list[str]]:
    """
    Converts a list of Table objects into a dict mapping table names to their columns.
    """
    return {t.table_name: t.columns for t in tables}


def cast_filter_value(value: str, column_type: str) -> Any:
    """
    Casts a string value to the appropriate Python type based on the PostgreSQL column type.
    """
    match column_type:
        case "text" | "varchar" | "char" | "character varying":
            return value

        case "integer" | "bigint" | "smallint":
            return int(value)

        case "numeric" | "decimal" | "real" | "double precision":
            return float(value)

        case "boolean":
            return value.lower() in ("true", "1", "yes")

        case "date":
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid date format: {value} (expected YYYY-MM-DD)")

        case "timestamp" | "timestamp without time zone" | "timestamp with time zone":
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(
                    f"Invalid timestamp format: {value} (expected ISO 8601)"
                )

        case "time" | "time without time zone" | "time with time zone":
            try:
                return datetime.strptime(value, "%H:%M:%S").time()
            except ValueError:
                raise ValueError(f"Invalid time format: {value} (expected HH:MM:SS)")

        case "json" | "jsonb":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON format: {value}")

        case _:
            raise ValueError(f"Unsupported column type: '{column_type}'")


def cast_value_for_column(value: Any, column_type: str) -> Any:
    """
    Casts incoming data for inserts or updates to Python objects compatible with SQLAlchemy/asyncpg.
    """
    if value is None:
        return None

    normalized_type = column_type.lower()

    # For JSON/JSONB columns, ensure we always pass a JSON-encoded string when
    # executing raw SQL via text(); without explicit typing, passing dicts/lists
    # leads to drivers attempting to encode objects as bytes.
    if normalized_type in ("json", "jsonb"):
        if isinstance(value, str):
            # If it's a string, keep as-is (database will cast text -> json/jsonb).
            return value
        # Serialize non-string JSON-compatible values.
        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, str):
        return cast_filter_value(value, normalized_type)

    if normalized_type == "date" and isinstance(value, datetime):
        return value.date()

    if normalized_type in (
        "timestamp",
        "timestamp without time zone",
        "timestamp with time zone",
    ):
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, datetime.min.time())
        return value

    return value


async def build_where_clause_with_types(
    table_name: str,
    filters: dict[str, str],
    key_prefix: str = "val",
    column_types: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any]]:
    column_types = column_types or await queries.get_column_types(table_name)

    return _build_where_clause(filters, column_types, key_prefix)


def _build_where_clause(
    filters: dict[str, str], column_types: dict[str, str], key_prefix: str = "val"
) -> tuple[str, dict[str, Any]]:
    """
    Builds SQL WHERE clause expressions and parameters from a filter dictionary.
    """
    clauses = []
    values = {}

    for idx, (key, raw_val) in enumerate(filters.items()):
        op, val = _parse_filter(str(raw_val))
        param = f"{key_prefix}{idx}"

        column_type = column_types.get(key)
        if column_type:
            val = cast_filter_value(val, column_type)

        sql_op_map = {
            FilterOperator.EQ: f"{key} = :{param}",
            FilterOperator.LT: f"{key} < :{param}",
            FilterOperator.LTE: f"{key} <= :{param}",
            FilterOperator.GT: f"{key} > :{param}",
            FilterOperator.GTE: f"{key} >= :{param}",
        }

        sql_op = sql_op_map.get(op)
        if not sql_op:
            raise ValueError(f"Unsupported operator: {op}")

        clauses.append(sql_op)
        values[param] = val

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    return where_clause, values


def _parse_filter(raw_val: str) -> tuple[FilterOperator, Any]:
    """
    Parses a filter value like 'gte:500' into (FilterOperator.GTE, 500).
    """
    if ":" not in raw_val:
        raise ValueError(f"Invalid filter format: {raw_val}")

    op_str, val = raw_val.split(":", 1)

    try:
        op = FilterOperator(op_str)
    except ValueError:
        raise ValueError(f"Unsupported operator: {op_str}")

    return op, val


def build_order_clause(order_by: str | None) -> str:
    """
    Builds an ORDER BY SQL clause from a string like 'column:desc' or 'column'.
    Defaults to ASC if direction is not specified.
    """
    if not order_by:
        return ""

    if ":" in order_by:
        col, direction = order_by.split(":")
        direction = direction.upper()
    else:
        col = order_by
        direction = "ASC"

    return f"ORDER BY {col} {direction}"


def build_set_clause(
    data: dict,
    prefix: str = "set",
    column_types: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Builds SQL SET clause expressions and parameter dict from a dictionary of updates.
    """
    clauses = []
    values = {}

    for k, v in data.items():
        key = f"{prefix}_{k}"
        clauses.append(f"{k} = :{key}")
        if column_types and (column_type := column_types.get(k)):
            values[key] = cast_value_for_column(v, column_type)
        else:
            values[key] = v

    return clauses, values


def normalize_row(row: dict) -> dict:
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}


def cast_input_values(
    data: dict[str, Any], column_types: dict[str, str] | None
) -> dict[str, Any]:
    if not column_types:
        return dict(data)

    casted: dict[str, Any] = {}
    for key, value in data.items():
        column_type = column_types.get(key)
        if column_type:
            casted[key] = cast_value_for_column(value, column_type)
        else:
            casted[key] = value

    return casted
