from contextlib import asynccontextmanager
from collections import defaultdict, deque
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .api.v1 import router
from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import Category, Department, User
from .scheduler import start_scheduler


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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), geolocation=(self), microphone=()"
        if settings.environment.lower() in {"production", "prod"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
                "form-action 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https://*.tile.openstreetmap.org; "
                "connect-src 'self' https://nominatim.openstreetmap.org; worker-src 'self' blob:"
            )
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    WINDOW_SECONDS = 300
    LIMITS = {
        "/api/v1/auth/login": 10,
        "/api/v1/auth/register": 5,
    }

    def __init__(self, app):
        super().__init__(app)
        self.attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        limit = self.LIMITS.get(request.url.path) if request.method == "POST" else None
        if not limit:
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, request.url.path)
        now = monotonic()
        bucket = self.attempts[key]
        while bucket and now - bucket[0] > self.WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many authentication attempts. Try again later."},
                headers={"Retry-After": str(self.WINDOW_SECONDS)},
            )
        bucket.append(now)
        return await call_next(request)


def seed_data() -> None:
    db = SessionLocal()
    try:
        for name, description in DEFAULT_DEPARTMENTS:
            if not db.scalar(select(Department).where(Department.name == name)):
                db.add(Department(name=name, description=description))
        for name, sla in DEFAULT_CATEGORIES:
            if not db.scalar(select(Category).where(Category.name == name)):
                db.add(Category(name=name, default_sla_hours=sla, description=f"{name} complaints"))
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
production = settings.environment.lower() in {"production", "prod"}
allowed_origins = [settings.frontend_origin]
if not production:
    allowed_origins.extend(["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"])
allowed_hosts = []
if not production:
    allowed_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0"])
frontend_host = urlparse(settings.frontend_origin).hostname
if frontend_host:
    allowed_hosts.append(frontend_host)
allowed_hosts.extend(
    host.strip().lower()
    for host in settings.trusted_hosts.split(",")
    if host.strip()
)
if production:
    allowed_hosts.append("*.onrender.com")

app = FastAPI(
    title="CivicConnect API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=sorted(set(allowed_hosts)))
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=sorted(set(allowed_origins)), allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
uploads_dir = Path(settings.uploads_dir).resolve()
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir, check_dir=False), name="uploads")
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "service": "civicconnect-api", "database": engine.dialect.name}


# In the Render monolith, FastAPI serves the compiled React app from the same
# origin. This must be registered after the API and health routes.
frontend_dist = Path(settings.frontend_dist_dir or (Path(__file__).resolve().parents[2] / "frontend" / "dist")).resolve()

if frontend_dist.is_dir():
    frontend_assets = frontend_dist / "assets"
    if frontend_assets.is_dir():
        app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Keep browsers that request the conventional .ico path happy."""
        favicon_path = frontend_dist / "favicon.svg"
        if favicon_path.is_file():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Favicon not found")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        if production and full_path.rstrip("/") in {"docs", "redoc", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not found")
        requested_path = (frontend_dist / full_path).resolve()
        if frontend_dist not in requested_path.parents and requested_path != frontend_dist:
            raise HTTPException(status_code=404, detail="Not found")
        if requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(frontend_dist / "index.html")
