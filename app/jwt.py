from datetime import datetime, timedelta
from jose import jwt


from dotenv import load_dotenv

load_dotenv()
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

to_encode = {
    "sub": "1",
    "exp": datetime.utcnow() + timedelta(hours=24),
}

token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
print(token)
