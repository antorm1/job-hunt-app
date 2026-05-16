"""Tests for Job Hunt App backend."""

import pytest
from datetime import datetime
from main import (
    _make_id, _clean, cache_get, cache_set, cache_clear,
)


class TestHelpers:
    def test_make_id_is_deterministic(self):
        a = _make_id("remotive", "hello")
        b = _make_id("remotive", "hello")
        assert a == b

    def test_make_id_differs_by_source(self):
        a = _make_id("remotive", "hello")
        b = _make_id("arbeitnow", "hello")
        assert a != b

    def test_make_id_differs_by_text(self):
        a = _make_id("remotive", "hello")
        b = _make_id("remotive", "world")
        assert a != b

    def test_make_id_length(self):
        assert len(_make_id("x", "y")) == 12

    def test_clean_strips_html(self):
        assert _clean("<p>Hello <b>world</b></p>") == "Hello world"

    def test_clean_truncates_long_text(self):
        long = "x" * 600
        result = _clean(long, max_len=100)
        assert len(result) <= 104  # 100 + "…"
        assert result.endswith("…")

    def test_clean_handles_none(self):
        assert _clean(None) == ""

    def test_clean_strips_newlines(self):
        assert _clean("hello\nworld\rtest") == "hello world test"


class TestCache:
    def setup_method(self):
        cache_clear()

    def test_cache_set_and_get(self):
        cache_set("key1", {"value": 42})
        result = cache_get("key1")
        assert result == {"value": 42}

    def test_cache_miss(self):
        assert cache_get("nonexistent") is None

    def test_cache_clear(self):
        cache_set("k", {"v": 1})
        cache_clear()
        assert cache_get("k") is None

    def test_cache_expired(self):
        cache_set("exp", {"v": 1})
        # Manually expire it
        from main import _cache
        from datetime import timedelta
        _cache["exp"]["expires"] = datetime.utcnow() - timedelta(seconds=1)
        assert cache_get("exp") is None


class TestAPIEndpoints:
    """Integration-style tests using TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_categories(self, client):
        resp = client.get("/api/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert len(data["categories"]) > 1

    def test_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "sources" in data

    def test_jobs_returns_structure(self, client):
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert "total" in data
        assert "sources" in data
        assert "page" in data
        assert "per_page" in data
        assert "has_more" in data

    def test_jobs_pagination(self, client):
        resp = client.get("/api/jobs?page=1&per_page=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_jobs_search(self, client):
        resp = client.get("/api/jobs?search=python")
        assert resp.status_code == 200

    def test_cache_clear(self, client):
        resp = client.post("/api/cache/clear")
        assert resp.status_code == 200
