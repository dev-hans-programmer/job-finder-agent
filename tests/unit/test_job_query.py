import uuid
from types import SimpleNamespace

import pytest

from app.api.v1.jobs import _match_payload, get_job, get_match, list_jobs, save_feedback
from app.dependencies.job_query import get_job_query_service
from app.domain.jobs.query_schemas import FeedbackInput
from app.domain.jobs.query_service import JobQueryService


class FakeJobs:
    def __init__(self, job=None, feedback=None):
        self.job, self.saved = job, feedback

    async def list(self, *args, **kwargs):
        return ([self.job] if self.job else [], 1 if self.job else 0)

    async def get(self, *args):
        return self.job

    async def feedback(self, *args):
        return self.saved

    async def save_feedback(self, session, value):
        self.saved = value
        return value


class FakeMatches:
    async def latest(self, *args):
        return SimpleNamespace(
            id=uuid.uuid4(),
            score=80,
            confidence=0.8,
            decision="notify",
            component_scores={},
            matched_criteria=[],
            missing_criteria=[],
            concerns=[],
            reasoning="ok",
        )


class FakeSession:
    async def commit(self):
        return None

    async def refresh(self, value):
        return None


def make_job():
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Backend",
        company_name="Acme",
        description="Python",
        locations=["Mumbai"],
        work_mode="hybrid",
        application_url="https://apply",
        status="active",
        last_seen_at=None,
    )


@pytest.mark.asyncio
async def test_query_service_and_routes_cover_success_paths():
    assert isinstance(get_job_query_service(), JobQueryService)
    job = make_job()
    jobs = FakeJobs(job)
    service = JobQueryService(jobs, FakeMatches())
    user_id = uuid.uuid4()
    rows, total = await service.list(
        None,
        user_id,
        page=1,
        page_size=10,
        min_score=None,
        status=None,
        company=None,
        location=None,
    )
    assert rows and total == 1
    detail = await service.detail(None, user_id, job.id)
    assert detail["job"] is job
    feedback = await service.feedback(
        None, user_id, job.id, FeedbackInput(label="saved", note="good")
    )
    assert feedback.label == "saved"
    assert (await list_jobs(user_id, None, service, 1, 10, None, None, None, None))["total"] == 1
    assert (await get_job(job.id, user_id, None, service))["job"]["id"] == str(job.id)
    assert (await get_match(job.id, user_id, None, service))["decision"] == "notify"
    saved = await save_feedback(
        job.id, FeedbackInput(label="saved"), user_id, FakeSession(), service
    )
    assert saved["label"] == "saved"
    assert _match_payload(None) is None


@pytest.mark.asyncio
async def test_query_service_not_found_paths():
    service = JobQueryService(FakeJobs(), FakeMatches())
    user_id = uuid.uuid4()
    assert await service.detail(None, user_id, uuid.uuid4()) is None
    assert (
        await service.feedback(None, user_id, uuid.uuid4(), FeedbackInput(label="hidden")) is None
    )


@pytest.mark.asyncio
async def test_query_routes_raise_not_found():
    from fastapi import HTTPException

    service = JobQueryService(FakeJobs(), FakeMatches())
    with pytest.raises(HTTPException):
        await get_job(uuid.uuid4(), uuid.uuid4(), None, service)
    with pytest.raises(HTTPException):
        await get_match(uuid.uuid4(), uuid.uuid4(), None, service)
    with pytest.raises(HTTPException):
        await save_feedback(uuid.uuid4(), FeedbackInput(label="saved"), uuid.uuid4(), None, service)
