from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.preferences import router as preferences_router
from app.api.v1.runs import router as runs_router
from app.api.v1.sources import router as sources_router
from app.config import Settings, get_settings
from app.db import RuntimeResources
from app.observability.errors import AppError, app_error_handler
from app.observability.logging import configure_logging, request_id_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        resources = RuntimeResources(app_settings)
        app.state.resources = resources
        try:
            yield
        finally:
            await resources.close()

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(health_router)
    app.include_router(preferences_router)
    app.include_router(sources_router)
    app.include_router(runs_router)
    app.include_router(jobs_router)
    return app


app = create_app()
