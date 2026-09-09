from app.domain.jobs.ingestion_service import IngestionService
from app.domain.jobs.source_service import SourceService
from app.ingestion.greenhouse import GreenhouseAdapter
from app.ingestion.lever import LeverAdapter
from app.repositories.sources import SourceRepository


def build_ingestion_service(redis=None) -> IngestionService:
    return IngestionService(
        SourceRepository(),
        {"greenhouse": GreenhouseAdapter(), "lever": LeverAdapter()},
        redis,
    )


def get_ingestion_service() -> IngestionService:
    return build_ingestion_service()


def get_source_service() -> SourceService:
    return SourceService(SourceRepository())
