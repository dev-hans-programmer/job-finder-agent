import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.jobs.models import Job
from app.domain.matching.models import MatchResult
from app.domain.preferences.models import PreferenceProfile
from app.domain.preferences.schemas import PreferenceInput
from app.matching.rule_engine import evaluate_rules
from app.repositories.jobs import JobRepository
from app.repositories.matching import MatchingRepository
from app.repositories.preferences import PreferenceRepository


class MatchingService:
    def __init__(self, jobs=None, preferences=None, matches=None):
        self.jobs = jobs or JobRepository()
        self.preferences = preferences or PreferenceRepository()
        self.matches = matches or MatchingRepository()

    async def match_job(
        self, session: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> MatchResult | None:
        job = await self.jobs.get(session, job_id)
        profile = await self.preferences.get_active(session, user_id)
        if job is None or profile is None:
            return None
        return await self.evaluate(session, job, profile)

    async def evaluate(
        self, session: AsyncSession, job: Job, profile: PreferenceProfile
    ) -> MatchResult:
        preferences = PreferenceInput.model_validate(profile.config)
        decision = evaluate_rules(job, preferences)
        result = MatchResult(
            job_id=job.id,
            preference_profile_id=profile.id,
            job_description_hash=job.description_hash,
            score=decision.score,
            confidence=decision.confidence,
            decision=decision.decision,
            component_scores=decision.component_scores,
            matched_criteria=decision.matched_criteria,
            missing_criteria=decision.missing_criteria,
            concerns=decision.concerns,
            reasoning=decision.reasoning,
        )
        return await self.matches.create(session, result)
