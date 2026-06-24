class TableNotFoundError(ValueError):
    def __init__(self, table_name: str):
        super().__init__(f"Table '{table_name}' does not exist")


class ColumnNotFoundError(ValueError):
    def __init__(self, table_name: str, columns: list[str]):
        cols = ", ".join(columns)
        super().__init__(f"Columns not found in table '{table_name}': {cols}")


class ForbiddenUpdateError(PermissionError):
    pass


class ItemNotFoundError(ValueError):
    def __init__(self):
        super().__init__("No matching item found.")
