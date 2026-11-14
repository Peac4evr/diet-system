from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    user = db.execute(select(User).where(User.token == authorization[7:])).scalar()
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return user