from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.observability.metrics import prometheus, prometheus_content_type

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(prometheus(), media_type=prometheus_content_type())
