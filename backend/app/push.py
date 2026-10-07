import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Notification, PushSubscription

logger = logging.getLogger("civicconnect.push")


def notify_user(db: Session, user_id: int, title: str, message: str, type_: str = "status", complaint_id: int | None = None) -> None:
    """Store an in-app notification and attempt to deliver a real browser push to every device the user subscribed from."""
    db.add(Notification(user_id=user_id, complaint_id=complaint_id, title=title, message=message, type=type_))

    settings = get_settings()
    if not settings.vapid_private_key:
        return
    subscriptions = db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id)).all()
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps({"title": title, "body": message}),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in (404, 410):
                db.delete(sub)
            else:
                logger.warning("Push delivery failed for user %s: %s", user_id, exc)
