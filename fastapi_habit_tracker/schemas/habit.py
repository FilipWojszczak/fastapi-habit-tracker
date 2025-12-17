from datetime import datetime

from pydantic import BaseModel, Field


class HabitBase(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    period: str


class HabitCreate(HabitBase):
    model_config = {"extra": "forbid"}


class HabitRead(HabitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HabitUpdate(BaseModel):
    name: str = Field(default=None, min_length=1)
    description: str | None = None
    period: str | None = None
    model_config = {"extra": "forbid"}


class HabitStats(BaseModel):
    current_streak_days: int
    total_logs: int


class HabitWithStatsRead(HabitRead):
    stats: HabitStats | None = None
