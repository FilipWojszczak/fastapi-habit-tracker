from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

value_description = "Minutes or repetitions (depends on habit type)"


class HabitLogCreate(BaseModel):
    habit_id: int
    performed_at: datetime | None = None
    note: str | None = None
    value: int | None = Field(default=None, description=value_description, ge=0)
    model_config = ConfigDict(extra="forbid")


class HabitLogRead(BaseModel):
    id: int
    habit_id: int
    performed_at: datetime
    note: str | None = None
    value: int | None = Field(default=None, description=value_description)

    model_config = ConfigDict(from_attributes=True)


class HabitLogUpdate(BaseModel):
    habit_id: int | None = None
    performed_at: datetime | None = None
    note: str | None = None
    value: int | None = Field(default=None, description=value_description, ge=0)
    model_config = ConfigDict(extra="forbid")
