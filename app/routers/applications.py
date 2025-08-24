from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import UserCreate, UserLogin
from passlib.hash import bcrypt
from app.utils import create_access_token, get_current_user


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
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
        }
    
    
@router.post("/login-app")
def login_app(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me")
def return_me(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}. You are authenticated!"}