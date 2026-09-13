from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.observability.metrics import prometheus

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    return prometheus()
