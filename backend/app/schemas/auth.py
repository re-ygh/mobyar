from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str = Field(..., examples=["09120000000"])
    password: str = Field(..., examples=["admin123"])


class UserOut(BaseModel):
    user_id: int
    name: str
    phone: str
    email: str | None = None
    status: str
    role_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
