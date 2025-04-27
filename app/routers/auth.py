from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User
from database import get_db
from services.auth import get_password_hash, verify_password, create_access_token
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


# 📦 DTOs (Schemas)
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# 📦 Routes
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(data.password)
    new_user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hashed_password,
        is_premium=False,
        has_free_pdf_access=False,
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=15),  # Access token: 15 mins
    )

    refresh_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=7),  # Refresh token: 7 days
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/auth/token")  # ✅ Better route
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=15),  # Access token valid 15 min
    )

    refresh_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=7),  # Refresh token valid 7 days
    )
    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)
    # Return both tokens
    # as part of the response

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# 📦 New Route: Refresh Token
@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest):
    from services.auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token(
            data={"sub": str(user_id)}, expires_delta=timedelta(minutes=15)
        )

        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
