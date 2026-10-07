import httpx

from .config import get_settings


class StorageNotConfigured(Exception):
    pass


def _require_settings():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise StorageNotConfigured("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set to use Supabase storage")
    return settings


def _headers(settings) -> dict:
    return {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }


def ensure_bucket() -> None:
    """Create the private complaint-images bucket if it doesn't already exist. Safe to call repeatedly."""
    settings = _require_settings()
    base = settings.supabase_url.rstrip("/")
    bucket = settings.supabase_storage_bucket
    with httpx.Client(timeout=10) as client:
        existing = client.get(f"{base}/storage/v1/bucket/{bucket}", headers=_headers(settings))
        if existing.status_code == 200:
            return
        response = client.post(
            f"{base}/storage/v1/bucket",
            headers=_headers(settings),
            json={"id": bucket, "name": bucket, "public": False},
        )
        if response.status_code not in (200, 201) and "already exists" not in response.text.lower():
            response.raise_for_status()


def upload_image(content: bytes, content_type: str, path: str) -> str:
    """Uploads bytes to the private bucket and returns the storage object path (not a public URL)."""
    settings = _require_settings()
    base = settings.supabase_url.rstrip("/")
    bucket = settings.supabase_storage_bucket
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{base}/storage/v1/object/{bucket}/{path}",
            headers={**_headers(settings), "Content-Type": content_type},
            content=content,
        )
        response.raise_for_status()
    return path


def get_signed_url(path: str, expires_in: int = 300) -> str:
    """Returns a time-limited URL for a private object. expires_in is in seconds."""
    settings = _require_settings()
    base = settings.supabase_url.rstrip("/")
    bucket = settings.supabase_storage_bucket
    with httpx.Client(timeout=10) as client:
        response = client.post(
            f"{base}/storage/v1/object/sign/{bucket}/{path}",
            headers=_headers(settings),
            json={"expiresIn": expires_in},
        )
        response.raise_for_status()
        signed_path = response.json()["signedURL"]
    return f"{base}/storage/v1{signed_path}"
