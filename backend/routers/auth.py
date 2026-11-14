from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from deps import get_db, get_current_user
from models import User
from services import security

router = APIRouter()


def user_public(u: User):
    return {"id": u.id, "username": u.username, "name": u.name}


class RegisterReq(BaseModel):
    username: str
    password: str


class LoginReq(BaseModel):
    username: str
    password: str


class ChangePasswordReq(BaseModel):
    old_password: str
    new_password: str


@router.post("/auth/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    if len(req.username) < 3 or len(req.password) < 6:
        raise HTTPException(400, "用户名至少3位，密码至少6位")
    if db.execute(select(User).where(User.username == req.username)).scalar():
        raise HTTPException(400, "用户名已存在")
    user = User(username=req.username, password_hash=security.hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = security.create_token()
    user.token = token
    db.commit()
    return {"token": token, "user": user_public(user)}


@router.post("/auth/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == req.username)).scalar()
    if not user or not security.verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = security.create_token()
    user.token = token
    db.commit()
    return {"token": token, "user": user_public(user)}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_public(user)


@router.post("/auth/change-password")
def change_password(req: ChangePasswordReq, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not security.verify_password(req.old_password, user.password_hash):
        raise HTTPException(400, "原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(400, "新密码至少6位")
    user.password_hash = security.hash_password(req.new_password)
    db.commit()
    return {"ok": True}


@router.post("/auth/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token = None
    db.commit()
    return {"ok": True}