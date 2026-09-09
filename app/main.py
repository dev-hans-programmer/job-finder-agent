from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.db import RuntimeResources
from app.errors import AppError, app_error_handler
from app.health import router as health_router
from app.logging import configure_logging, request_id_middleware


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
    return app


app = create_app()
