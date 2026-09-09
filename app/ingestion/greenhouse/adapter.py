from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ingestion.base import RateLimiter, RawJobRecord, get_json


class GreenhouseAdapter:
    def __init__(self):
        self.malformed_count = 0

    async def fetch(self, config: dict[str, Any]) -> AsyncIterator[RawJobRecord]:
        board = config["board"]
        url = config.get("url", f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
        self.malformed_count = 0
        pages = config.get("max_pages", 1)
        limiter = RateLimiter(config.get("rate_limit_seconds", 0.0))
        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(1, pages + 1):
                payload = await get_json(client, url + f"?page={page}", rate_limiter=limiter)
                jobs = payload.get("jobs", [])
                if not jobs:
                    break
                for job in jobs:
                    try:
                        location = (job.get("location") or {}).get("name")
                        yield RawJobRecord(
                            external_id=str(job["id"]),
                            title=job["title"],
                            description=job.get("content", ""),
                            application_url=job.get("absolute_url", ""),
                            location=location,
                            raw_payload=job,
                        )
                    except (KeyError, TypeError):
                        self.malformed_count += 1
