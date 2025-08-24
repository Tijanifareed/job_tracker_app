from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, database

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
