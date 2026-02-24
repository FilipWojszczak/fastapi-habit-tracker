from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.habit import (
    HabitCreate,
    HabitRead,
    HabitStats,
    HabitUpdate,
    HabitWithStatsRead,
)
from ..schemas.habit_log import HabitLogRead
from ..utils.stats import current_streak_days, longest_streak_days

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post(
    "/",
    response_model=HabitRead,
    status_code=201,
    summary="Create a new habit for the authenticated user",
    description=(
        "Creates a new habit associated with the currently authenticated user.\n\n"
        "The habit must have a name, period and optional description"
    ),
)
async def create_habit(
    habit_data: HabitCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = Habit(**habit_data.model_dump(), user_id=user.id)
    await session.add(habit)
    await session.commit()
    await session.refresh(habit)
    return habit


@router.get(
    "/",
    response_model=list[HabitWithStatsRead],
    summary="List habits belonging to the authenticated user",
    description=(
        "Returns all habits owned by the authenticated user.\n\n"
        "Only habits belonging to the current user are returned.  \n"
        "Supports optional expansion with statistics using the `include_stats` query "
        "parameter."
    ),
)
async def list_habits(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    include_stats: bool = False,
):
    statement = select(Habit).where(Habit.user_id == user.id)

    if include_stats:
        statement = statement.options(selectinload(Habit.logs))

    habits = await session.exec(statement).all()

    if not include_stats:
        return habits

    to_return: list[HabitWithStatsRead] = []
    for habit in habits:
        logs = sorted(habit.logs, key=lambda log: log.performed_at, reverse=True)

        habit_out = HabitWithStatsRead.model_validate(habit)
        habit_out.stats = HabitStats(
            total_logs=len(logs),
            current_streak_days=current_streak_days(logs),
        )

        to_return.append(habit_out)

    return to_return


@router.get(
    "/{habit_id}",
    response_model=HabitRead,
    summary="Retrieve a single habit",
    description=(
        "Returns details of a habit identified by its ID.\n\n"
        "A 404 error is returned if the habit does not exist or does not belong to the "
        "current user."
    ),
)
async def get_habit(
    habit_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = await session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.put(
    "/{habit_id}",
    response_model=HabitRead,
    summary="Update a habit",
    description=(
        "Updates the selected habit.  \n"
        "Only fields provided in the request body are modified.\n\n"
        "Acts like a PATCH endpoint (partial update).  \n"
        "A 404 error is returned if the habit does not exist or does not belong to the "
        "current user."
    ),
)
async def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = await session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    habit.updated_at = datetime.now(UTC)
    habit_data_dict = habit_data.model_dump(exclude_unset=True)
    habit.sqlmodel_update(habit_data_dict)
    await session.add(habit)
    await session.commit()
    await session.refresh(habit)
    return habit


@router.delete(
    "/{habit_id}",
    status_code=204,
    summary="Delete a habit",
    description=(
        "Deletes the specified habit belonging to the authenticated user.  \n"
        "A 404 error is returned if the habit does not exist or does not belong to the "
        "current user.\n\n"
        "The associated logs remain in the database unless explicitly removed."
    ),
)
async def delete_habit(
    habit_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = await session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    await session.delete(habit)
    await session.commit()
    return


@router.get(
    "/{habit_id}/logs",
    response_model=list[HabitLogRead],
    summary="List log entries for a habit",
    description=(
        "Returns log entries for a specific habit.\n\n"
        "Supports filtering by date range (`since`, `to`) and a limit of returned "
        "entries.  \n"
        "The results are sorted from newest to oldest.\n\n"
        "A 404 error is returned if the habit does not exist or does not belong to the "
        "current user."
    ),
)
async def list_logs_for_habit(
    habit_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    since: date | None = None,
    to: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    if since is not None and to is not None and since > to:
        raise HTTPException(status_code=422, detail="'since' must be before 'to'")
    habit = await session.get(Habit, habit_id)
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

    return await session.exec(statement).all()


@router.get(
    "/{habit_id}/stats",
    summary="Retrieve statistics for a habit",
    description=(
        "`total_logs` - number of all logs for a habit  \n"
        "`last_performed_at` - timestamp for the newest log  \n"
        "`unique_days` - number of days which any log was saved at  \n"
        "`current_streak_days` - days with saved log in a row, calculated from today "
        "(or yesterday if there is no log today)  \n"
        "`longest_streak_days` - the longest set of days with saved log in a row"
    ),
)
async def get_stats_for_habit(
    habit_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    since: date | None = None,
    to: date | None = None,
):
    if since is not None and to is not None and since > to:
        raise HTTPException(status_code=422, detail="'since' must be before 'to'")
    habit = await session.get(Habit, habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")

    statement = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if since is not None:
        since_dt = datetime.combine(since, time.min)
        statement = statement.where(HabitLog.performed_at >= since_dt)
    if to is not None:
        to_dt = datetime.combine(to, time.max)
        statement = statement.where(HabitLog.performed_at <= to_dt)
    statement = statement.order_by(HabitLog.performed_at.desc())
    logs = await session.exec(statement).all()

    if not logs:
        to_return = {
            "total_logs": 0,
            "last_performed_at": None,
            "unique_days": 0,
            "longest_streak_days": 0,
        }
    else:
        to_return = {}
        to_return["total_logs"] = len(logs)
        to_return["last_performed_at"] = logs[0].performed_at
        to_return["unique_days"] = len(set(log.performed_at.date() for log in logs))
        to_return["longest_streak_days"] = longest_streak_days(logs)

    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)

    is_range_historical = to is not None and to < yesterday
    is_range_future = since is not None and since > today

    if is_range_historical or is_range_future:
        to_return["current_streak_days"] = (
            "The provided date range does not include today or yesterday."
        )
    else:
        if not logs:
            to_return["current_streak_days"] = 0
        else:
            to_return["current_streak_days"] = current_streak_days(logs)

    return to_return
