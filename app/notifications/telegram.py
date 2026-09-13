import httpx

from app.notifications.base import NotificationMessage


class TelegramProvider:
    def __init__(self, token: str, chat_id: str, client=None):
        self.token, self.chat_id, self.client = token, chat_id, client

    async def send(self, message: NotificationMessage) -> str:
        if not self.token or not self.chat_id:
            raise ValueError("Telegram token and chat_id are required")
        client = self.client or httpx.AsyncClient()
        response = await client.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": self.chat_id, "text": message.body},
        )
        response.raise_for_status()
        return str(response.json().get("result", {}).get("message_id", "unknown"))
