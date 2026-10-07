from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt

from app.database import get_db
from app.models import User, ContentVerification, VerificationReport
from app.schemas import UserCreate, UserLogin, TokenResponse, VerificationInput, VerificationResponse
from app.services.auth import create_access_token, hash_password, verify_password, decode_access_token
from app.services.verifier import build_verification_result
from app.services.analytics import call_ai_service

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=str(payload.email),
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}
