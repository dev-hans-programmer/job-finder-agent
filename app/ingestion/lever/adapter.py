from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ingestion.base import RateLimiter, RawJobRecord, get_json


class LeverAdapter:
    def __init__(self):
        self.malformed_count = 0

    async def fetch(self, config: dict[str, Any]) -> AsyncIterator[RawJobRecord]:
        account = config["account"]
        url = config.get("url", f"https://api.lever.co/v0/postings/{account}?mode=json")
        self.malformed_count = 0
        pages = config.get("max_pages", 1)
        limiter = RateLimiter(config.get("rate_limit_seconds", 0.0))
        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(pages):
                payload = await get_json(client, url + f"&page={page}", rate_limiter=limiter)
                if not payload:
                    break
                for job in payload:
                    try:
                        categories = job.get("categories", {})
                        yield RawJobRecord(
                            external_id=str(job["id"]),
                            title=job["text"],
                            description=job.get("descriptionPlain", job.get("description", "")),
                            application_url=job.get("hostedUrl", ""),
                            location=categories.get("location"),
                            raw_payload=job,
                        )
                    except (KeyError, TypeError):
                        self.malformed_count += 1
