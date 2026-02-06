from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..ai.extractor import extract_habit_data
from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.ai import AILogRequest
from ..schemas.habit_log import HabitLogRead

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/log",
    response_model=HabitLogRead,
    summary="Create a habit log via AI",
    description=(
        "Analyzes natural language text to log a habit.\n\n"
        "1. Fetches user's available habits.  \n"
        "2. Uses LLM to match text to a habit and extract details.  \n"
        "3. Saves the new log to the database.  \n"
    ),
)
def log_habit_with_ai(
    request: AILogRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    statement = select(Habit).where(Habit.user_id == user.id)
    habits = session.exec(statement).all()

    if not habits:
        raise HTTPException(
            status_code=400,
            detail="You don't have any habits to track yet. Create one first!",
        )

    habit_names = [h.name for h in habits]

    try:
        extraction_result = extract_habit_data(request.text, habit_names)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI processing failed: {e!s}"
        ) from e

    matched_habit = next(
        (h for h in habits if h.name.lower() == extraction_result.habit_name.lower()),
        None,
    )

    if not matched_habit:
        raise HTTPException(
            status_code=400,
            detail=(
                f"AI identified '{extraction_result.habit_name}', but I couldn't find "
                "this habit in your list."
            ),
        )

    new_log = HabitLog(
        habit_id=matched_habit.id,
        value=extraction_result.value,
        note=extraction_result.note,
    )

    session.add(new_log)
    session.commit()
    session.refresh(new_log)

    return new_log
