from app.domain.jobs.normalizer import description_hash, normalize_company, normalize_record
from app.ingestion.base import RawJobRecord


def test_normalizer_produces_stable_candidate():
    record = RawJobRecord(
        "1", "  Backend   Engineer ", "Python", "https://apply", "Mumbai", {"id": 1}
    )
    candidate = normalize_record(record, "Acme, Inc.")
    assert candidate.title == "Backend Engineer"
    assert candidate.company_normalized == "acme inc"
    assert candidate.locations == ["Mumbai"]
    assert candidate.description_hash == description_hash("Python")
    assert normalize_company("ACME, Inc.") == "acme inc"


def test_normalizer_handles_missing_location_and_description():
    record = RawJobRecord("1", "Backend", "", "https://apply")
    candidate = normalize_record(record, "Acme")
    assert candidate.locations == []
    assert candidate.description_hash == description_hash("")
