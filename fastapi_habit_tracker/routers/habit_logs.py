from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.habit_log import HabitLogCreate, HabitLogRead, HabitLogUpdate

router = APIRouter(prefix="/habit-logs", tags=["habit logs"])


@router.post(
    "/",
    response_model=HabitLogRead,
    status_code=201,
    summary="Add a new log entry to a habit",
    description=(
        "Creates a new log entry for the given habit.\n\n"
        "If `performed_at` is not provided, the current timestamp is used. \n"
        "A user may record multiple logs per day.\n\n"
        "A 404 error is returned if the habit does not exist or does not belong to the "
        "current user."
    ),
)
async def create_habit_log(
    habit_log_data: HabitLogCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit = await session.get(Habit, habit_log_data.habit_id)
    if not habit or habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit not found")
    data = habit_log_data.model_dump()

    if data["performed_at"] is None:
        data["performed_at"] = datetime.now(UTC)
    habit_log = HabitLog(**data)
    await session.add(habit_log)
    await session.commit()
    await session.refresh(habit_log)
    return habit_log


@router.put(
    "/{habit_log_id}",
    response_model=HabitLogRead,
    summary="Update an existing habit log",
    description=(
        "Updates the selected habit log.  \n"
        "Only fields provided in the request body are modified.\n\n"
        "Acts like a PATCH endpoint (partial update).  \n"
        "A 404 error is returned if the habit log does not exist or does not belong to "
        "the current user."
    ),
)
async def update_habit_log(
    habit_log_id: int,
    habit_log_data: HabitLogUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit_log = await session.get(HabitLog, habit_log_id)
    if not habit_log or habit_log.habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit log not found")
    habit_log_data_dict = habit_log_data.model_dump(exclude_unset=True)
    if "habit_id" in habit_log_data_dict:
        new_habit = await session.get(Habit, habit_log_data_dict["habit_id"])
        if not new_habit or new_habit.user_id != user.id:
            raise HTTPException(status_code=404, detail="Habit not found")
    habit_log.sqlmodel_update(habit_log_data_dict)
    await session.add(habit_log)
    await session.commit()
    await session.refresh(habit_log)
    return habit_log


@router.delete(
    "/{habit_log_id}",
    status_code=204,
    summary="Delete a habit log",
    description=(
        "Deletes the selected habit log.\n\n"
        "A 404 error is returned if the habit log does not exist or does not belong to "
        "the current user."
    ),
)
async def delete_habit_log(
    habit_log_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    habit_log = await session.get(HabitLog, habit_log_id)
    if not habit_log or habit_log.habit.user_id != user.id:
        raise HTTPException(status_code=404, detail="Habit log not found")
    await session.delete(habit_log)
    await session.commit()
    return
