import re
from datetime import UTC, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_UTC_OFFSET_PATTERN = re.compile(
    r"^(?:UTC|GMT)?(?P<sign>[+-])(?P<hours>\d{1,2})(?::?(?P<minutes>\d{2}))?$"
)
_UTC_OFFSET_NAME_PATTERN = re.compile(
    r"^UTC(?P<sign>[+-])(?P<hours>\d{2}):(?P<minutes>\d{2})$"
)


def normalize_timezone(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None

    offset_name = _normalize_utc_offset(candidate)
    if offset_name is not None:
        return offset_name

    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return None
    return candidate


def safe_timezone(value: str) -> tzinfo:
    offset_timezone = _parse_normalized_utc_offset(value)
    if offset_timezone is not None:
        return offset_timezone

    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError:
        return UTC


def _normalize_utc_offset(value: str) -> str | None:
    match = _UTC_OFFSET_PATTERN.fullmatch(value.upper())
    if match is None:
        return None

    sign = match.group("sign")
    hours = int(match.group("hours"))
    minutes = int(match.group("minutes") or "0")
    if hours > 14 or minutes > 59 or (hours == 14 and minutes != 0):
        return None

    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def _parse_normalized_utc_offset(value: str) -> tzinfo | None:
    match = _UTC_OFFSET_NAME_PATTERN.fullmatch(value.upper())
    if match is None:
        return None

    sign = 1 if match.group("sign") == "+" else -1
    hours = int(match.group("hours"))
    minutes = int(match.group("minutes"))
    return timezone(sign * timedelta(hours=hours, minutes=minutes), value)
