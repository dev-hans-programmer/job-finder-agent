from fastapi import APIRouter, Request

from app.api.responses import SuccessResponse, success_response
from app.version import RuntimeMetadata, runtime_metadata

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/version", response_model=SuccessResponse[RuntimeMetadata])
async def version(request: Request) -> SuccessResponse[RuntimeMetadata]:
    return success_response(runtime_metadata(request.app.state.settings), request)
