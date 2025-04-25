from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import get_db
from models import User
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends

# .env file should contain the secret key
# and algorithm for JWT token generation
import os
from dotenv import load_dotenv

load_dotenv()


# Secret and algorithm
SECRET_KEY = os.getenv("SECRET_KEY")
# Default secret key for development; change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Hashing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ✅ Dependency: Get current user from JWT
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(*roles):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role access")
        return current_user

    return checker
