from typing import Literal

from pydantic import BaseModel, Field


class SourceInput(BaseModel):
    kind: Literal["greenhouse", "lever"]
    name: str = Field(min_length=1)
    config: dict
    schedule: str | None = None
    enabled: bool = True


class SourceResponse(SourceInput):
    id: str


class RunResponse(BaseModel):
    run_id: str
    status: str
