import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.preferences.models import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    company_name: Mapped[str] = mapped_column(String(255))
    company_normalized: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    description_hash: Mapped[str] = mapped_column(String(64), index=True)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    work_mode: Mapped[str] = mapped_column(String(16), default="unknown")
    experience_min: Mapped[int | None] = mapped_column(Integer)
    experience_max: Mapped[int | None] = mapped_column(Integer)
    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    salary_unit: Mapped[str | None] = mapped_column(String(32))
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    application_url: Mapped[str] = mapped_column(Text)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)


class JobSourceRecord(Base):
    __tablename__ = "job_source_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    raw_payload_hash: Mapped[str] = mapped_column(String(64))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
