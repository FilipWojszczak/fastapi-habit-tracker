from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models.habit import Habit
from ..schemas.habit import HabitCreate, HabitRead


router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("/", response_model=HabitRead)
async def create_habit(
    habit_data: HabitCreate, session: Session = Depends(get_session)
):
    habit = Habit(
        **habit_data.model_dump(), user_id=1
    )  # Temporary user_id =1 - replace with actual user ID from auth
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


@router.get("/", response_model=list[HabitRead])
async def list_habits(session: Session = Depends(get_session)):
    habits = session.exec(select(Habit).all())
    return habits


@router.get("/{habit_id}", response_model=HabitRead)
async def get_habit(habit_id: int, session: Session = Depends(get_session)):
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit
