import pytest

from app.money import format_eur


@pytest.mark.parametrize(
    ("cents", "text"),
    [(55, "0,55 €"), (123456, "1.234,56 €"), (-500, "-5,00 €"), (0, "0,00 €")],
)
def test_format_eur(cents: int, text: str) -> None:
    assert format_eur(cents) == text
