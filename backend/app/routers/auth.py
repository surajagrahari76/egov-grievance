from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    OTPRequest,
    OTPRequestResponse,
    OTPVerifyRequest,
    PasswordLoginRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import (
    authenticate_password_user,
    request_mock_otp,
    verify_mock_otp,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/otp/request", response_model=OTPRequestResponse)
def request_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    return request_mock_otp(db, payload.phone)


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    token, user = verify_mock_otp(
        db=db,
        phone=payload.phone,
        otp=payload.otp,
        name=payload.name,
        consent_accepted=payload.consent_accepted,
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login_with_password(payload: PasswordLoginRequest, db: Session = Depends(get_db)):
    token, user = authenticate_password_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
