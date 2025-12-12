from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models.habit import Habit, User
from ..schemas.habit import HabitCreate, HabitRead

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("/", response_model=HabitRead)
async def create_habit(
    habit_data: HabitCreate,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = Habit(**habit_data.model_dump(), user_id=user.id)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


@router.get("/", response_model=list[HabitRead])
async def list_habits(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habits = session.exec(select(Habit).where(Habit.user_id == user.id)).all()
    return habits


@router.get("/{habit_id}", response_model=HabitRead)
async def get_habit(
    habit_id: int,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit
