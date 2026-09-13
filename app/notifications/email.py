from app.notifications.base import NotificationMessage


class EmailProvider:
    def __init__(self, recipient: str):
        self.recipient = recipient

    async def send(self, message: NotificationMessage) -> str:
        if "@" not in self.recipient:
            raise ValueError("valid email recipient is required")
        return f"outbox:{self.recipient}:{message.subject}"
