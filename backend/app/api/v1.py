from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..models import Category, Complaint, ComplaintHistory, Department, Notification, PushSubscription, ResolutionProof, User
from ..push import notify_user
from ..scheduler import OPEN_STATUSES
from ..schemas import (
    AuthRequest,
    AuthResponse,
    ComplaintCreate,
    ComplaintOut,
    ComplaintUpdate,
    DashboardOut,
    NotificationOut,
    PushSubscribeRequest,
    RegisterRequest,
    UserOut,
)
from ..security import create_access_token, get_user_from_token, hash_password, verify_password

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DB = Annotated[Session, Depends(get_db)]


def current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    user = get_user_from_token(token, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_roles(*roles: str):
    def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        return user

    return dependency


def serialize_complaint(complaint: Complaint) -> ComplaintOut:
    return ComplaintOut(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        description=complaint.description,
        category=complaint.category.name if complaint.category else None,
        severity=complaint.severity,
        status=complaint.status,
        image_url=complaint.image_url,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        address=complaint.address,
        city=complaint.city,
        area=complaint.area,
        ward=complaint.ward,
        department=complaint.department.name if complaint.department else None,
        citizen_name=complaint.citizen.name if complaint.citizen else None,
        assigned_officer=complaint.assigned_officer.name if complaint.assigned_officer else None,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        resolved_at=complaint.resolved_at,
        history=complaint.history,
    )


def load_complaint(db: Session, complaint_id: int) -> Complaint:
    complaint = db.scalar(
        select(Complaint)
        .options(
            selectinload(Complaint.category),
            selectinload(Complaint.department),
            selectinload(Complaint.citizen),
            selectinload(Complaint.assigned_officer),
            selectinload(Complaint.history),
        )
        .where(Complaint.id == complaint_id)
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


def add_history(db: Session, complaint: Complaint, actor: User | None, new_status: str, comment: str | None = None) -> None:
    old_status = complaint.status
    complaint.status = new_status
    complaint.updated_at = datetime.now(timezone.utc)
    db.add(ComplaintHistory(complaint_id=complaint.id, actor_id=actor.id if actor else None, old_status=old_status, new_status=new_status, comment=comment))


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, db: DB):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(name=payload.name, email=payload.email.lower(), phone=payload.phone, password_hash=hash_password(payload.password), role="citizen")
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(access_token=create_access_token(user), user=user)


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: DB):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthResponse(access_token=create_access_token(user), user=user)


@router.get("/auth/me", response_model=UserOut)
def me(user: Annotated[User, Depends(current_user)]):
    return user


@router.post("/uploads")
async def upload_image(file: UploadFile = File(...), user: Annotated[User, Depends(current_user)] = None):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are accepted")
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be smaller than 8 MB")
    root = Path(get_settings().uploads_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    filename = f"{user.id}-{uuid4().hex}{suffix}"
    (root / filename).write_bytes(content)
    return {"url": f"/uploads/{filename}"}


@router.post("/complaints", response_model=ComplaintOut, status_code=201)
def create_complaint(payload: ComplaintCreate, db: DB, user: Annotated[User, Depends(current_user)]):
    category = db.scalar(select(Category).where(Category.name == payload.category))
    if not category:
        category = db.scalar(select(Category).where(Category.name == "Other"))
    category_departments = {
        "Road Damage": "Roads & Infrastructure", "Pothole": "Roads & Infrastructure",
        "Broken Footpath": "Roads & Infrastructure", "Public Infrastructure Damage": "Roads & Infrastructure",
        "Open Manhole": "Roads & Infrastructure", "Garbage": "Sanitation", "Illegal Dumping": "Sanitation",
        "Water Leakage": "Water Works", "Drainage": "Water Works", "Waterlogging": "Water Works",
        "Streetlight": "Electrical Services", "Traffic Signal": "Traffic & Transport", "Fallen Tree": "Parks & Emergency Services",
    }
    department_name = category_departments.get(payload.category, "General Civic Services")
    department = db.scalar(select(Department).where(Department.name == department_name)) or db.scalar(select(Department).limit(1))
    location = payload.location
    complaint = Complaint(
        complaint_number=f"CMP-{datetime.now(timezone.utc).strftime('%y%m%d')}-{uuid4().hex[:4].upper()}",
        citizen_id=user.id,
        category_id=category.id if category else None,
        title=payload.title,
        description=payload.description,
        severity=payload.severity.upper(),
        status="SUBMITTED",
        image_url=payload.image_url,
        latitude=location.latitude if location else None,
        longitude=location.longitude if location else None,
        location_accuracy=location.accuracy if location else None,
        address=location.address if location else None,
        city=location.city if location else None,
        area=location.area if location else None,
        ward=location.ward if location else None,
        department_id=department.id if department else None,
    )
    db.add(complaint)
    db.flush()
    db.add(ComplaintHistory(complaint_id=complaint.id, actor_id=user.id, old_status=None, new_status="SUBMITTED", comment="Complaint submitted by citizen"))
    notify_user(db, user.id, "Complaint submitted", "Your complaint is now being reviewed.", type_="submitted", complaint_id=complaint.id)
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.get("/complaints", response_model=list[ComplaintOut])
def list_complaints(db: DB, user: Annotated[User, Depends(current_user)], status_filter: str | None = None):
    query = select(Complaint).options(selectinload(Complaint.category), selectinload(Complaint.department), selectinload(Complaint.citizen), selectinload(Complaint.assigned_officer), selectinload(Complaint.history)).order_by(Complaint.created_at.desc())
    if user.role == "citizen":
        query = query.where(Complaint.citizen_id == user.id)
    if status_filter:
        query = query.where(Complaint.status == status_filter.upper())
    return [serialize_complaint(item) for item in db.scalars(query).all()]


@router.get("/complaints/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: DB, user: Annotated[User, Depends(current_user)]):
    complaint = load_complaint(db, complaint_id)
    if user.role == "citizen" and complaint.citizen_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own complaints")
    return serialize_complaint(complaint)


@router.patch("/complaints/{complaint_id}", response_model=ComplaintOut)
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: DB, user: Annotated[User, Depends(current_user)]):
    complaint = load_complaint(db, complaint_id)
    if user.role == "citizen" and complaint.citizen_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own complaints")
    data = payload.model_dump(exclude_unset=True)
    comment = data.pop("comment", None)
    if user.role == "citizen" and "status" in data:
        raise HTTPException(status_code=403, detail="Citizens cannot change complaint status directly")
    if "category" in data:
        category = db.scalar(select(Category).where(Category.name == data.pop("category")))
        complaint.category_id = category.id if category else complaint.category_id
    new_status = data.pop("status", None)
    for key, value in data.items():
        setattr(complaint, key, value)
    if new_status and new_status != complaint.status:
        add_history(db, complaint, user, new_status, comment)
    elif comment:
        db.add(ComplaintHistory(complaint_id=complaint.id, actor_id=user.id, old_status=complaint.status, new_status=complaint.status, comment=comment))
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.post("/complaints/{complaint_id}/verify", response_model=ComplaintOut)
def verify_resolution(complaint_id: int, accepted: bool, db: DB, user: Annotated[User, Depends(current_user)]):
    complaint = load_complaint(db, complaint_id)
    if user.role != "citizen" or complaint.citizen_id != user.id:
        raise HTTPException(status_code=403, detail="Only the reporting citizen can verify this resolution")
    add_history(db, complaint, user, "RESOLVED" if accepted else "REOPENED", "Citizen verified resolution" if accepted else "Citizen requested the issue be reopened")
    if accepted:
        complaint.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.get("/officer/complaints", response_model=list[ComplaintOut])
def officer_complaints(db: DB, user: Annotated[User, Depends(require_roles("officer", "admin"))]):
    query = select(Complaint).options(selectinload(Complaint.category), selectinload(Complaint.department), selectinload(Complaint.citizen), selectinload(Complaint.assigned_officer), selectinload(Complaint.history)).order_by(Complaint.created_at.desc())
    if user.role == "officer":
        query = query.where(or_(Complaint.assigned_officer_id == user.id, Complaint.assigned_officer_id.is_(None)))
    return [serialize_complaint(item) for item in db.scalars(query).all()]


@router.post("/officer/complaints/{complaint_id}/accept", response_model=ComplaintOut)
def accept_complaint(complaint_id: int, db: DB, user: Annotated[User, Depends(require_roles("officer", "admin"))]):
    complaint = load_complaint(db, complaint_id)
    complaint.assigned_officer_id = user.id if user.role == "officer" else complaint.assigned_officer_id or user.id
    add_history(db, complaint, user, "ASSIGNED", "Complaint accepted and assigned")
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.post("/officer/complaints/{complaint_id}/start", response_model=ComplaintOut)
def start_complaint(complaint_id: int, db: DB, user: Annotated[User, Depends(require_roles("officer", "admin"))]):
    complaint = load_complaint(db, complaint_id)
    if user.role == "officer" and complaint.assigned_officer_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Complaint is assigned to another officer")
    complaint.assigned_officer_id = user.id if user.role == "officer" else complaint.assigned_officer_id
    add_history(db, complaint, user, "IN_PROGRESS", "Work started")
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.post("/officer/complaints/{complaint_id}/resolve", response_model=ComplaintOut)
def resolve_complaint(complaint_id: int, db: DB, user: Annotated[User, Depends(require_roles("officer", "admin"))]):
    complaint = load_complaint(db, complaint_id)
    if user.role == "officer" and complaint.assigned_officer_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Complaint is assigned to another officer")
    complaint.assigned_officer_id = user.id if user.role == "officer" else complaint.assigned_officer_id
    add_history(db, complaint, user, "AWAITING_CITIZEN_VERIFICATION", "Resolution submitted for citizen verification")
    notify_user(
        db,
        complaint.citizen_id,
        "Your complaint is resolved",
        f"Thanks for reporting \"{complaint.title}\" ({complaint.complaint_number}) — it's been marked as fixed. Tap to check it.",
        type_="resolution",
        complaint_id=complaint.id,
    )
    db.commit()
    return serialize_complaint(load_complaint(db, complaint.id))


@router.get("/admin/dashboard", response_model=DashboardOut)
def admin_dashboard(db: DB, user: Annotated[User, Depends(require_roles("admin"))]):
    def count(*conditions):
        return db.scalar(select(func.count(Complaint.id)).where(*conditions)) or 0

    total = count()
    pending = count(Complaint.status.in_(["SUBMITTED", "PENDING_REVIEW", "ASSIGNED"]))
    in_progress = count(Complaint.status.in_(["ACKNOWLEDGED", "IN_PROGRESS", "RESOLUTION_SUBMITTED", "AWAITING_CITIZEN_VERIFICATION"]))
    critical = count(Complaint.severity == "CRITICAL")
    resolved = count(Complaint.status == "RESOLVED")
    overdue = count(Complaint.status.in_(OPEN_STATUSES), Complaint.sla_escalated_at.is_not(None))
    return DashboardOut(total=total, pending=pending, in_progress=in_progress, critical=critical, resolved=resolved, overdue=overdue)


@router.get("/admin/officers", response_model=list[UserOut])
def admin_officers(db: DB, user: Annotated[User, Depends(require_roles("admin"))]):
    return db.scalars(select(User).where(User.role == "officer").order_by(User.name)).all()


@router.get("/push/vapid-public-key")
def vapid_public_key():
    return {"key": get_settings().vapid_public_key}


@router.post("/notifications/subscribe", status_code=204)
def subscribe_push(payload: PushSubscribeRequest, db: DB, user: Annotated[User, Depends(current_user)]):
    existing = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint))
    if existing:
        existing.user_id = user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
    else:
        db.add(PushSubscription(user_id=user.id, endpoint=payload.endpoint, p256dh=payload.keys.p256dh, auth=payload.keys.auth))
    db.commit()


@router.post("/notifications/unsubscribe", status_code=204)
def unsubscribe_push(payload: dict, db: DB, user: Annotated[User, Depends(current_user)]):
    endpoint = payload.get("endpoint")
    sub = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint, PushSubscription.user_id == user.id))
    if sub:
        db.delete(sub)
        db.commit()


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(db: DB, user: Annotated[User, Depends(current_user)]):
    return db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)).all()


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, db: DB, user: Annotated[User, Depends(current_user)]):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return notification
