from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_roles
from app.models.user import User
from app.schemas.auth import PaginatedResponse
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceCreateResponse,
    GrievanceOut,
    GrievanceTrackPublicOut,
)
from app.services.grievance_service import (
    create_grievance,
    get_grievance_by_ticket,
    list_user_grievances,
    track_public_grievance,
)

router = APIRouter(prefix="/grievances", tags=["Grievances"])


@router.post("", response_model=GrievanceCreateResponse, status_code=status.HTTP_201_CREATED)
async def submit_grievance(
    title: str = Form(..., min_length=4, max_length=200),
    text: str = Form(..., min_length=10, max_length=5000),
    category: Optional[str] = Form(default=None),
    language: str = Form(default="en"),
    lat: Optional[float] = Form(default=None),
    lng: Optional[float] = Form(default=None),
    address: Optional[str] = Form(default=None),
    ward_id: Optional[int] = Form(default=None),
    is_anonymous: bool = Form(default=False),
    consent_accepted: bool = Form(default=True),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    payload = GrievanceCreate(
        title=title,
        text=text,
        category=category or None,
        language=language,
        lat=lat,
        lng=lng,
        address=address or None,
        ward_id=ward_id,
        is_anonymous=is_anonymous,
        consent_accepted=consent_accepted,
    )
    grievance, anon_code = await create_grievance(db, payload, current_user, files)
    return GrievanceCreateResponse(
        grievance=GrievanceOut.model_validate(grievance),
        anonymous_tracking_code=anon_code,
    )


@router.get("/mine", response_model=PaginatedResponse[GrievanceOut])
def get_my_grievances(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = list_user_grievances(db, current_user, page=page, page_size=page_size, status_filter=status_filter)
    return PaginatedResponse[GrievanceOut](
        items=[GrievanceOut.model_validate(g) for g in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/track/{ticket_id}", response_model=GrievanceTrackPublicOut)
def track_ticket_public(
    ticket_id: str,
    anonymous_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return track_public_grievance(db, ticket_id, anonymous_code=anonymous_code)


@router.get("/{ticket_id}", response_model=GrievanceOut)
def get_grievance_detail(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grievance = get_grievance_by_ticket(db, ticket_id)
    if current_user.role == "citizen" and grievance.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this grievance")
    return GrievanceOut.model_validate(grievance)


@router.get("/rbac-check/staff-only", tags=["RBAC"])
def staff_only_check(current_user: User = Depends(require_roles("officer", "dept_head", "district_head", "admin"))):
    return {"ok": True, "role": current_user.role}
