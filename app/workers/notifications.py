"""Notification worker execution boundary."""

import asyncio

from app.notifications.base import is_retryable


async def run_with_dead_letter(operation, *, max_attempts: int = 3):
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            return await operation()
        except Exception as error:
            if not is_retryable(error) or attempts == max_attempts:
                return {"status": "dead_letter", "attempts": attempts, "error": str(error)}
            await asyncio.sleep(0)
