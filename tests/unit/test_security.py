from types import SimpleNamespace

import pytest
from starlette.responses import Response

from app.observability.security import csrf_middleware, security_headers_middleware


def request(settings, method="GET", cookies=None, headers=None):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(settings=settings)),
        method=method,
        cookies=cookies or {},
        headers=headers or {},
    )


async def next_response(_):
    return Response("ok")


@pytest.mark.asyncio
async def test_security_headers_are_added_without_hsts():
    settings = SimpleNamespace(security_headers_enabled=True, hsts_enabled=False)
    response = await security_headers_middleware(request(settings), next_response)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_security_headers_can_add_optional_hsts_or_be_disabled():
    settings = SimpleNamespace(security_headers_enabled=True, hsts_enabled=True)
    response = await security_headers_middleware(request(settings), next_response)
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
    disabled = SimpleNamespace(security_headers_enabled=False, hsts_enabled=False)
    response = await security_headers_middleware(request(disabled), next_response)
    assert "X-Frame-Options" not in response.headers


@pytest.mark.asyncio
async def test_csrf_is_required_only_for_cookie_auth_when_enabled():
    settings = SimpleNamespace(csrf_enabled=True)
    blocked = await csrf_middleware(
        request(settings, method="POST", cookies={"access_token": "cookie"}),
        next_response,
    )
    assert blocked.status_code == 403
    allowed = await csrf_middleware(
        request(
            settings,
            method="POST",
            cookies={"access_token": "cookie", "csrf_token": "csrf"},
            headers={"X-CSRF-Token": "csrf"},
        ),
        next_response,
    )
    assert allowed.status_code == 200
    bearer = await csrf_middleware(
        request(settings, method="POST", headers={"Authorization": "Bearer token"}),
        next_response,
    )
    assert bearer.status_code == 200
    disabled = await csrf_middleware(
        request(SimpleNamespace(csrf_enabled=False), method="POST", cookies={"access_token": "x"}),
        next_response,
    )
    assert disabled.status_code == 200
