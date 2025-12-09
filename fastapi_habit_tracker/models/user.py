from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .habit import Habit


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)

    habits: List["Habit"] = Relationship(back_populates="user")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
