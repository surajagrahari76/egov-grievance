from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

WorkflowStatus = Literal["submitted", "assigned", "in_progress", "resolved", "closed"]


class GrievanceStatusUpdateRequest(BaseModel):
    status: WorkflowStatus
    remarks: Optional[str] = Field(default=None, max_length=1000)
    assigned_officer_id: Optional[int] = None


class GrievanceAssignRequest(BaseModel):
    officer_id: Optional[int] = None
    remarks: Optional[str] = Field(default=None, max_length=500)


class GrievanceReassignDepartmentRequest(BaseModel):
    dept_code: str = Field(..., min_length=2, max_length=32)
    remarks: Optional[str] = Field(default=None, max_length=500)


class OfficerSummaryOut(BaseModel):
    id: int
    user_id: int
    name: str
    email: Optional[str] = None
    dept_id: int
    ward_id: Optional[int] = None
    level: str
    designation: str


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grievance_id: Optional[int] = None
    channel: str
    title: str
    message: str
    is_read: bool
    delivery_status: str
    created_at: datetime
