from app.domain.notifications.service import NotificationService


def get_notification_service() -> NotificationService:
    return NotificationService()
