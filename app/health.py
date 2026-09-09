from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db import check_postgres, check_redis

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(request: Request) -> JSONResponse:
    resources = request.app.state.resources
    postgres_ok, redis_ok = await check_postgres(resources), await check_redis(resources)
    if postgres_ok and redis_ok:
        return JSONResponse(status_code=200, content={"status": "ok"})
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "DEPENDENCY_UNAVAILABLE",
                "message": "One or more dependencies are unavailable",
                "details": {"postgres": postgres_ok, "redis": redis_ok},
                "request_id": request.state.request_id,
            }
        },
    )
