from datetime import datetime

from pydantic import BaseModel, Field

value_description = "Minutes or repetitions (depends on habit type)"


class HabitLogCreate(BaseModel):
    habit_id: int
    performed_at: datetime | None = None
    note: str | None = None
    value: int | None = Field(default=None, description=value_description, ge=0)


class HabitLogRead(BaseModel):
    id: int
    habit_id: int
    performed_at: datetime
    note: str | None = None
    value: int | None = Field(default=None, description=value_description)

    class Config:
        from_attributes = True


class HabitLogUpdate(BaseModel):
    habit_id: int | None = None
    performed_at: datetime | None = None
    note: str | None = None
    value: int | None = Field(default=None, description=value_description, ge=0)
    model_config = {"extra": "forbid"}
