from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .user import User

if TYPE_CHECKING:
    from .habit_log import HabitLog


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    name: str
    description: str | None = None
    period: str  # "daily" | "weekly"

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: User = Relationship(back_populates="habits")
    logs: list[HabitLog] = Relationship(back_populates="habit")
