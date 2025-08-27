from fastapi import APIRouter, Depends
from app import database
from app.schemas import ForgotPasswordRequest, TimeZoneRequest
from app.timezones import TimezoneEnum
from app.utils import get_current_user, send_mail
from datetime import datetime, timedelta
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import ForgotPasswordRequest, ResetPasswordRequest, UserCreate, UserLogin
from passlib.hash import bcrypt
from app.utils import create_access_token, genarate_reset_token, get_current_user, send_mail

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


@router.post("/create-account")
def create_account(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = bcrypt.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "message": "User created successfully",
        "data":{
            "user_id": db_user.id,
            "username": db_user.username,
            "email": db_user.email
        }
        }
    
    
@router.post("/login-app")
def login_app(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user.email})
    return {
        "data":{
            "access_token": access_token,
            "token_type": "bearer"
        }
       }


@router.get("/me")
def return_me(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}. You are authenticated!"}


reset_code_cache = {}
@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    code = genarate_reset_token()
    reset_entry = models.PasswordReset(
        user_id=db_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(reset_entry)
    db.commit()
    send_mail(
        "Password Reset Code",
        f"Your password reset code is: {code}",
        request.email,
    )
    return {
        "message": "Reset code sent to your email",
        "code": code  # For testing purposes only; remove in production
        }
    

@router.post("/verify-reset-code")
def verify_reset_code(token: str, email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    reset_entry = db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == db_user.id,
        models.PasswordReset.code == token,
        models.PasswordReset.expires_at > datetime.utcnow()
    ).first()
    if not reset_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    # Delete The reset code after successful verification
    db.delete(reset_entry)
    db.commit()
    return {"message": "Reset code verified successfully. You can now reset your password."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    hashed_password = bcrypt.hash(request.new_password)
    db_user.password_hash = hashed_password
    db.commit()
    db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == db_user.id
    ).delete()
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/add-timezone")
def add_timezone(timezone_request: TimeZoneRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tz_value = TimezoneEnum[timezone_request.timezone].value
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid timezone provided")
    current_user.timezone = tz_value
    db.commit()
   
    return {
        "message": "Timezone added successfully",
        "timezone": timezone_request.timezone
    }
    

def cleanup_expired_reset_codes(db: Session):
    db.query(models.PasswordReset).filter(
        models.PasswordReset.expires_at < datetime.utcnow()
    ).delete()
    db.commit()        
