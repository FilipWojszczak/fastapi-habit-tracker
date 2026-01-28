from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from itertools import pairwise

from ..models import HabitLog


def _unique_dates_desc(logs: Sequence[HabitLog]) -> Sequence[HabitLog]:
    # Extract unique dates in descending order
    dates = []
    for log in logs:
        d = log.performed_at.date()
        if not dates or dates[-1] != d:
            dates.append(d)
    # dates[0] = newest day, dates[-1] = oldest day
    return dates


def current_streak_days(descending_logs: Sequence[HabitLog]) -> int:
    if not descending_logs:
        return 0

    unique_dates_desc = _unique_dates_desc(descending_logs)

    today = datetime.now(UTC).date()

    # streak exists only if the first (newest) log is today or yesterday
    if unique_dates_desc[0] < today - timedelta(days=1):
        return 0

    streak = 1

    # iterate descending: dates[0], dates[1], dates[2], ...
    for prev, curr in pairwise(unique_dates_desc):
        # prev is newer, curr is older
        if prev - curr == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


def longest_streak_days(descending_logs: Sequence[HabitLog]) -> int:
    if not descending_logs:
        return 0

    unique_dates_desc = _unique_dates_desc(descending_logs)

    longest = 1
    current = 1

    for prev, curr in pairwise(unique_dates_desc):
        if prev - curr == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest
