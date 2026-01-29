from datetime import UTC, datetime


def dt_with_tzinfo_from_isoformat(iso_str: str) -> datetime:
    datetime_obj = datetime.fromisoformat(iso_str)
    if datetime_obj.tzinfo is None:
        datetime_obj = datetime_obj.replace(tzinfo=UTC)
    return datetime_obj
