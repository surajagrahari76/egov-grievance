from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    mime_type: str
    size_bytes: int
    file_path: str
    ai_vision_label: Optional[str] = None
    ai_vision_caption: Optional[str] = None
    uploaded_at: datetime


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: Optional[str] = None
    to_status: str
    remarks: Optional[str] = None
    is_system_action: bool
    created_at: datetime


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_hi: str
    helpline: Optional[str] = None


class WardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    zone: str
    city: str
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None


class GrievanceCreate(BaseModel):
    title: str = Field(..., min_length=4, max_length=200)
    text: str = Field(..., min_length=10, max_length=5000)
    category: Optional[str] = Field(default=None, max_length=64)
    language: str = Field(default="en", max_length=16)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)
    ward_id: Optional[int] = None
    is_anonymous: bool = False
    consent_accepted: bool = True


class GrievanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    user_id: Optional[int] = None
    is_anonymous: bool
    title: str
    text: str
    language: str
    category: str
    ai_confidence: Optional[float] = None
    priority: str
    priority_reason: Optional[str] = None
    summary: Optional[str] = None
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    ward_id: Optional[int] = None
    dept_id: Optional[int] = None
    assigned_officer_id: Optional[int] = None
    parent_grievance_id: Optional[int] = None
    is_emergency: bool
    spam_flag: bool
    sla_deadline: Optional[datetime] = None
    estimated_resolution_at: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    attachments: List[AttachmentOut] = []
    status_history: List[StatusHistoryOut] = []
    department: Optional[DepartmentOut] = None
    ward: Optional[WardOut] = None


class GrievanceCreateResponse(BaseModel):
    grievance: GrievanceOut
    anonymous_tracking_code: Optional[str] = None


class GrievanceTrackPublicOut(BaseModel):
    ticket_id: str
    title: str
    category: str
    priority: str
    status: str
    language: str
    address: Optional[str] = None
    ward_name: Optional[str] = None
    department_name: Optional[str] = None
    is_emergency: bool
    sla_deadline: Optional[datetime] = None
    estimated_resolution_at: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    status_history: List[StatusHistoryOut] = []
    attachments: List[AttachmentOut] = []
