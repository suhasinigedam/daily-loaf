from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="local",
        database_url="postgresql+psycopg://unused",
        cors_origins=["http://localhost:4200"],
        cognito_issuer="https://cognito-idp.eu-central-1.amazonaws.com/test-pool",
        cognito_client_id="test-client",
        bills_bucket="test-bills",
        business_name="Test Bakery",
        business_address="Teststraße 1, 60311 Frankfurt",
    )


@pytest.fixture
def anon_client(test_settings: Settings) -> TestClient:
    return TestClient(create_app(test_settings))


BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_cfg(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    """One throwaway Postgres for the whole test run, migrated to the latest version."""
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as pg:
        url = pg.get_connection_url()
        command.upgrade(alembic_cfg(url), "head")
        yield url


@pytest.fixture(scope="session")
def engine(pg_url: str) -> Iterator[Engine]:
    eng = create_engine(pg_url)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Each test runs inside a transaction that is rolled back afterwards."""
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield db
        finally:
            db.close()
            transaction.rollback()

@pytest.fixture
def alembic_config(pg_url: str) -> Config:
    return alembic_cfg(pg_url)