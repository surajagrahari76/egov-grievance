import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.governance import Notification
from app.models.grievance import Grievance

logger = logging.getLogger(__name__)


def notify_status_change(
    db: Session,
    grievance: Grievance,
    from_status: Optional[str],
    to_status: str,
    remarks: Optional[str] = None,
) -> None:
    """Create in-app notification for citizen and emit clearly marked mock SMS/Email logs."""
    title = f"Ticket {grievance.ticket_id} is now {to_status.replace('_', ' ').title()}"
    msg = f"Status changed from {from_status or 'new'} to {to_status}."
    if remarks:
        msg = f"{msg} Remarks: {remarks}"

    if grievance.user_id is not None:
        db.add(
            Notification(
                user_id=grievance.user_id,
                grievance_id=grievance.id,
                channel="in_app",
                title=title,
                message=msg,
                is_read=False,
                delivery_status="delivered",
            )
        )

    mock_sms = f"[MOCK SMS NOTIFICATION] Ticket={grievance.ticket_id} | User={grievance.user_id or 'anonymous'} | {title}"
    mock_email = f"[MOCK EMAIL NOTIFICATION] Ticket={grievance.ticket_id} | {msg}"
    logger.info(mock_sms)
    logger.info(mock_email)
