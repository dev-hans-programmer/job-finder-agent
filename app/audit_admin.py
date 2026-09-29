"""One-shot audit retention operations."""

import asyncio

from app.config import get_settings
from app.db import RuntimeResources, session_scope
from app.domain.audit.service import AuditService
from app.repositories.audit import AuditRepository


async def apply_retention():
    settings = get_settings()
    resources = RuntimeResources(settings)
    try:
        async with session_scope(resources) as session:
            return await AuditService(AuditRepository()).apply_retention(
                session,
                retention_days=settings.audit_retention_days,
                archive_enabled=settings.audit_archive_enabled,
                archive_dir=settings.audit_archive_dir,
            )
    finally:
        await resources.close()


def main():  # pragma: no cover
    result = asyncio.run(apply_retention())
    print(result)


if __name__ == "__main__":  # pragma: no cover
    main()
