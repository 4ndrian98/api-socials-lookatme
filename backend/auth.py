import os, datetime as dt
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Query, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-please")
ALGORITHM = "HS256"
ACCESS_MIN = int(os.getenv("JWT_MINUTES", "60"))

pwdctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_password(p: str) -> str:
    return pwdctx.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return pwdctx.verify(p, hashed)

def create_access_token(sub: str) -> str:
    payload = {"sub": sub, "exp": dt.datetime.utcnow() + dt.timedelta(minutes=ACCESS_MIN)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def authenticate(db: Session, email: str, password: str) -> bool:
    u = db.query(User).filter(User.email == email).first()
    return bool(u and verify_password(password, u.password_hash))

def require_token(token: str = Query(..., description="JWT token")) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") or "unknown"
    except JWTError:
        raise HTTPException(status_code=401, detail="Token non valido")
