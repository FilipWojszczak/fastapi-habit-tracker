from datetime import datetime

from pydantic import BaseModel, Field


class HabitLogCreate(BaseModel):
    habit_id: int
    performed_at: datetime | None = None
    note: str | None = None
    value: int | None = Field(
        default=None, description="Minutes or repetitions (depends on habit type)", ge=0
    )


class HabitLogRead(BaseModel):
    id: int
    habit_id: int
    performed_at: datetime
    note: str | None
    value: int | None = Field(
        description="Minutes or repetitions (depends on habit type)"
    )

    class Config:
        from_attributes = True
