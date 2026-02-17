from pydantic import BaseModel

from ..ai.schemas import HabitLogData


class LoggingAgentResponse(BaseModel):
    status: str
    message: str | None = None
    log: HabitLogData | None = None
    thread_id: str | None = None
