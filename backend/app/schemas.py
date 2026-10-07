import re
from datetime import datetime
from typing import Optional

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str


class AdminUserOut(UserOut):
    is_active: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: Literal["citizen", "officer", "admin"]
    is_active: bool


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(AuthRequest):
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: str = "citizen"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LocationInput(BaseModel):
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    accuracy: Optional[float] = Field(default=None, ge=0)
    address: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    ward: Optional[str] = None


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=2)
    category: str = "Other"
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    image_url: Optional[str] = None
    location: Optional[LocationInput] = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"complaints/\d+/[0-9a-f]{32}\.(jpg|png|webp)", value):
            raise ValueError("Images must be uploaded through the upload endpoint")
        return value


class ComplaintUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=160)
    description: Optional[str] = Field(default=None, min_length=2)
    category: Optional[str] = None
    severity: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None
    status: Optional[Literal["SUBMITTED", "PENDING_REVIEW", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLUTION_SUBMITTED", "AWAITING_CITIZEN_VERIFICATION", "RESOLVED", "REOPENED"]] = None
    comment: Optional[str] = None


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: Optional[str]
    new_status: str
    comment: Optional[str]
    created_at: datetime


class ComplaintOut(BaseModel):
    id: int
    complaint_number: str
    title: str
    description: str
    category: Optional[str]
    severity: str
    status: str
    image_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]
    city: Optional[str]
    area: Optional[str]
    ward: Optional[str]
    department: Optional[str]
    citizen_name: Optional[str]
    assigned_officer: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    history: list[HistoryOut] = Field(default_factory=list)


class DashboardOut(BaseModel):
    total: int
    pending: int
    in_progress: int
    critical: int
    resolved: int
    overdue: int = 0


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushKeys


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: Optional[int]
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime


class ImageUrlOut(BaseModel):
    url: str
