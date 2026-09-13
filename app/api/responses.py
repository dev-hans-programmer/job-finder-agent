"""Shared HTTP response contracts and factories."""

from typing import Generic, Literal, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str = "unknown"
    api_version: str = "v1"
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1)
    total: int | None = Field(default=None, ge=0)


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T
    meta: ResponseMeta


def success_response(
    data: T,
    request: Request | None,
    *,
    api_version: str = "v1",
    page: int | None = None,
    page_size: int | None = None,
    total: int | None = None,
) -> SuccessResponse[T]:
    return SuccessResponse(
        data=data,
        meta=ResponseMeta(
            request_id=getattr(getattr(request, "state", None), "request_id", "unknown"),
            api_version=api_version,
            page=page,
            page_size=page_size,
            total=total,
        ),
    )
