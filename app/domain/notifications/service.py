import uuid

from app.domain.jobs.models import Job
from app.domain.matching.models import MatchResult
from app.notifications.base import NotificationMessage, is_retryable
from app.notifications.templates import render_match
from app.repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, repository=None):
        self.repository = repository or NotificationRepository()

    async def get_for_user(self, session, delivery_id, user_id):
        return await self.repository.get_for_user(session, delivery_id, user_id)

    async def deliver(
        self,
        session,
        user_id: uuid.UUID,
        job: Job,
        profile_id: uuid.UUID,
        match: MatchResult,
        channel: str,
        provider,
    ):
        if match.decision != "notify":
            return None
        delivery, created = await self.repository.get_or_create(
            session, user_id=user_id, job_id=job.id, profile_id=profile_id, channel=channel
        )
        if not created and delivery.status == "delivered":
            return delivery
        delivery.attempt_count += 1
        try:
            subject, body = render_match(job, match)
            delivery.provider_message_id = await provider.send(NotificationMessage(subject, body))
            delivery.status, delivery.error = "delivered", None
        except Exception as error:
            delivery.status = "retryable" if is_retryable(error) else "failed"
            delivery.error = str(error)
        await session.commit()
        await session.refresh(delivery)
        return delivery
