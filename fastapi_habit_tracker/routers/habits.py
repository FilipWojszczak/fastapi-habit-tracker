from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, cast, func
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
    session.add(habit)
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
    result = await session.exec(statement)
    habits = result.all()

    if not include_stats or not habits:
        return habits

    counts_stmt = (
        select(HabitLog.habit_id, func.count(HabitLog.id))
        .join(Habit)
        .where(Habit.user_id == user.id)
        .group_by(HabitLog.habit_id)
    )
    counts_result = await session.exec(counts_stmt)
    counts_by_habit = dict(counts_result.all())

    dates_stmt = (
        select(HabitLog.habit_id, cast(HabitLog.performed_at, Date))
        .join(Habit)
        .where(Habit.user_id == user.id)
        .distinct()
        .order_by(HabitLog.habit_id, cast(HabitLog.performed_at, Date).desc())
    )
    dates_result = await session.exec(dates_stmt)

    dates_by_habit = defaultdict(list)
    for h_id, log_date in dates_result.all():
        dates_by_habit[h_id].append(log_date)

    to_return: list[HabitWithStatsRead] = []
    for habit in habits:
        habit_out = HabitWithStatsRead.model_validate(habit)
        habit_out.stats = HabitStats(
            total_logs=counts_by_habit.get(habit.id, 0),
            current_streak_days=current_streak_days(dates_by_habit.get(habit.id, [])),
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
    habit_data_dict = habit_data.model_dump(exclude_unset=True)
    habit.sqlmodel_update(habit_data_dict)
    session.add(habit)
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
        since = datetime.combine(since, time.min, UTC)
        statement = statement.where(HabitLog.performed_at >= since)
    if to is not None:
        to = datetime.combine(to, time.max, UTC)
        statement = statement.where(HabitLog.performed_at <= to)
    statement = statement.order_by(HabitLog.performed_at.desc()).limit(limit)

    result = await session.exec(statement)
    return result.all()


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

    stats_stmt = select(
        func.count(HabitLog.id).label("total_logs"),
        func.max(HabitLog.performed_at).label("last_performed_at"),
        func.count(func.distinct(cast(HabitLog.performed_at, Date))).label(
            "unique_days"
        ),
    ).where(HabitLog.habit_id == habit_id)

    if since is not None:
        since_dt = datetime.combine(since, time.min, UTC)
        stats_stmt = stats_stmt.where(HabitLog.performed_at >= since_dt)
    if to is not None:
        to_dt = datetime.combine(to, time.max, UTC)
        stats_stmt = stats_stmt.where(HabitLog.performed_at <= to_dt)

    stats_result = await session.exec(stats_stmt)
    total_logs, last_performed_at, unique_days = stats_result.one()

    dates_stmt = select(cast(HabitLog.performed_at, Date)).where(
        HabitLog.habit_id == habit_id
    )
    if since is not None:
        dates_stmt = dates_stmt.where(HabitLog.performed_at >= since_dt)
    if to is not None:
        dates_stmt = dates_stmt.where(HabitLog.performed_at <= to_dt)

    dates_stmt = dates_stmt.distinct().order_by(
        cast(HabitLog.performed_at, Date).desc()
    )
    dates_result = await session.exec(dates_stmt)
    unique_dates_desc = dates_result.all()

    to_return = {
        "total_logs": total_logs,
        "last_performed_at": last_performed_at,
        "unique_days": unique_days,
        "longest_streak_days": longest_streak_days(unique_dates_desc),
    }

    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)

    is_range_historical = to is not None and to < yesterday
    is_range_future = since is not None and since > today

    if is_range_historical or is_range_future:
        to_return["current_streak_days"] = (
            "The provided date range does not include today or yesterday."
        )
    else:
        to_return["current_streak_days"] = current_streak_days(unique_dates_desc)

    return to_return
