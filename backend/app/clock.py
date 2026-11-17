import re
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.errors import DomainError, ErrorCode

BERLIN = ZoneInfo("Europe/Berlin")
_MONTH_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


def today_berlin(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(BERLIN).date()


def month_start(d: date) -> date:
    return d.replace(day=1)


def next_month(m: date) -> date:
    return (m.replace(day=28) + timedelta(days=4)).replace(day=1)


def prev_month(m: date) -> date:
    return (m.replace(day=1) - timedelta(days=1)).replace(day=1)


def month_end(m: date) -> date:
    return next_month(m) - timedelta(days=1)


def parse_month(s: str) -> date:
    match = _MONTH_PATTERN.match(s)
    if match and 1 <= int(match[2]) <= 12:
        return date(int(match[1]), int(match[2]), 1)
    raise DomainError(ErrorCode.VALIDATION_ERROR, "Month must look like 2026-10", field="month")


def format_month(m: date) -> str:
    return m.strftime("%Y-%m")
