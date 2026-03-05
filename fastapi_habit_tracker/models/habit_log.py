from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .habit import Habit


class HabitLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id", ondelete="CASCADE")

    performed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    note: str | None = None
    value: int | None = Field(default=None, ge=0)

    habit: Habit = Relationship(back_populates="logs")
