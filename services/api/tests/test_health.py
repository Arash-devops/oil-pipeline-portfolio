"""Tests for GET /api/v1/health."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_health_has_status_field(client: TestClient) -> None:
    body = client.get("/api/v1/health").json()
    assert "status" in body


def test_health_required_fields_present(client: TestClient) -> None:
    body = client.get("/api/v1/health").json()
    for field in ("status", "postgresql", "duckdb", "timestamp", "uptime_seconds"):
        assert field in body, f"Missing field: {field}"


def test_health_reports_both_backends_healthy(client: TestClient) -> None:
    body = client.get("/api/v1/health").json()
    assert body["postgresql"] == "healthy"
    assert body["duckdb"] == "healthy"
    assert body["status"] == "healthy"


def test_health_uptime_is_non_negative(client: TestClient) -> None:
    body = client.get("/api/v1/health").json()
    assert body["uptime_seconds"] >= 0
