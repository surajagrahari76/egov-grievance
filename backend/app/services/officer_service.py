import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.grievance import Grievance, StatusHistory
from app.models.organization import Department, Officer
from app.models.user import User
from app.services.grievance_service import get_grievance_by_ticket
from app.services.notification_service import notify_status_change

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"assigned", "in_progress"},
    "assigned": {"in_progress", "resolved"},
    "in_progress": {"resolved", "assigned"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
    "reopened": {"assigned", "in_progress"},
}

PRIORITY_ORDER = case(
    (Grievance.priority == "critical", 0),
    (Grievance.priority == "high", 1),
    (Grievance.priority == "medium", 2),
    (Grievance.priority == "low", 3),
    else_=4,
)


def _get_caller_officer(db: Session, user: User) -> Optional[Officer]:
    return db.query(Officer).filter(Officer.user_id == user.id).first()


def _ensure_staff_access(db: Session, user: User, grievance: Grievance) -> Optional[Officer]:
    officer = _get_caller_officer(db, user)
    if user.role in ("admin", "district_head"):
        return officer
    if not officer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff officer profile not found")
    if grievance.dept_id != officer.dept_id and grievance.assigned_officer_id != officer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage grievances outside your department",
        )
    return officer


def list_staff_grievances(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    dept_id: Optional[int] = None,
    ward_id: Optional[int] = None,
    priority: Optional[str] = None,
) -> dict:
    query = db.query(Grievance).options(
        selectinload(Grievance.attachments),
        selectinload(Grievance.status_history),
        joinedload(Grievance.department),
        joinedload(Grievance.ward),
    )

    if user.role in ("officer", "dept_head"):
        officer = _get_caller_officer(db, user)
        if not officer:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        query = query.filter(Grievance.dept_id == officer.dept_id)
    elif dept_id is not None:
        query = query.filter(Grievance.dept_id == dept_id)

    if status_filter:
        query = query.filter(Grievance.status == status_filter)
    if ward_id is not None:
        query = query.filter(Grievance.ward_id == ward_id)
    if priority:
        query = query.filter(Grievance.priority == priority)

    total = query.count()
    items = (
        query.order_by(PRIORITY_ORDER, Grievance.created_at.desc())
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


def get_staff_grievance_detail(db: Session, user: User, ticket_id: str) -> Grievance:
    grievance = get_grievance_by_ticket(db, ticket_id)
    _ensure_staff_access(db, user, grievance)
    return grievance


def assign_grievance(
    db: Session,
    user: User,
    ticket_id: str,
    officer_id: Optional[int] = None,
    remarks: Optional[str] = None,
) -> Grievance:
    grievance = get_grievance_by_ticket(db, ticket_id)
    caller_officer = _ensure_staff_access(db, user, grievance)

    target_officer: Optional[Officer] = None
    if officer_id is not None:
        target_officer = db.query(Officer).filter(Officer.id == officer_id).first()
        if not target_officer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target officer not found")
    else:
        target_officer = caller_officer

    if target_officer:
        grievance.assigned_officer_id = target_officer.id

    from_status = grievance.status
    if from_status == "submitted":
        grievance.status = "assigned"

    note = remarks or (
        f"Assigned to {target_officer.designation}" if target_officer else "Assigned by staff"
    )
    db.add(
        StatusHistory(
            grievance_id=grievance.id,
            from_status=from_status,
            to_status=grievance.status,
            changed_by_user_id=user.id,
            remarks=note,
            is_system_action=False,
        )
    )
    notify_status_change(db, grievance, from_status, grievance.status, note)
    db.commit()
    return get_grievance_by_ticket(db, ticket_id)


def update_grievance_status(
    db: Session,
    user: User,
    ticket_id: str,
    new_status: str,
    remarks: Optional[str] = None,
    assigned_officer_id: Optional[int] = None,
) -> Grievance:
    grievance = get_grievance_by_ticket(db, ticket_id)
    caller_officer = _ensure_staff_access(db, user, grievance)

    current_status = grievance.status
    if new_status == current_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grievance is already in '{current_status}' status",
        )

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed: {sorted(allowed)}",
        )

    if assigned_officer_id is not None:
        target = db.query(Officer).filter(Officer.id == assigned_officer_id).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned officer not found")
        grievance.assigned_officer_id = target.id
    elif new_status == "assigned" and grievance.assigned_officer_id is None and caller_officer is not None:
        grievance.assigned_officer_id = caller_officer.id

    now = datetime.now(timezone.utc)
    grievance.status = new_status
    if new_status == "resolved":
        grievance.resolved_at = now
    elif new_status == "closed":
        if grievance.resolved_at is None:
            grievance.resolved_at = now
        grievance.closed_at = now

    note = (remarks or "").strip() or f"Status updated to {new_status.replace('_', ' ')}"
    db.add(
        StatusHistory(
            grievance_id=grievance.id,
            from_status=current_status,
            to_status=new_status,
            changed_by_user_id=user.id,
            remarks=note,
            is_system_action=False,
        )
    )
    notify_status_change(db, grievance, current_status, new_status, note)
    db.commit()
    return get_grievance_by_ticket(db, ticket_id)


def reassign_department(
    db: Session,
    user: User,
    ticket_id: str,
    dept_code: str,
    remarks: Optional[str] = None,
) -> Grievance:
    grievance = get_grievance_by_ticket(db, ticket_id)
    _ensure_staff_access(db, user, grievance)

    target_dept = (
        db.query(Department)
        .filter(Department.code == dept_code.strip().lower(), Department.is_active.is_(True))
        .first()
    )
    if not target_dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target department not found")

    old_category = grievance.category
    grievance.dept_id = target_dept.id
    grievance.category = target_dept.code
    grievance.assigned_officer_id = None

    note = (remarks or "").strip() or f"Reassigned from '{old_category}' to '{target_dept.name}'"
    db.add(
        StatusHistory(
            grievance_id=grievance.id,
            from_status=grievance.status,
            to_status=grievance.status,
            changed_by_user_id=user.id,
            remarks=note,
            is_system_action=False,
        )
    )
    notify_status_change(db, grievance, grievance.status, grievance.status, note)
    db.commit()
    return get_grievance_by_ticket(db, ticket_id)


def list_officers_for_staff(db: Session, user: User) -> list[dict]:
    query = db.query(Officer).options(joinedload(Officer.user)).filter(Officer.is_available.is_(True))
    if user.role in ("officer", "dept_head"):
        caller = _get_caller_officer(db, user)
        if not caller:
            return []
        query = query.filter(Officer.dept_id == caller.dept_id)

    officers = query.order_by(Officer.id.asc()).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "name": o.user.name if o.user else o.designation,
            "email": o.user.email if o.user else None,
            "dept_id": o.dept_id,
            "ward_id": o.ward_id,
            "level": o.level,
            "designation": o.designation,
        }
        for o in officers
    ]
