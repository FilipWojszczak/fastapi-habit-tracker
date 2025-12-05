from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List

from .user import User

if TYPE_CHECKING:
    from .habit_log import HabitLog


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    name: str
    description: Optional[str] = None
    period: str  # "daily" | "weekly"

    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    user: User = Relationship(back_populates="habits")
    logs: List[HabitLog] = Relationship(back_populates="habit")
