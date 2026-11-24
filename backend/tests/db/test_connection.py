from sqlalchemy import text
from sqlalchemy.orm import Session


def test_database_reachable(session: Session) -> None:
    assert session.execute(text("select 1")).scalar_one() == 1
