from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.habit import HabitPeriod


class HabitBase(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    period: HabitPeriod


class HabitCreate(HabitBase):
    model_config = ConfigDict(extra="forbid")


class HabitRead(HabitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    period: HabitPeriod | None = None
    model_config = ConfigDict(extra="forbid")


class HabitStats(BaseModel):
    current_streak_days: int
    total_logs: int


class HabitWithStatsRead(HabitRead):
    stats: HabitStats | None = None
