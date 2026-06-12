"""Tests for the SK + PostgreSQL orders assistant (real kernel + plugin, mock table)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_mock():
    body = client.get("/health").json()
    assert body["framework"] == "semantic-kernel"
    assert body["store"] == "mock"


def test_known_order():
    r = client.post("/api/v1/orders/ask", json={"question": "where is order ORD-1001?"})
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == "ORD-1001"
    assert body["found"] is True
    assert body["status"] == "shipped"
    assert "Jordan Avery" in body["answer"]
    assert body["invoked_via"] == "semantic-kernel native plugin"


def test_unknown_order():
    r = client.post("/api/v1/orders/ask", json={"question": "status of ORD-9999"})
    body = r.json()
    assert body["found"] is False
    assert body["status"] == "not_found"


def test_no_order_id():
    r = client.post("/api/v1/orders/ask", json={"question": "where is my order?"})
    assert r.json()["order_id"] is None


def test_validation_rejects_empty():
    assert client.post("/api/v1/orders/ask", json={"question": ""}).status_code == 422
