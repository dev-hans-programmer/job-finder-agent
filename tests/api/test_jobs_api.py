import uuid

import pytest

from app.api.v1.jobs import match_job


class _Service:
    async def match_job(self, session, job_id, user_id):
        return type(
            "Result",
            (),
            {
                "id": job_id,
                "score": 80,
                "confidence": 0.8,
                "decision": "notify",
                "component_scores": {"role": 10},
                "matched_criteria": ["Python"],
                "missing_criteria": [],
                "concerns": [],
                "reasoning": "good fit",
            },
        )()


def test_match_missing_job_returns_not_found(client):
    response = client.post(f"/api/v1/jobs/{uuid.uuid4()}/match")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_match_job_returns_explainable_result():
    job_id = uuid.uuid4()
    response = await match_job(job_id, None, _Service(), uuid.uuid4())
    assert response["id"] == str(job_id)
    assert response["decision"] == "notify"
