from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.app.services.postgresql.service import Database


class Usage(Database.Base):
    __tablename__ = "usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "tokens": self.tokens,
            "cost": self.cost,
            "timestamp": self.timestamp,
        }


class ConsumptionLimit(Database.Base):
    __tablename__ = "consumption_limits"
    __table_args__ = (
        UniqueConstraint("period", "path", name="uq_consumption_limit_period_path"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str | None] = mapped_column(String, nullable=True)
    max_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "period": self.period,
            "path": self.path,
            "max_cost": self.max_cost,
            "max_tokens": self.max_tokens,
        }
