from app.domain.preferences.deletion_service import DeletionService


def get_deletion_service() -> DeletionService:
    return DeletionService()
