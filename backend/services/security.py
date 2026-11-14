import hashlib
import secrets

from sqlalchemy import select

from database import SessionLocal
from models import User


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return salt + ":" + h.hex()


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":")
    except ValueError:
        return False
    h2 = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return secrets.compare_digest(h2.hex(), h)


def create_token() -> str:
    return secrets.token_hex(32)


def get_user_by_token(token: str):
    with SessionLocal() as db:
        return db.execute(select(User).where(User.token == token)).scalar()