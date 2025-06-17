from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
EXPIRES_IN_HOURS = int(os.getenv("EXPIRES_IN_HOURS", 24))


def generate_jwt(user_id: str, expires_in_hours: int = EXPIRES_IN_HOURS):
    to_encode = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token
