from datetime import datetime
from pydantic import BaseModel, Field


class HabitBase(BaseModel):
    name: str = Field(min_length=1)
    descrtiption: str | None = None
    period: str


class HabitCreate(HabitBase):
    pass


class HabitRead(HabitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
