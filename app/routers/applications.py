from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy import func
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import AddApplicationRequest, InterviewDateRequest, RecentApplicationResponse, StatsResponse, UpdateApplicationRequest
from app.utils.time_ago import time_ago
from app.utils.interview import make_ics, parse_local_datetime, resolve_to_iana, schedule_reminders_for_application
from app.utils.utils import get_current_user, send_mail


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
        user_id=current_user.id,
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
    return {"data": applications}

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
    
    return {"data": application}

# @router.put("/my-applications/{application_id}",)
# def update_application(
#     application_id: int,
#     application_data: UpdateApplicationRequest,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     application = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
#     next_action = None
#     if application_data.status == "Interview":
#         next_action = "Set interview date."
#     if not application:
#         raise HTTPException(status_code=404, detail="No Application to update")
#     application.job_title = application_data.job_title or application.job_title
#     application.company = application_data.company or application.company
#     application.status = application_data.status or application.status
#     application.applied_date = application_data.applied_date or application.applied_date
#     application.notes = application_data.notes or application.notes
#     application.job_description = application_data.job_description or application.job_description
#     application.job_link = application_data.job_link or application.job_link
#     db.commit()
#     db.refresh(application)
#     return {
#         "message": "Application updated successfully",
#         "application": application,
#         "next_action": next_action
#     }


@router.patch("/my-applications/{application_id}")
def update_application(
    application_id: int,
    application_data: UpdateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    application = (
        db.query(models.Application)
        .filter(
            models.Application.id == application_id,
            models.Application.user_id == current_user.id
        )
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="No Application to update")

    update_data = application_data.dict(exclude_unset=True)  # <-- only changed fields

    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    next_action = None
    if update_data.get("status") == "Interview":
        next_action = "Set interview date."

    return {
        "message": "Application updated successfully",
        "application": application,
        "next_action": next_action,
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

@router.post("/applications/{id}/set-interview")
def set_interview_date(
    id: int,
    request: InterviewDateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    application = db.query(models.Application).filter(
        models.Application.id == id,
        models.Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != models.ApplicationStatus.interview:
        raise HTTPException(status_code=400, detail="Cannot set interview date unless status is 'interview'")
    
    # 2) Resolve recruiter timezone (either short code like 'EDT' or an IANA string)
    try:
        recruiter_iana = resolve_to_iana(request.timezone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))   
    
        
    # 3) Parse date/time in recruiter tz and convert to UTC    
    try:
        local_dt = parse_local_datetime(request.interview_date, recruiter_iana) 
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {e}") 
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    
    application.interview_date_utc = utc_dt
    application.interview_timezone = recruiter_iana
    db.commit()
    db.refresh(application)
    
    # 5) Compose display datetime in user's timezone
    user_iana = current_user.timezone or "UTC"
    user_local_dt = utc_dt.astimezone(ZoneInfo(user_iana))
    pretty = user_local_dt.strftime("%A, %B %d, %Y at %I:%M %p %Z")

    # 6) Create ICS and send immediate confirmation email (attach ICS)
    ics_bytes = make_ics(application, local_dt, recruiter_iana, duration_minutes=60)
    subject = "Interview Scheduled"
    body = f"""Hello {current_user.username},
    Your interview for {application.job_title} at {application.company} is scheduled on:
        📅 {pretty}

        An invite is attached (you can add it to Google/Apple/Outlook).

    Good luck!
    """
    
    # Here show how your send_mail should accept attachments: adjust to your helper's signature
    try:
        send_mail(subject=subject, body=body, to_email=current_user.email,
                attachments=[("invite.ics", ics_bytes, "text/calendar")])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")    
    
    
     # 7) Schedule reminders (scheduler runs in UTC)
    schedule_reminders_for_application(application, utc_dt, user_iana)
    
    return {
        "message": "Interview date set successfully. Confirmation email (with .ics) sent.",
        "application": {
            "id": application.id,
            "job_title": application.job_title,
            "company": application.company,
            "interview_date_utc": utc_dt.isoformat(),
            "interview_timezone": application.interview_timezone,
            "display_time_user_tz": pretty
        }
    }
    
    
@router.get("/search-applications")   
def search_applications(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not query.strip():
        return []
    results = db.query(models.Application).filter(
        models.Application.user_id == current_user.id,
        (models.Application.job_title.ilike(f"%{query}%")) | 
        (models.Application.company.ilike(f"%{query}%")) | 
        (models.Application.notes.ilike(f"%{query}%"))
    ).all()
    
    return {"results": results}

@router.get("/stats", response_model=StatsResponse)
def all_applications_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    results = (
        db.query(models.Application.status, func.count(models.Application.id))
        .filter(models.Application.user_id == current_user.id)
        .group_by(models.Application.status)
        .all()
    )
    
    stats = {status.value: count for status, count in results}
    
    
    return{
        
            "data":{
                "applied": stats.get("Applied", 0),
                "interview": stats.get("Interview", 0),
                "offer": stats.get("Offer", 0),
                "rejected": stats.get("Rejected", 0),
            } 
        
    }
    
    
@router.get("/recent",  response_model=list[RecentApplicationResponse])
def recent_appication(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 5,
):
    
    applications = (
        db.query(models.Application)
        .filter(models.Application.user_id == current_user.id)
        .order_by(models.Application.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return[
        RecentApplicationResponse(
            id=app.id,
            job_title=app.job_title,
            company_name=app.company,
            status=app.status.value,  
            time_ago=time_ago(app.created_at),
        )
        for app in applications
    ]
    
    