from pydantic import BaseModel, EmailStr, Field


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)


class LoginInput(RegisterInput):
    pass


class RefreshInput(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    id: str
    device_name: str | None
    user_agent: str | None
    ip_address: str | None
    created_at: str
    last_used_at: str
    current: bool


class UserResponse(BaseModel):
    id: str
    email: str
    roles: list[str]


class RoleInput(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_-]*$")
    description: str | None = None
