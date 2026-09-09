import hashlib
import re
from dataclasses import dataclass

from app.ingestion.base import RawJobRecord


@dataclass(frozen=True)
class JobCandidate:
    title: str
    company_name: str
    company_normalized: str
    description: str
    description_hash: str
    locations: list[str]
    application_url: str
    external_id: str
    raw_payload: dict | None


def normalize_company(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def description_hash(description: str) -> str:
    return hashlib.sha256(description.strip().encode()).hexdigest()


def normalize_record(record: RawJobRecord, company_name: str) -> JobCandidate:
    description = record.description or ""
    return JobCandidate(
        title=" ".join(record.title.split()),
        company_name=company_name.strip(),
        company_normalized=normalize_company(company_name),
        description=description,
        description_hash=description_hash(description),
        locations=[record.location] if record.location else [],
        application_url=record.application_url,
        external_id=record.external_id,
        raw_payload=record.raw_payload,
    )
