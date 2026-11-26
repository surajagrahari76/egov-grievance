import math
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import generate_anonymous_code, hash_token
from app.models.grievance import Attachment, Grievance, StatusHistory
from app.models.organization import Department, Ward
from app.models.user import User
from app.schemas.grievance import GrievanceCreate
from app.services.classifier import classify_department
from app.services.storage_service import save_validated_upload


def generate_ticket_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    for _ in range(10):
        suffix = f"{secrets.randbelow(900000) + 100000}"
        ticket = f"GRV-{year}-{suffix}"
        exists = db.query(Grievance.id).filter(Grievance.ticket_id == ticket).first()
        if not exists:
            return ticket
    return f"GRV-{year}-{secrets.token_hex(4).upper()}"


async def create_grievance(
    db: Session,
    payload: GrievanceCreate,
    current_user: Optional[User],
    files: list[UploadFile] | None = None,
) -> tuple[Grievance, Optional[str]]:
    if not payload.consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privacy consent is required before submitting a grievance",
        )

    if not payload.is_anonymous and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login is required for non-anonymous complaints, or select anonymous filing",
        )

    dept_id = None
    category = (payload.category or "").strip().lower()
    if category:
        dept = db.query(Department).filter(Department.code == category).first()
        if dept:
            dept_id = dept.id
    else:
        dept = classify_department(db, f"{payload.title} {payload.text}")
        if dept:
            dept_id = dept.id
            category = dept.code
        else:
            category = "general"
            dept_id = None

    if payload.ward_id is not None:
        ward = db.query(Ward).filter(Ward.id == payload.ward_id).first()
        if not ward:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected ward not found")

    ticket_id = generate_ticket_id(db)
    anonymous_code = generate_anonymous_code() if payload.is_anonymous else None
    now = datetime.now(timezone.utc)

    grievance = Grievance(
        ticket_id=ticket_id,
        user_id=None if payload.is_anonymous else current_user.id,
        is_anonymous=payload.is_anonymous,
        anonymous_code_hash=hash_token(anonymous_code) if anonymous_code else None,
        title=payload.title.strip(),
        text=payload.text.strip(),
        language=payload.language,
        category=category,
        priority="medium",
        status="submitted",
        lat=payload.lat,
        lng=payload.lng,
        address=payload.address.strip() if payload.address else None,
        ward_id=payload.ward_id,
        dept_id=dept_id,
        sla_deadline=now + timedelta(hours=48),
        estimated_resolution_at=now + timedelta(hours=48),
    )
    db.add(grievance)
    db.flush()

    db.add(
        StatusHistory(
            grievance_id=grievance.id,
            from_status=None,
            to_status="submitted",
            changed_by_user_id=None if payload.is_anonymous else current_user.id,
            remarks="Grievance submitted by citizen" + (" (anonymous)" if payload.is_anonymous else ""),
            is_system_action=False,
        )
    )

    for upload in files or []:
        if not upload.filename:
            continue
        meta = await save_validated_upload(upload, ticket_id)
        db.add(
            Attachment(
                grievance_id=grievance.id,
                file_path=meta["file_path"],
                original_name=meta["original_name"],
                mime_type=meta["mime_type"],
                size_bytes=meta["size_bytes"],
            )
        )

    db.commit()
    loaded = get_grievance_by_ticket(db, ticket_id)
    return loaded, anonymous_code


def get_grievance_by_ticket(db: Session, ticket_id: str) -> Grievance:
    grievance = (
        db.query(Grievance)
        .options(
            selectinload(Grievance.attachments),
            selectinload(Grievance.status_history),
            joinedload(Grievance.department),
            joinedload(Grievance.ward),
        )
        .filter(Grievance.ticket_id == ticket_id.strip().upper())
        .first()
    )
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance ticket not found")
    return grievance


def list_user_grievances(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None,
) -> dict:
    query = (
        db.query(Grievance)
        .options(
            selectinload(Grievance.attachments),
            selectinload(Grievance.status_history),
            joinedload(Grievance.department),
            joinedload(Grievance.ward),
        )
        .filter(Grievance.user_id == user.id)
    )
    if status_filter:
        query = query.filter(Grievance.status == status_filter)

    total = query.count()
    items = (
        query.order_by(Grievance.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, math.ceil(total / page_size))
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def track_public_grievance(
    db: Session,
    ticket_id: str,
    anonymous_code: Optional[str] = None,
) -> dict:
    grievance = get_grievance_by_ticket(db, ticket_id)
    if grievance.is_anonymous and anonymous_code:
        if grievance.anonymous_code_hash != hash_token(anonymous_code.strip().upper()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid anonymous tracking code for this ticket",
            )

    return {
        "ticket_id": grievance.ticket_id,
        "title": grievance.title,
        "category": grievance.category,
        "priority": grievance.priority,
        "status": grievance.status,
        "language": grievance.language,
        "address": None if grievance.is_anonymous else grievance.address,
        "ward_name": grievance.ward.name if grievance.ward else None,
        "department_name": grievance.department.name if grievance.department else None,
        "is_emergency": grievance.is_emergency,
        "sla_deadline": grievance.sla_deadline,
        "estimated_resolution_at": grievance.estimated_resolution_at,
        "created_at": grievance.created_at,
        "resolved_at": grievance.resolved_at,
        "status_history": grievance.status_history,
        "attachments": grievance.attachments,
    }
