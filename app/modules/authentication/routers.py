from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt
from app.core.db import SessionLocal
from app.modules.authentication.models import User
from app.modules.authentication.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")
    hashed_pw = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
    user = User(
        email=user_data.email,
        password=hashed_pw.decode("utf-8"),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# Otros endpoints (update, delete) se pueden agregar de forma similar
