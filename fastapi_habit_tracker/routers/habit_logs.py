from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.habit_log import HabitLogCreate, HabitLogRead

router = APIRouter(prefix="/habit-logs", tags=["habit logs"])


@router.post("/", response_model=HabitLogRead)
async def create_habit_log(
    habit_log_data: HabitLogCreate,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = session.get(Habit, habit_log_data.habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit_log_data.performed_at is None:
        habit_log_data.performed_at = datetime.now(UTC)
    habit_log = HabitLog(**habit_log_data.model_dump())
    session.add(habit_log)
    session.commit()
    session.refresh(habit_log)
    return habit_log
