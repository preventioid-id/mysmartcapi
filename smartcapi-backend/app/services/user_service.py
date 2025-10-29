# smartcapi-backend/app/services/user_service.py

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
import secrets

from ..core import config
from ..model.tables import User, PasswordResetToken, UserRole
from ..schemas.auth import UserCreate

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None

class UserService:
    """Service for user management and authentication."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create_user(self, user: UserCreate) -> User:
        if self.get_user_by_username(user.username):
            raise ValueError(f"Username '{user.username}' already exists")
        if self.get_user_by_email(user.email):
            raise ValueError(f"Email '{user.email}' already exists")

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user or not verify_password(password, user.password):
            return None
        return user

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        allowed_fields = ['email', 'full_name', 'phone', 'role', 'voice_sample_path']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True

    def create_password_reset_token(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        
        reset_token_obj = self.db.query(PasswordResetToken).filter_by(user_id=user.id).first()
        if reset_token_obj:
            reset_token_obj.token = token
            reset_token_obj.expires_at = expires
        else:
            reset_token_obj = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires
            )
            self.db.add(reset_token_obj)
            
        self.db.commit()
        return token

    def get_user_by_password_reset_token(self, token: str) -> Optional[User]:
        reset_token_obj = self.db.query(PasswordResetToken).filter_by(token=token).first()
        if not reset_token_obj or reset_token_obj.expires_at < datetime.utcnow():
            return None
        return reset_token_obj.user

    def reset_password(self, user: User, new_password: str) -> bool:
        user.password = get_password_hash(new_password)
        
        # Delete the reset token after use
        reset_token_obj = self.db.query(PasswordResetToken).filter_by(user_id=user.id).first()
        if reset_token_obj:
            self.db.delete(reset_token_obj)
            
        self.db.commit()
        return True


def get_current_user(db: Session, token: str) -> Optional[User]:
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        return None
    username = payload["sub"]
    user_service = UserService(db)
    return user_service.get_user_by_username(username)
