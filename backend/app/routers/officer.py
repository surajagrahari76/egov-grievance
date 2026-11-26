from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User
from app.schemas.auth import PaginatedResponse
from app.schemas.grievance import GrievanceOut
from app.schemas.officer import (
    GrievanceAssignRequest,
    GrievanceReassignDepartmentRequest,
    GrievanceStatusUpdateRequest,
    OfficerSummaryOut,
)
from app.services.officer_service import (
    assign_grievance,
    get_staff_grievance_detail,
    list_officers_for_staff,
    list_staff_grievances,
    reassign_department,
    update_grievance_status,
)

STAFF_ROLES = ("officer", "dept_head", "district_head", "admin")

router = APIRouter(prefix="/officer", tags=["Officer & Staff"])


@router.get("/grievances", response_model=PaginatedResponse[GrievanceOut])
def get_staff_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    dept_id: Optional[int] = Query(default=None),
    ward_id: Optional[int] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    result = list_staff_grievances(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        dept_id=dept_id,
        ward_id=ward_id,
        priority=priority,
    )
    return PaginatedResponse[GrievanceOut](
        items=[GrievanceOut.model_validate(g) for g in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/grievances/{ticket_id}", response_model=GrievanceOut)
def get_staff_grievance(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    grievance = get_staff_grievance_detail(db, current_user, ticket_id)
    return GrievanceOut.model_validate(grievance)


@router.post("/grievances/{ticket_id}/assign", response_model=GrievanceOut)
def assign_grievance_endpoint(
    ticket_id: str,
    payload: GrievanceAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    grievance = assign_grievance(
        db=db,
        user=current_user,
        ticket_id=ticket_id,
        officer_id=payload.officer_id,
        remarks=payload.remarks,
    )
    return GrievanceOut.model_validate(grievance)


@router.patch("/grievances/{ticket_id}/status", response_model=GrievanceOut)
def update_status_endpoint(
    ticket_id: str,
    payload: GrievanceStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    grievance = update_grievance_status(
        db=db,
        user=current_user,
        ticket_id=ticket_id,
        new_status=payload.status,
        remarks=payload.remarks,
        assigned_officer_id=payload.assigned_officer_id,
    )
    return GrievanceOut.model_validate(grievance)


@router.post("/grievances/{ticket_id}/reassign", response_model=GrievanceOut)
def reassign_department_endpoint(
    ticket_id: str,
    payload: GrievanceReassignDepartmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    grievance = reassign_department(
        db=db,
        user=current_user,
        ticket_id=ticket_id,
        dept_code=payload.dept_code,
        remarks=payload.remarks,
    )
    return GrievanceOut.model_validate(grievance)


@router.get("/team", response_model=List[OfficerSummaryOut])
def get_officer_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
):
    return list_officers_for_staff(db, current_user)
