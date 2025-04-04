from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.db import SessionLocal
from app.modules.authentication.models.user import User
from app.modules.orders.models import Order
from app.modules.authentication.security import verify_token
import logging
from jose import JWTError, jwt
from app.core.config import settings

SECRET_KEY = settings.AUTH_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        user = db.query(User).filter(
            User.id == token_data.user_id, 
            User.active == True
        ).first()
        
        if not user:
            raise credentials_exception
            
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
    return current_user

async def get_owner_or_admin_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def verify_user_access(user_id_param: str = "user_id"):
    """
    Creates a dependency that verifies if the current user has access to the
    resources of the user specified by user_id_param.
    
    Args:
        user_id_param: The name of the path parameter containing the user ID
    """
    async def dependency(
        current_user: User = Depends(get_current_user),
        **path_params
    ):
        user_id = int(path_params[user_id_param])
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user's data"
            )
        return current_user
    
    return dependency

def verify_order_access(order_id_param: str = "order_id"):
    """
    Creates a dependency that verifies if the current user has access to the
    order specified by order_id_param.
    
    Args:
        order_id_param: The name of the path parameter containing the order ID
    """
    async def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        **path_params
    ):
        order_id = int(path_params[order_id_param])
        order = db.query(Order).filter(
            and_(Order.id == order_id, Order.active == True)
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or inactive")
        
        if current_user.id != order.user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this order"
            )
        
        return order
    
    return dependency