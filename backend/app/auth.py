from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from .config import settings
from .db import Session
from .models import User
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_NAME = "access_token"

class Creds(BaseModel):
    email: EmailStr
    password: str

def create_token(uid: int):
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    return jwt.encode({"sub": str(uid), "exp": exp}, settings.JWT_SECRET, algorithm="HS256")

async def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401)
    uid = int(payload["sub"])
    async with Session() as s:
        user = (await s.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        if not user: raise HTTPException(401)
        return user

@router.post("/register")
async def register(creds: Creds):
    async with Session() as s:
        if (await s.execute(select(User).where(User.email == creds.email))).scalar_one_or_none():
            raise HTTPException(400, "email taken")
        u = User(email=creds.email, password_hash=bcrypt.hash(creds.password))
        s.add(u); await s.commit()
    return {"ok": True}

@router.post("/login")
async def login(creds: Creds, resp: Response):
    async with Session() as s:
        u = (await s.execute(select(User).where(User.email == creds.email))).scalar_one_or_none()
        if not u or not bcrypt.verify(creds.password, u.password_hash):
            raise HTTPException(401, "bad creds")
    token = create_token(u.id)
    resp.set_cookie(COOKIE_NAME, token, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", max_age=60*settings.JWT_EXPIRES_MIN)
    return {"ok": True}

@router.post("/logout")
async def logout(resp: Response):
    resp.delete_cookie(COOKIE_NAME)
    return {"ok": True}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "map_state": user.map_state}

@router.put("/me/map-state")
async def save_map_state(state: dict, user: User = Depends(get_current_user)):
    async with Session() as s:
        dbu = await s.get(User, user.id)
        dbu.map_state = state
        await s.commit()
    return {"ok": True}
