"""Create or reset one protected officer/admin account.

Run this manually from the backend directory. It prompts for the password so
credentials are never committed to the repository or placed in shell history.
"""

from getpass import getpass
from pathlib import Path
import sys

from sqlalchemy import select

# Allow this file to be run directly with: python scripts/create_role_user.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402


ALLOWED_ROLES = {"officer", "admin"}


def main() -> None:
    role = input("Role (officer/admin): ").strip().lower()
    if role not in ALLOWED_ROLES:
        raise SystemExit("Role must be officer or admin.")

    name = input("Full name: ").strip()
    email = input("Official email: ").strip().lower()
    password = getpass("Password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if not name or "@" not in email:
        raise SystemExit("Enter a valid name and email.")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.name = name
            user.password_hash = hash_password(password)
            user.role = role
            user.is_active = True
            action = "updated"
        else:
            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                )
            )
            action = "created"
        db.commit()
        print(f"Successfully {action} {role} account: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
