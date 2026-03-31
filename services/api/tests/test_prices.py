"""Tests for the /api/v1/prices/* endpoints (PostgreSQL backend)."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# GET /prices/latest
# ---------------------------------------------------------------------------


def test_latest_returns_200(pg_client: TestClient) -> None:
    assert pg_client.get("/api/v1/prices/latest").status_code == 200


def test_latest_response_envelope(pg_client: TestClient) -> None:
    body = pg_client.get("/api/v1/prices/latest").json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)
    assert body["meta"]["source"] == "postgresql"


def test_latest_record_fields(pg_client: TestClient) -> None:
    body = pg_client.get("/api/v1/prices/latest").json()
    assert len(body["data"]) == 1
    record = body["data"][0]
    assert record["commodity_id"] == "CL=F"
    assert record["commodity_name"] == "Crude Oil WTI"
    assert record["price_close"] == 75.5


def test_latest_invalid_commodity_returns_422(pg_client: TestClient) -> None:
    assert pg_client.get("/api/v1/prices/latest?commodity=INVALID").status_code == 422


def test_latest_valid_commodity_filter(pg_client: TestClient) -> None:
    assert pg_client.get("/api/v1/prices/latest?commodity=CL=F").status_code == 200


# ---------------------------------------------------------------------------
# GET /prices/history
# ---------------------------------------------------------------------------


def test_history_returns_200(pg_client: TestClient) -> None:
    assert pg_client.get("/api/v1/prices/history").status_code == 200


def test_history_with_date_range(pg_client: TestClient) -> None:
    resp = pg_client.get("/api/v1/prices/history?start_date=2024-01-01&end_date=2024-01-31")
    assert resp.status_code == 200


def test_history_inverted_date_range_returns_422(pg_client: TestClient) -> None:
    resp = pg_client.get("/api/v1/prices/history?start_date=2024-06-01&end_date=2024-01-01")
    assert resp.status_code == 422


def test_history_invalid_commodity_returns_422(pg_client: TestClient) -> None:
    assert pg_client.get("/api/v1/prices/history?commodity=NOPE").status_code == 422


def test_history_response_envelope(pg_client: TestClient) -> None:
    body = pg_client.get("/api/v1/prices/history").json()
    assert body["status"] == "success"
    assert body["meta"]["source"] == "postgresql"


# ---------------------------------------------------------------------------
# GET /prices/commodities
# ---------------------------------------------------------------------------


def test_commodities_returns_200(commodity_client: TestClient) -> None:
    assert commodity_client.get("/api/v1/prices/commodities").status_code == 200


def test_commodities_response_envelope(commodity_client: TestClient) -> None:
    body = commodity_client.get("/api/v1/prices/commodities").json()
    assert body["status"] == "success"
    assert body["meta"]["source"] == "postgresql"


def test_commodities_record_fields(commodity_client: TestClient) -> None:
    body = commodity_client.get("/api/v1/prices/commodities").json()
    assert len(body["data"]) == 1
    record = body["data"][0]
    assert record["commodity_id"] == "CL=F"
    assert record["category"] == "Energy"
    assert record["exchange"] == "NYMEX"
