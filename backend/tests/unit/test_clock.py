from datetime import UTC, date, datetime

import pytest

from app.clock import (
    format_month,
    month_end,
    month_start,
    next_month,
    parse_month,
    prev_month,
    today_berlin,
)
from app.errors import DomainError, ErrorCode


def test_today_berlin_after_midnight_winter() -> None:
    # 23:30 UTC = 00:30 next day in Berlin (UTC+1 in winter)
    assert today_berlin(datetime(2026, 11, 3, 23, 30, tzinfo=UTC)) == date(2026, 11, 4)


def test_today_berlin_after_midnight_summer() -> None:
    # 22:30 UTC = 00:30 next day in Berlin (UTC+2 in summer)
    assert today_berlin(datetime(2026, 7, 1, 22, 30, tzinfo=UTC)) == date(2026, 7, 2)


def test_month_helpers() -> None:
    assert month_start(date(2026, 11, 17)) == date(2026, 11, 1)
    assert month_end(date(2026, 2, 1)) == date(2026, 2, 28)
    assert next_month(date(2026, 12, 1)) == date(2027, 1, 1)
    assert prev_month(date(2026, 1, 1)) == date(2025, 12, 1)
    assert format_month(date(2026, 10, 1)) == "2026-10"


def test_parse_month() -> None:
    assert parse_month("2026-10") == date(2026, 10, 1)


@pytest.mark.parametrize("bad", ["2026-13", "2026-1", "abc", ""])
def test_parse_month_rejects_bad_input(bad: str) -> None:
    with pytest.raises(DomainError) as e:
        parse_month(bad)
    assert e.value.code == ErrorCode.VALIDATION_ERROR
    assert e.value.field == "month"
