"""Version 2 example showing how to evolve an existing endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v2", tags=["health-v2"])


@router.get("/health/live")
async def live_v2() -> dict[str, str]:
    """Return the same liveness signal with an explicit API version."""
    return {"status": "ok", "api_version": "v2"}
