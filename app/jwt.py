from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "anishkumar23"
ALGORITHM = "HS256"

to_encode = {
    "sub": "1",  # Make sure it's a string if your backend expects that
    "exp": datetime.utcnow() + timedelta(minutes=60),
}

token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
print(token)
