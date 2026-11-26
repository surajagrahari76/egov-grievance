from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Grievance(Base):
    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anonymous_code_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)

    category: Mapped[str] = mapped_column(String(64), default="general", nullable=False, index=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)
    priority_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="submitted", nullable=False, index=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)

    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id", ondelete="SET NULL"), nullable=True, index=True)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_officer_id: Mapped[int | None] = mapped_column(
        ForeignKey("officers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_grievance_id: Mapped[int | None] = mapped_column(
        ForeignKey("grievances.id", ondelete="SET NULL"), nullable=True, index=True
    )

    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    spam_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    spam_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    estimated_resolution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="grievances", foreign_keys=[user_id])
    ward = relationship("Ward", back_populates="grievances")
    department = relationship("Department", back_populates="grievances")
    assigned_officer = relationship("Officer", back_populates="assigned_grievances")
    parent_grievance = relationship("Grievance", remote_side=[id], backref="duplicate_grievances")

    attachments = relationship("Attachment", back_populates="grievance", cascade="all, delete-orphan")
    status_history = relationship(
        "StatusHistory", back_populates="grievance", cascade="all, delete-orphan", order_by="StatusHistory.created_at"
    )
    feedback = relationship("Feedback", back_populates="grievance", uselist=False, cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="grievance", cascade="all, delete-orphan")
    ai_overrides = relationship("AIOverride", back_populates="grievance", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_grievance_status_priority", "status", "priority"),
        Index("ix_grievance_dept_status", "dept_id", "status"),
        Index("ix_grievance_ward_category", "ward_id", "category"),
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_vision_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_vision_caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    grievance = relationship("Grievance", back_populates="attachments")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system_action: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    grievance = relationship("Grievance", back_populates="status_history")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(
        ForeignKey("grievances.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reopen_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    grievance = relationship("Grievance", back_populates="feedback")
