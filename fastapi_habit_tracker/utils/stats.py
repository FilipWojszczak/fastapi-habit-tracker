from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise


def current_streak_days(unique_dates_desc: Sequence[date]) -> int:
    if not unique_dates_desc:
        return 0

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


def longest_streak_days(unique_dates_desc: Sequence[date]) -> int:
    if not unique_dates_desc:
        return 0

    longest = 1
    current = 1

    for prev, curr in pairwise(unique_dates_desc):
        if prev - curr == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest
