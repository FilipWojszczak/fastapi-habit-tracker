from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone

from .habit import Habit


class HabitLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id")

    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc))

    habit: "Habit" = Relationship(back_populates="logs")
