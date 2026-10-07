import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal
from .models import Complaint, User
from .push import notify_user

logger = logging.getLogger("civicconnect.scheduler")

OPEN_STATUSES = ["SUBMITTED", "PENDING_REVIEW", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS"]


def check_overdue_complaints() -> None:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.sla_hours)
    db = SessionLocal()
    try:
        overdue = db.scalars(
            select(Complaint).where(
                Complaint.status.in_(OPEN_STATUSES),
                Complaint.created_at <= cutoff,
                Complaint.sla_escalated_at.is_(None),
            )
        ).all()
        for complaint in overdue:
            age_days = (datetime.now(timezone.utc) - complaint.created_at).days
            title = "Complaint overdue"
            message = f"\"{complaint.title}\" ({complaint.complaint_number}) was reported {age_days} day(s) ago and is still unresolved. Please take action today."
            if complaint.assigned_officer_id:
                notify_user(db, complaint.assigned_officer_id, title, message, type_="sla_breach", complaint_id=complaint.id)
            else:
                officers = db.scalars(select(User).where(User.role.in_(["officer", "admin"]))).all()
                for officer in officers:
                    notify_user(db, officer.id, title, message, type_="sla_breach", complaint_id=complaint.id)
            complaint.sla_escalated_at = datetime.now(timezone.utc)
        if overdue:
            db.commit()
            logger.info("Escalated %d overdue complaint(s)", len(overdue))
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(check_overdue_complaints, "interval", hours=1, next_run_time=datetime.now(timezone.utc))
    scheduler.start()
    return scheduler
