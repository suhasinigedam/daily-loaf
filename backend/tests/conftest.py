import pytest
from fastapi.testclient import TestClient

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