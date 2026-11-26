import logging
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_token,
    verify_password,
)
from app.models.user import OtpCode, User

logger = logging.getLogger(__name__)
settings = get_settings()

OTP_TTL_SECONDS = 300


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain at least 10 digits",
        )
    return digits[-10:]


def request_mock_otp(db: Session, phone: str) -> dict:
    """Generate a 6-digit OTP and log it to console as a MOCK SMS service."""
    norm_phone = normalize_phone(phone)
    # Invalidate prior unconsumed OTPs for this phone
    db.query(OtpCode).filter(OtpCode.phone == norm_phone, OtpCode.consumed.is_(False)).update(
        {"consumed": True}
    )

    # Use deterministic 123456 only in DEMO_MODE if phone is demo citizen, else random 6-digit
    otp_plain = "123456" if (settings.DEMO_MODE and norm_phone == "9876543210") else f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=OTP_TTL_SECONDS)

    db.add(
        OtpCode(
            phone=norm_phone,
            code_hash=hash_token(otp_plain),
            expires_at=expires_at,
            consumed=False,
        )
    )
    db.commit()

    # Clearly marked MOCK SMS output
    mock_banner = f"[MOCK SMS OTP] Phone=+91-{norm_phone} | OTP={otp_plain} | Valid={OTP_TTL_SECONDS}s"
    print(mock_banner, flush=True)
    logger.info(mock_banner)

    hint = (
        f"Mock OTP logged to backend console (Demo OTP: {otp_plain})"
        if settings.APP_ENV in ("dev", "test") and settings.DEMO_MODE
        else "Mock OTP logged to backend console"
    )
    return {
        "message": "OTP sent via mock SMS gateway",
        "mock_otp_hint": hint,
        "expires_in_seconds": OTP_TTL_SECONDS,
    }


def verify_mock_otp(
    db: Session,
    phone: str,
    otp: str,
    name: str | None = None,
    consent_accepted: bool = True,
) -> tuple[str, User]:
    norm_phone = normalize_phone(phone)
    now = datetime.now(timezone.utc)

    record = (
        db.query(OtpCode)
        .filter(OtpCode.phone == norm_phone, OtpCode.consumed.is_(False))
        .order_by(OtpCode.id.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP found. Please request a new OTP.")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        record.consumed = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")

    if record.code_hash != hash_token(otp.strip()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    record.consumed = True
    user = db.query(User).filter(User.phone == norm_phone).first()
    if not user:
        if not consent_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Privacy consent must be accepted to register",
            )
        user = User(
            name=(name or f"Citizen {norm_phone[-4:]}").strip(),
            phone=norm_phone,
            role="citizen",
            consent_accepted_at=now,
            is_active=True,
        )
        db.add(user)
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive or deleted")
    elif name and name.strip() and user.name.startswith("Citizen "):
        user.name = name.strip()

    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role)
    return token, user


def authenticate_password_user(db: Session, email: str, password: str) -> tuple[str, User]:
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token = create_access_token(subject=str(user.id), role=user.role)
    return token, user
