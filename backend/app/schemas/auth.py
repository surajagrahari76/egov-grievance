from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class OTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    name: Optional[str] = Field(default=None, max_length=120)


class OTPRequestResponse(BaseModel):
    message: str
    mock_otp_hint: str
    expires_in_seconds: int


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=4, max_length=8)
    name: Optional[str] = Field(default=None, max_length=120)
    consent_accepted: bool = True


class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    totp_code: Optional[str] = Field(default=None, max_length=10)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    preferred_lang: str
    is_2fa_enabled: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
