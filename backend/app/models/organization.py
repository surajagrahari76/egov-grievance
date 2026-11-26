from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    helpline: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    officers = relationship("Officer", back_populates="department")
    grievances = relationship("Grievance", back_populates="department")


class Ward(Base):
    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    zone: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False, default="New Delhi")
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    geojson_bounds: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    officers = relationship("Officer", back_populates="ward")
    grievances = relationship("Grievance", back_populates="ward")


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    dept_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id", ondelete="SET NULL"), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="officer", index=True)
    designation: Mapped[str] = mapped_column(String(120), nullable=False)
    max_active_load: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="officer_profile")
    department = relationship("Department", back_populates="officers")
    ward = relationship("Ward", back_populates="officers")
    assigned_grievances = relationship("Grievance", back_populates="assigned_officer")

    __table_args__ = (Index("ix_officer_dept_ward_level", "dept_id", "ward_id", "level"),)
