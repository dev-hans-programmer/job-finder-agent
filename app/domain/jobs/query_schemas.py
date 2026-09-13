from pydantic import BaseModel, Field


class FeedbackInput(BaseModel):
    label: str = Field(pattern="^(saved|applied|rejected|hidden)$")
    note: str | None = None
