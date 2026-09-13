from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class NotificationMessage:
    subject: str
    body: str


class NotificationProvider(Protocol):
    async def send(self, message: NotificationMessage) -> str: ...


def is_retryable(error: Exception) -> bool:
    code = getattr(error, "status_code", None)
    return (
        isinstance(error, (TimeoutError, ConnectionError))
        or code == 429
        or (code is not None and code >= 500)
    )
