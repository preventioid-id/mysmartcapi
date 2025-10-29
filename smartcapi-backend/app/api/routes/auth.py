# c:\xampp\htdocs\smartcapi_pwa\smartcapi-backend\app\api\routes\auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ...schemas import auth as auth_schema
from ...services.user_service import UserService, get_password_hash, create_access_token, verify_password
from ...services.db import get_db
from ...core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from ...model.tables import User

router = APIRouter()

@router.post("/register", response_model=auth_schema.UserResponse)
def register_user(user: auth_schema.UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    try:
        created_user = user_service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return created_user

@router.post("/token", response_model=auth_schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/password/forgot")
def forgot_password(request: auth_schema.PasswordResetRequest, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = user_service.create_password_reset_token(user)
    # In a real application, you would email this token to the user.
    # For now, we will return it in the response for testing.
    print(f"Password reset token for {user.email}: {token}")
    return {"message": "Password reset token generated. In a real app, this would be emailed.", "reset_token": token}

@router.post("/password/reset")
def reset_password(request: auth_schema.PasswordReset, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.get_user_by_password_reset_token(request.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user_service.reset_password(user, request.new_password)
    return {"message": "Password has been reset successfully"}

# This is a placeholder for a protected route
@router.get("/users/me", response_model=auth_schema.UserResponse)
def read_users_me(current_user: User = Depends(user_service.get_current_user)):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user