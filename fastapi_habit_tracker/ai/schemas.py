from enum import StrEnum
from typing import Annotated, Literal, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import add_messages
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


class ExtractionStatus(StrEnum):
    MATCH = "match"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


class LoggingAgentDecision(BaseModel):
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


class LoggingAgentState(TypedDict):
    user_input: str
    chat_history: list[str]
    available_habits: list[str]
    decision: LoggingAgentDecision | None
    question: str | None
    attempt_count: int


class UserDecision(BaseModel):
    decision: Literal["approve", "reject"] = Field(
        description=(
            "User's decision regarding the proposed SQL query. MUST be one of: "
            "'approve' if the user accepted the proposed SQL query, 'reject' if the "
            "user rejected the proposed SQL query or if the response is ambiguous or "
            "incomprehensible."
        )
    )


class InfoAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: int
    user_decision_text: str | None
    user_decision: UserDecision | None
