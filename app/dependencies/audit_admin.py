from fastapi import Depends

from app.domain.audit.service import AuditService
from app.repositories.audit import AuditRepository


def get_audit_admin_service(repository: AuditRepository = Depends()) -> AuditService:
    return AuditService(repository)
