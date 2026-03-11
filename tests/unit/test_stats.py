from datetime import UTC, datetime, timedelta

from fastapi_habit_tracker.utils.stats import current_streak_days, longest_streak_days


def create_date(days_ago: int):
    return (datetime.now(UTC) - timedelta(days=days_ago)).date()


def test_streak_empty_logs():
    logs = []

    assert current_streak_days(logs) == 0
    assert longest_streak_days(logs) == 0


def test_current_streak_active_today():
    logs = [create_date(0)]

    assert current_streak_days(logs) == 1
    assert longest_streak_days(logs) == 1


def test_current_streak_broken_yesterday():
    logs = [create_date(0), create_date(2)]

    assert current_streak_days(logs) == 1
    assert longest_streak_days(logs) == 1


def test_longest_streak_calculation():
    logs = [
        create_date(0),
        create_date(1),
        create_date(4),
        create_date(5),
        create_date(6),
    ]

    assert current_streak_days(logs) == 2
    assert longest_streak_days(logs) == 3


def test_current_streak_is_zero_when_old_logs_only():
    logs = [create_date(2), create_date(3)]

    assert current_streak_days(logs) == 0
    assert longest_streak_days(logs) == 2
