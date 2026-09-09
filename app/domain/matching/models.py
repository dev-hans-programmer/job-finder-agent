import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.preferences.models import Base


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    preference_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("preference_profiles.id", ondelete="CASCADE"), index=True
    )
    job_description_hash: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(16))
    component_scores: Mapped[dict] = mapped_column(JSON)
    matched_criteria: Mapped[list] = mapped_column(JSON)
    missing_criteria: Mapped[list] = mapped_column(JSON)
    concerns: Mapped[list] = mapped_column(JSON)
    reasoning: Mapped[str] = mapped_column(Text)
    matcher_version: Mapped[str] = mapped_column(String(64), default="rules-v1")
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
