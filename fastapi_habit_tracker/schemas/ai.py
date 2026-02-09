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


class AILogRequest(BaseModel):
    text: str
