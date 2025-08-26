from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import AddApplicationRequest, UpdateApplicationRequest
from app.utils import get_current_user


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


    
    
@router.post("/add-new-application")
def add_new_application(
  application_data: AddApplicationRequest,  
  db: Session = Depends(get_db),
  current_user: models.User = Depends(get_current_user)
):
    new_application = models.Application(
        job_title=application_data.job_title,
        company=application_data.company,
        status=application_data.status,
        applied_date=application_data.applied_date or datetime.utcnow(),
        notes=application_data.notes,
        job_description=application_data.job_description,
        job_link=application_data.job_link,
        user_id=current_user.id
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return {
        "message": "Application added successfully",
        "application": new_application
    }
    
@router.get("/my-applications")
def list_user_applications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    applications = db.query(models.Application).filter(models.Application.user_id == current_user.id).all()
    if not applications:
        return {"message": "You have no applications."}
    return {"applications": applications}

@router.get("/my-applications/{application_id}")
def get_application_details(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    application = db.query(models.Application).filter(
        models.Application.id == application_id,
        models.Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"application": application}

@router.put("/my-applications/{application_id}",)
def update_application(
    application_id: int,
    application_data: UpdateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    application = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not application:
        raise HTTPException(status_code=404, detail="No Application to update")
    application.job_title = application_data.job_title or application.job_title
    application.company = application_data.company or application.company
    application.status = application_data.status or application.status
    application.applied_date = application_data.applied_date or application.applied_date
    application.notes = application_data.notes or application.notes
    application.job_description = application_data.job_description or application.job_description
    application.job_link = application_data.job_link or application.job_link
    db.commit()
    db.refresh(application)
    return {
        "message": "Application updated successfully",
        "application": application
    }

@router.delete("/my-applications/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    application = db.query(models.Application).filter(
        models.Application.id == application_id,
        models.Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted successfully"}