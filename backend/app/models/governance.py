from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    grievance_id: Mapped[int | None] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="in_app", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(32), default="delivered", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class SLARule(Base):
    __tablename__ = "sla_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (Index("ix_sla_rule_lookup", "dept_id", "category", "priority"),)


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    from_level: Mapped[str] = mapped_column(String(32), nullable=False)
    to_level: Mapped[str] = mapped_column(String(32), nullable=False)
    escalate_after_breach_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    from_officer_id: Mapped[int | None] = mapped_column(ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    to_officer_id: Mapped[int | None] = mapped_column(ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    from_level: Mapped[str] = mapped_column(String(32), nullable=False)
    to_level: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    grievance = relationship("Grievance", back_populates="escalations")


class AIOverride(Base):
    __tablename__ = "ai_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id: Mapped[int | None] = mapped_column(ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_value: Mapped[str] = mapped_column(String(64), nullable=False)
    officer_value: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    grievance = relationship("Grievance", back_populates="ai_overrides")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class FAQDocument(Base):
    __tablename__ = "faq_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
