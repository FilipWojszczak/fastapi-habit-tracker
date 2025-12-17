from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.habit import HabitCreate, HabitRead, HabitUpdate, HabitWithStatsRead
from ..schemas.habit_log import HabitLogRead
from ..utils.stats import current_streak_days, longest_streak_days

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


@router.get("/", response_model=list[HabitWithStatsRead])
async def list_habits(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    include_stats: bool = False,
):
    habits = session.exec(select(Habit).where(Habit.user_id == user.id)).all()
    if include_stats:
        to_return = []
        for habit in habits:
            habit = habit.model_dump()
            statement = select(HabitLog).where(HabitLog.habit_id == habit["id"])
            statement = statement.order_by(HabitLog.performed_at.desc())
            logs = session.exec(statement).all()
            habit["stats"] = {
                "total_logs": len(logs),
                "current_streak_days": current_streak_days(logs),
            }
            to_return.append(habit)
    else:
        to_return = habits
    return to_return


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


@router.put("/{habit_id}", response_model=HabitRead)
async def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    habit_data_dict = habit_data.model_dump(exclude_unset=True)
    for key, value in habit_data_dict.items():
        setattr(habit, key, value)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: int,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    session.delete(habit)
    session.commit()
    return {"message": "Item deleted successfully"}


@router.get("/{habit_id}/logs", response_model=list[HabitLogRead])
async def list_logs_for_habit(
    habit_id: int,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    since: date | None = None,
    to: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    if since is not None and to is not None and since > to:
        raise HTTPException(status_code=422, detail="'since' must be before 'to'")
    habit = session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")

    statement = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if since is not None:
        since = datetime.combine(since, time.min)
        statement = statement.where(HabitLog.performed_at >= since)
    if to is not None:
        to = datetime.combine(to, time.max)
        statement = statement.where(HabitLog.performed_at <= to)
    statement = statement.order_by(HabitLog.performed_at.desc()).limit(limit)

    return session.exec(statement).all()


@router.get("/{habit_id}/stats")
async def get_stats_for_habit(
    habit_id: int,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    since: date | None = None,
    to: date | None = None,
):
    if since is not None and to is not None and since > to:
        raise HTTPException(status_code=422, detail="'since' must be before 'to'")
    habit = session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")

    statement = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if since is not None:
        since = datetime.combine(since, time.min)
        statement = statement.where(HabitLog.performed_at >= since)
    if to is not None:
        to = datetime.combine(to, time.max)
        statement = statement.where(HabitLog.performed_at <= to)
    statement = statement.order_by(HabitLog.performed_at.desc())
    logs = session.exec(statement).all()

    to_return = {}
    to_return["total_logs"] = len(logs)
    to_return["last_performed_at"] = str(session.exec(statement).first().performed_at)
    to_return["unique_days"] = len(set(log.performed_at.date() for log in logs))
    to_return["current_streak_days"] = current_streak_days(logs)
    to_return["longest_streak_days"] = longest_streak_days(logs)

    return JSONResponse(to_return)
