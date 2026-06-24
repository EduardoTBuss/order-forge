from typing import Any

from pydantic import BaseModel, Field


class DatabaseNameOutput(BaseModel):
    database_name: str = Field(
        ...,
        description="The name of the connected PostgreSQL database.",
        examples=["my_database"],
    )


class BaseTable(BaseModel):
    table_name: str = Field(
        ...,
        description="Name of the table in the database.",
        examples=["test_employees"],
    )


class Table(BaseTable):
    columns: list[str] = Field(
        default_factory=list,
        description="List of column names available for the given table.",
        examples=[["first_name", "last_name"]],
    )


class DisabledTable(BaseTable):
    disabled_columns: list[str] = Field(
        default_factory=list,
        description="List of columns that are disabled for this table.",
        examples=[["salary"]],
    )
    is_fully_disabled: bool | None = Field(
        default=False,
        description="Whether the entire table is disabled.",
        examples=[False],
    )


class TableListOutput(BaseModel):
    tables: list[Table] = Field(
        ...,
        description="List of allowed tables with their enabled columns.",
        examples=[
            [
                {
                    "table_name": "employees",
                    "columns": ["first_name", "last_name", "email"],
                },
                {"table_name": "departments", "columns": ["id", "name"]},
            ]
        ],
    )


class DisabledTableListOutput(BaseModel):
    disabled_tables: list[DisabledTable] = Field(
        ...,
        description="List of tables and columns that are disabled.",
        examples=[
            [
                {
                    "table_name": "employees",
                    "disabled_columns": ["salary", "ssn"],
                    "is_fully_disabled": False,
                },
                {
                    "table_name": "audit_logs",
                    "disabled_columns": [],
                    "is_fully_disabled": True,
                },
            ]
        ],
    )


class AddOrUpdateDisabledTableInput(DisabledTable):
    """
    Input for creating or updating a disabled table rule.
    """

    pass


class QueryItemsInput(BaseTable):
    filters: dict[str, str] | None = Field(
        default=None,
        description="Dictionary of filters in the format {'column': 'op:value'}.",
        examples=[{"age": "gt:30"}],
    )
    columns: list[str] = Field(
        ...,
        description="List of column names to include in the result.",
        examples=[["id", "first_name", "salary"]],
    )
    order_by: str | None = Field(
        default=None,
        description="Optional ordering clause.",
        examples=["first_name:asc", "salary:desc"],
    )
    limit: int = Field(
        default=100,
        le=500,
        description="Maximum number of rows to return (max 500).",
        examples=[100],
    )
    offset: int = Field(default=0, description="Offset for pagination.", examples=[0])


class BaseFilters(BaseTable):
    filters: dict[str, str] = Field(
        ...,
        description="Dictionary of filters in the format {'column': 'op:value'}.",
        examples=[{"age": "eq:25"}],
    )


class BaseQuery(Table, BaseFilters):
    pass


class CreateItemInput(BaseTable):
    columns: dict[str, Any] = Field(
        ...,
        description="Key-value pairs representing the row to insert.",
        examples=[
            {
                "first_name": "Alice",
                "last_name": "Smith",
                "department": "Marketing",
                "salary": 5000,
            }
        ],
    )


class UpdateItemInput(BaseFilters):
    update: dict[str, Any] = Field(
        ...,
        description="Key-value pairs representing the fields to update.",
        examples=[{"salary": 6000}],
    )


class DeleteItemsInput(BaseFilters):
    """
    Input for deleting rows from a table using filters.
    """

    pass


class CreateItemOutput(BaseModel):
    item_created: dict[str, Any] = Field(
        ...,
        description="Columns of the inserted item.",
        examples=[{"id": 1, "first_name": "Alice", "last_name": "Smith"}],
    )


class UpdateItemsOutput(BaseModel):
    updated_items: list[dict[str, Any]] = Field(
        ...,
        description="List of updated items with allowed columns.",
        examples=[
            {"id": 1, "first_name": "Alice", "last_name": "Smith"},
            {"id": 2, "first_name": "Bob", "last_name": "Jones"},
        ],
    )


class DeleteItemsOutput(BaseModel):
    deleted_count: int = Field(..., description="Number of rows deleted.", examples=[5])


class ItemsPaginatedOutput(BaseModel):
    items: list[dict[str, Any]] = Field(
        ...,
        description="List of rows returned from the query.",
        examples=[
            [
                {"id": 1, "first_name": "Alice", "last_name": "Smith"},
                {"id": 2, "first_name": "Bob", "last_name": "Jones"},
            ]
        ],
    )
    count: int = Field(
        ..., description="Total number of items that match the filters.", examples=[25]
    )
    next_offset: int | None = Field(
        default=None,
        description="Offset to use for fetching the next page of results.",
        examples=[100],
    )
