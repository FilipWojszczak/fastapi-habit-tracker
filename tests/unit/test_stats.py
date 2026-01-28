from datetime import UTC, datetime, timedelta

from fastapi_habit_tracker.models import HabitLog
from fastapi_habit_tracker.utils.stats import current_streak_days, longest_streak_days


def create_log(days_ago: int):
    return HabitLog(performed_at=datetime.now(UTC) - timedelta(days=days_ago))


def test_streak_empty_logs():
    logs = []

    assert current_streak_days(logs) == 0
    assert longest_streak_days(logs) == 0


def test_current_streak_active_today():
    logs = [create_log(0)]

    assert current_streak_days(logs) == 1
    assert longest_streak_days(logs) == 1


def test_current_streak_broken_yesterday():
    logs = [create_log(0), create_log(2)]

    assert current_streak_days(logs) == 1
    assert longest_streak_days(logs) == 1


def test_longest_streak_calculation():
    logs = [
        create_log(0),
        create_log(1),
        create_log(4),
        create_log(5),
        create_log(6),
    ]

    assert current_streak_days(logs) == 2
    assert longest_streak_days(logs) == 3


def test_current_streak_is_zero_when_old_logs_only():
    logs = [create_log(2), create_log(3)]

    assert current_streak_days(logs) == 0
    assert longest_streak_days(logs) == 2
