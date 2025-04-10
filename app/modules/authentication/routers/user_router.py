from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.authentication.models.user import User
from app.modules.authentication.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import verify_user_access, get_admin_user, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")
    
    try:
        with db.begin_nested():
            hashed_pw = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
            user = User(
                email=user_data.email,
                password=hashed_pw.decode("utf-8"),
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role,
                active=True
            )
            db.add(user)
            db.flush()
        db.commit()
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/users", response_model=PagedResponse[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user)
):
    query = db.query(User).filter(User.active == True)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            User.email.ilike(search_term) | 
            User.first_name.ilike(search_term) | 
            User.last_name.ilike(search_term)
        )
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, UserResponse)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_user_access())
):
    user = db.query(User).filter(
        and_(User.id == user_id, User.active == True)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return user

@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_user_access())
):
    user = db.query(User).filter(
        and_(User.id == user_id, User.active == True)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "email" in update_data and update_data["email"] != user.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists.")
    
    if "password" in update_data and update_data["password"]:
        hashed_pw = bcrypt.hashpw(update_data["password"].encode("utf-8"), bcrypt.gensalt())
        update_data["password"] = hashed_pw.decode("utf-8")
    
    try:
        with db.begin_nested():
            for key, value in update_data.items():
                setattr(user, key, value)
            db.flush()
        db.commit()
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_user_access())
):
    user = db.query(User).filter(
        and_(User.id == user_id, User.active == True)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    try:
        with db.begin_nested():
            user.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@router.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/users/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "email" in update_data and update_data["email"] != current_user.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists.")
    
    if "password" in update_data and update_data["password"]:
        hashed_pw = bcrypt.hashpw(update_data["password"].encode("utf-8"), bcrypt.gensalt())
        update_data["password"] = hashed_pw.decode("utf-8")
    
    try:
        with db.begin_nested():
            for key, value in update_data.items():
                setattr(current_user, key, value)
            db.flush()
        db.commit()
        return current_user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")