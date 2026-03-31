"""Tests for the /api/v1/analytics/* endpoints (DuckDB/lakehouse backend)."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# GET /analytics/monthly-summary
# ---------------------------------------------------------------------------


def test_monthly_summary_returns_200(client: TestClient) -> None:
    assert client.get("/api/v1/analytics/monthly-summary").status_code == 200


def test_monthly_summary_envelope(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/monthly-summary").json()
    assert body["status"] == "success"
    assert body["meta"]["source"] == "duckdb"
    assert isinstance(body["data"], list)


def test_monthly_summary_record_fields(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/monthly-summary").json()
    assert len(body["data"]) == 1
    rec = body["data"][0]
    assert rec["commodity_id"] == "CL=F"
    assert rec["year"] == 2024
    assert rec["month"] == 1
    assert rec["avg_close"] == 75.0


def test_monthly_summary_commodity_filter(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/monthly-summary?commodity=CL=F")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


def test_monthly_summary_year_filter(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/monthly-summary?year=2024")
    assert resp.status_code == 200


def test_monthly_summary_invalid_commodity_returns_422(client: TestClient) -> None:
    assert client.get("/api/v1/analytics/monthly-summary?commodity=INVALID").status_code == 422


# ---------------------------------------------------------------------------
# GET /analytics/price-metrics
# ---------------------------------------------------------------------------


def test_price_metrics_returns_200(client: TestClient) -> None:
    assert client.get("/api/v1/analytics/price-metrics").status_code == 200


def test_price_metrics_envelope(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/price-metrics").json()
    assert body["status"] == "success"
    assert body["meta"]["source"] == "duckdb"


def test_price_metrics_record_fields(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/price-metrics").json()
    assert len(body["data"]) == 1
    rec = body["data"][0]
    assert rec["commodity_id"] == "CL=F"
    assert rec["close"] == 75.5
    assert rec["ma_7"] == 74.0
    assert rec["bollinger_upper"] == 78.0


def test_price_metrics_date_range(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/price-metrics?start_date=2024-01-01&end_date=2024-12-31")
    assert resp.status_code == 200


def test_price_metrics_inverted_date_range_returns_422(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/price-metrics?start_date=2024-06-01&end_date=2024-01-01")
    assert resp.status_code == 422


def test_price_metrics_invalid_commodity_returns_422(client: TestClient) -> None:
    assert client.get("/api/v1/analytics/price-metrics?commodity=NOPE").status_code == 422


# ---------------------------------------------------------------------------
# GET /analytics/commodity-comparison
# ---------------------------------------------------------------------------


def test_commodity_comparison_returns_200(client: TestClient) -> None:
    assert client.get("/api/v1/analytics/commodity-comparison").status_code == 200


def test_commodity_comparison_envelope(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/commodity-comparison").json()
    assert body["status"] == "success"
    assert body["meta"]["source"] == "duckdb"


def test_commodity_comparison_record_fields(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/commodity-comparison").json()
    assert len(body["data"]) == 1
    rec = body["data"][0]
    assert rec["wti_close"] == 75.5
    assert rec["brent_close"] == 76.0
    assert rec["spread"] == -0.5


def test_commodity_comparison_date_range(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/commodity-comparison?start_date=2024-01-01&end_date=2024-12-31")
    assert resp.status_code == 200


def test_commodity_comparison_inverted_dates_returns_422(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/commodity-comparison?start_date=2024-06-01&end_date=2024-01-01")
    assert resp.status_code == 422
