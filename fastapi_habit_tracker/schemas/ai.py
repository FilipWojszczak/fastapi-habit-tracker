from enum import Enum

from pydantic import BaseModel, Field


class HabitLogData(BaseModel):
    habit_name: str = Field(
        description="The exact name of the habit from the provided list."
    )
    value: int | None = Field(
        description=(
            "The numerical value associated with the activity (e.g., minutes, pages, "
            "liters). 0 if not specified."
        )
    )
    note: str | None = Field(
        description="A short note or summary of the activity extracted from the text."
    )


class ExtractionStatus(str, Enum):
    MATCH = "match"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


class AgentDecision(BaseModel):
    status: ExtractionStatus
    habit_data: HabitLogData | None = Field(
        default=None, description="Populated ONLY if status is 'match'"
    )
    reasoning: str = Field(
        description=(
            "Brief justification for the decision. MUST be provided for ALL statuses "
            "(match, ambiguous, no_match)."
        )
    )


class AIResponse(BaseModel):
    status: str
    message: str | None = None
    log: HabitLogData | None = None
    thread_id: str | None = None
