"""Tests for middleware components."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.infrastructure.middleware import ClientCacheMiddleware, SecurityHeadersMiddleware


def _create_app_with_middleware(
    cache: bool = False,
    security: bool = False,
    environment: str = "development",
    max_age: int = 60,
) -> FastAPI:
    app = FastAPI()

    if cache:
        app.add_middleware(ClientCacheMiddleware, max_age=max_age)
    if security:
        app.add_middleware(SecurityHeadersMiddleware, environment=environment)

    @app.get("/api/v1/users")
    async def api_route():
        return {"users": []}

    @app.get("/static/logo.png")
    async def static_route():
        return {"file": "logo"}

    return app


# === ClientCacheMiddleware ===


@pytest.mark.asyncio
async def test_api_paths_get_no_cache():
    app = _create_app_with_middleware(cache=True, max_age=120)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users")

    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "private, no-cache, no-store, must-revalidate"


@pytest.mark.asyncio
async def test_static_paths_get_public_cache():
    app = _create_app_with_middleware(cache=True, max_age=120)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/static/logo.png")

    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "public, max-age=120"


# === SecurityHeadersMiddleware ===


@pytest.mark.asyncio
async def test_security_headers_present_in_dev():
    app = _create_app_with_middleware(security=True, environment="development")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users")

    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert resp.headers["x-xss-protection"] == "0"
    assert "camera=()" in resp.headers["permissions-policy"]
    # HSTS should NOT be set in dev
    assert "strict-transport-security" not in resp.headers


@pytest.mark.asyncio
async def test_hsts_set_in_production():
    app = _create_app_with_middleware(security=True, environment="production")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users")

    assert "strict-transport-security" in resp.headers
    assert "max-age=" in resp.headers["strict-transport-security"]
    assert "includeSubDomains" in resp.headers["strict-transport-security"]


@pytest.mark.asyncio
async def test_hsts_set_in_staging():
    app = _create_app_with_middleware(security=True, environment="staging")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users")

    assert "strict-transport-security" in resp.headers
