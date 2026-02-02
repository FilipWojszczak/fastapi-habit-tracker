from datetime import UTC, datetime
from typing import Protocol

from fastapi_habit_tracker.models import User


class UserFactory(Protocol):
    def __call__(self, email: str, password: str = "securepassword") -> User: ...


class TokenFactory(Protocol):
    def __call__(self, user: User) -> str: ...


def dt_with_tzinfo_from_isoformat(iso_str: str) -> datetime:
    datetime_obj = datetime.fromisoformat(iso_str)
    if datetime_obj.tzinfo is None:
        datetime_obj = datetime_obj.replace(tzinfo=UTC)
    return datetime_obj
