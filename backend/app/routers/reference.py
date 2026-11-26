from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organization import Department, Ward
from app.schemas.grievance import DepartmentOut, WardOut

router = APIRouter(prefix="/reference", tags=["Reference Data"])


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).filter(Department.is_active.is_(True)).order_by(Department.id.asc()).all()


@router.get("/wards", response_model=List[WardOut])
def list_wards(db: Session = Depends(get_db)):
    return db.query(Ward).order_by(Ward.id.asc()).all()
