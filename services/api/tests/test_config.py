"""Unit tests for application settings (app/config.py)."""

from __future__ import annotations

from app.config import Settings


def test_default_pg_host() -> None:
    assert Settings().pg_host == "localhost"


def test_default_pg_port() -> None:
    assert Settings().pg_port == 5432


def test_default_pg_database() -> None:
    assert Settings().pg_database == "oil_warehouse"


def test_default_api_prefix() -> None:
    assert Settings().api_prefix == "/api/v1"


def test_default_api_version() -> None:
    assert Settings().api_version == "1.0.0"


def test_pg_conninfo_contains_required_keys() -> None:
    conninfo = Settings().pg_conninfo
    assert "host=" in conninfo
    assert "dbname=" in conninfo
    assert "user=" in conninfo
    assert "password=" in conninfo


def test_pg_conninfo_reflects_settings() -> None:
    s = Settings()
    assert s.pg_host in s.pg_conninfo
    assert s.pg_database in s.pg_conninfo
    assert s.pg_user in s.pg_conninfo


def test_env_prefix() -> None:
    assert Settings.model_config["env_prefix"] == "OIL_API_"


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("OIL_API_PG_HOST", "db.example.com")
    s = Settings()
    assert s.pg_host == "db.example.com"


def test_env_port_override(monkeypatch) -> None:
    monkeypatch.setenv("OIL_API_PG_PORT", "5433")
    s = Settings()
    assert s.pg_port == 5433


def test_lakehouse_base_path_is_string() -> None:
    assert isinstance(Settings().lakehouse_base_path, str)
