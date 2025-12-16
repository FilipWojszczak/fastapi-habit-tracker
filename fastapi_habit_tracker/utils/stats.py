from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from itertools import pairwise

from fastapi_habit_tracker.models import HabitLog


def current_streak_days(logs: Sequence[HabitLog]) -> int:
    if not logs:
        return 0

    # Extract unique dates in descending order
    dates = []
    for log in logs:
        d = log.performed_at.date()
        if not dates or dates[-1] != d:
            dates.append(d)
    # dates[0] = newest day, dates[-1] = oldest day

    today = datetime.now(UTC).date()

    # streak exists only if the first (newest) log is today or yesterday
    if dates[0] < today - timedelta(days=1):
        return 0

    streak = 1

    # iterate descending: dates[0], dates[1], dates[2], ...
    for prev, curr in pairwise(dates):
        # prev is newer, curr is older
        if prev - curr == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


def longest_streak_days(logs: Sequence[HabitLog]) -> int:
    if not logs:
        return 0

    # Extract unique dates in descending order
    dates = []
    for log in logs:
        d = log.performed_at.date()
        if not dates or dates[-1] != d:
            dates.append(d)
    # dates[0] = newest, dates[-1] = oldest

    longest = 1
    current = 1

    for prev, curr in pairwise(dates):
        if prev - curr == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest
