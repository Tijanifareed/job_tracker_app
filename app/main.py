from fastapi import FastAPI
from app.routers import applications, auth, resume
from app.database import SessionLocal
from app.routers.auth import cleanup_expired_reset_codes
from apscheduler.schedulers.background import BackgroundScheduler

def scheduled_cleanup():
    db = SessionLocal()
    cleanup_expired_reset_codes(db)
    db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_cleanup, "interval", minutes=10)  # Runs every 10 minutes
scheduler.start()

app = FastAPI(title="Job Tracker API")
app.include_router(applications.router)
app.include_router(resume.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to Job Tracker API 🚀"}

