from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .habit_log import HabitLog
    from .user import User


class HabitPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    name: str
    description: str | None = None
    period: HabitPeriod = Field(
        sa_column=Column(
            "habit_period",
            SAEnum(HabitPeriod, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
        )
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: User = Relationship(back_populates="habits")
    logs: list[HabitLog] = Relationship(
        back_populates="habit",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
