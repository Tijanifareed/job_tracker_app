import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import ForgotPasswordRequest, UserCreate, UserLogin
from passlib.hash import bcrypt
from app.utils import create_access_token, genarate_reset_token, get_current_user, send_mail


router = APIRouter(prefix="/applications", tags=["Applications"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_applications(db: Session = Depends(get_db)):
    return db.query(models.Application).all()



@router.post("/auth/create-account")
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
    
    
@router.post("/auth/login-app")
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


@router.get("/auth/me")
def return_me(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}. You are authenticated!"}


reset_code_cache = {}
@router.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    code = genarate_reset_token()
    reset_code_cache[request.email] = code
    send_mail(
        "Password Reset Code",
        f"Your password reset code is: {code}",
        request.email,
        
    )
    return {
        "message": "Reset code sent to your email",
        "code": code  # For testing purposes only; remove in production
        }
    
