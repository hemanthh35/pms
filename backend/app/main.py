from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

from .api.v1 import router
from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import Category, Department, User
from .scheduler import start_scheduler
from .security import hash_password


DEFAULT_DEPARTMENTS = [
    ("Roads & Infrastructure", "Roads, footpaths, potholes and public structures"),
    ("Sanitation", "Garbage collection and illegal dumping"),
    ("Water Works", "Water leakage, drainage and waterlogging"),
    ("Electrical Services", "Streetlights and exposed electrical infrastructure"),
    ("Traffic & Transport", "Signals and traffic infrastructure"),
    ("Parks & Emergency Services", "Fallen trees and urgent public safety response"),
    ("General Civic Services", "General civic complaints"),
]
DEFAULT_CATEGORIES = [
    ("Road Damage", 24), ("Pothole", 12), ("Garbage", 12), ("Illegal Dumping", 12),
    ("Water Leakage", 12), ("Drainage", 24), ("Streetlight", 48), ("Traffic Signal", 12),
    ("Broken Footpath", 48), ("Fallen Tree", 4), ("Waterlogging", 12),
    ("Public Infrastructure Damage", 48), ("Open Manhole", 4), ("Other", 72),
]


def seed_data() -> None:
    db = SessionLocal()
    try:
        for name, description in DEFAULT_DEPARTMENTS:
            if not db.scalar(select(Department).where(Department.name == name)):
                db.add(Department(name=name, description=description))
        for name, sla in DEFAULT_CATEGORIES:
            if not db.scalar(select(Category).where(Category.name == name)):
                db.add(Category(name=name, default_sla_hours=sla, description=f"{name} complaints"))
        demo_users = [
            ("Demo Citizen", "citizen@civicconnect.app", "citizen123", "citizen"),
            ("Ravi Kumar", "officer@civicconnect.app", "officer123", "officer"),
            ("System Admin", "admin@civicconnect.app", "admin123", "admin"),
        ]
        for name, email, password, role in demo_users:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(name=name, email=email, password_hash=hash_password(password), role=role))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_data()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(title="CivicConnect API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
uploads_dir = Path(settings.uploads_dir).resolve()
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir, check_dir=False), name="uploads")
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "service": "civicconnect-api"}


# In the Render monolith, FastAPI serves the compiled React app from the same
# origin. This must be registered after the API and health routes.
frontend_dist = Path(settings.frontend_dist_dir or (Path(__file__).resolve().parents[2] / "frontend" / "dist")).resolve()

if frontend_dist.is_dir():
    frontend_assets = frontend_dist / "assets"
    if frontend_assets.is_dir():
        app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        requested_path = (frontend_dist / full_path).resolve()
        if frontend_dist not in requested_path.parents and requested_path != frontend_dist:
            raise HTTPException(status_code=404, detail="Not found")
        if requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(frontend_dist / "index.html")
