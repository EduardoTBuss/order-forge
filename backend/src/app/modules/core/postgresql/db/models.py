from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.app.services.postgresql.service import Database


class DisabledTable(Database.Base):
    __tablename__ = "disabled_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(unique=True)
    disabled_columns: Mapped[list[str]] = mapped_column(
        ARRAY(String), server_default="{}"
    )
    is_fully_disabled: Mapped[bool] = mapped_column(default=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "disabled_columns": self.disabled_columns,
            "is_fully_disabled": self.is_fully_disabled,
        }
