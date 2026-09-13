from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.preferences import router as preferences_router
from app.api.v1.runs import router as runs_router
from app.api.v1.sources import router as sources_router
from app.api.v1.users import router as users_router
from app.api.v2.health import router as health_v2_router
from app.api.v2.preferences import router as preferences_v2_router
from app.config import Settings, get_settings
from app.db import RuntimeResources
from app.observability.errors import AppError, app_error_handler
from app.observability.logging import configure_logging, request_id_middleware
from app.observability.rate_limit import rate_limit_middleware
from app.observability.telemetry import configure_telemetry, instrument_app, instrument_clients


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    configure_telemetry(app_settings)
    instrument_clients(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        resources = RuntimeResources(app_settings)
        app.state.resources = resources
        try:
            yield
        finally:
            await resources.close()

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.settings = app_settings
    instrument_app(app, app_settings)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(health_router)
    app.include_router(preferences_router)
    app.include_router(sources_router)
    app.include_router(runs_router)
    app.include_router(jobs_router)
    app.include_router(notifications_router)
    app.include_router(metrics_router)
    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(health_v2_router)
    app.include_router(preferences_v2_router)
    return app


app = create_app()
