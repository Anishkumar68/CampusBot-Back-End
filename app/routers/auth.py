from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User
from database import get_db
from services.auth import get_password_hash, verify_password, create_access_token
from datetime import datetime, timedelta

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(data.password)
    new_user = User(
        email=data.email,
        full_name=data.full_name,
        is_premium=False,
        has_free_pdf_access=False,
        created_at=datetime.utcnow(),
    )
    new_user.hashed_password = hashed_password  # Add this field in model
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": user.id}, expires_delta=timedelta(minutes=60)
    )
    return {"access_token": token, "token_type": "bearer"}
