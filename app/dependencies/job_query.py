from app.domain.jobs.query_service import JobQueryService


def get_job_query_service() -> JobQueryService:
    return JobQueryService()
