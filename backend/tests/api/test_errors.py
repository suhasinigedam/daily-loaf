import uuid

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.config import Settings
from app.errors import DomainError, ErrorCode
from app.main import create_app


class Item(BaseModel):
    quantity: int = Field(ge=1)


class Order(BaseModel):
    items: list[Item]


probe = APIRouter()


@probe.get("/_probe/domain")
def raise_domain() -> None:
    raise DomainError(ErrorCode.PERIOD_LOCKED, "x", "paid_on")


@probe.get("/_probe/boom")
def raise_boom() -> None:
    raise RuntimeError("secret")


@probe.post("/_probe/validate")
def validate(order: Order) -> dict[str, int]:
    return {"items": len(order.items)}


@pytest.fixture
def probe_client(test_settings: Settings) -> TestClient:
    app = create_app(test_settings)
    app.include_router(probe, prefix="/api/v1")
    return TestClient(app, raise_server_exceptions=False)


def test_domain_error_shape(probe_client: TestClient) -> None:
    r = probe_client.get("/api/v1/_probe/domain")
    assert r.status_code == 409
    assert r.json() == {"error": {"code": "PERIOD_LOCKED", "message": "x", "field": "paid_on"}}
    assert uuid.UUID(r.headers["X-Request-ID"])


def test_validation_error_has_field_path(probe_client: TestClient) -> None:
    r = probe_client.post("/api/v1/_probe/validate", json={"items": [{"quantity": 0}]})
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["field"] == "items.0.quantity"


def test_unexpected_error_hides_details(probe_client: TestClient) -> None:
    r = probe_client.get("/api/v1/_probe/boom")
    assert r.status_code == 500
    assert "secret" not in r.text
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert r.headers["X-Request-ID"]


def test_unknown_route_is_not_found(probe_client: TestClient) -> None:
    r = probe_client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_request_id_is_echoed(anon_client: TestClient) -> None:
    rid = str(uuid.uuid4())
    r = anon_client.get("/api/v1/health", headers={"X-Request-ID": rid})
    assert r.headers["X-Request-ID"] == rid


def test_bad_request_id_is_replaced(anon_client: TestClient) -> None:
    r = anon_client.get("/api/v1/health", headers={"X-Request-ID": "not-a-uuid"})
    assert r.headers["X-Request-ID"] != "not-a-uuid"
    assert uuid.UUID(r.headers["X-Request-ID"])
