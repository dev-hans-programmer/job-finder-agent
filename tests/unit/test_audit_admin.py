from unittest.mock import AsyncMock, patch

import pytest

from app.audit_admin import apply_retention
from app.dependencies.audit_admin import get_audit_admin_service


def test_audit_admin_dependency_builds_service():
    assert get_audit_admin_service().repository is not None


@pytest.mark.asyncio
async def test_apply_retention_uses_configured_policy():
    settings = type(
        "Settings",
        (),
        {
            "audit_retention_days": 30,
            "audit_archive_enabled": False,
            "audit_archive_dir": "./audit",
        },
    )()
    resources = type("Resources", (), {})()
    resources.session_factory = lambda: AsyncContext()
    resources.close = AsyncMock()
    service = type("Service", (), {"apply_retention": AsyncMock(return_value={"deleted": 1})})()
    with (
        patch("app.audit_admin.get_settings", return_value=settings),
        patch("app.audit_admin.RuntimeResources", return_value=resources),
        patch("app.audit_admin.AuditService", return_value=service),
    ):
        assert await apply_retention() == {"deleted": 1}
    resources.close.assert_awaited_once()


class AsyncContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *args):
        return None
