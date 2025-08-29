from fastapi import FastAPI
from app.routers import applications, auth, resume
from app.database import SessionLocal
from app.routers.auth import cleanup_expired_reset_codes
from app.utils.scheduler import start_scheduler, scheduler

def scheduled_cleanup():
    db = SessionLocal()
    cleanup_expired_reset_codes(db)
    db.close()


app = FastAPI(title="Job Tracker API")
app.include_router(applications.router)
app.include_router(resume.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to Job Tracker API 🚀"}

@app.on_event("startup")
def _startup():
    start_scheduler()
    scheduler.add_job(scheduled_cleanup, "interval", minutes=10)  # Runs every 10 minutes



@app.on_event("shutdown")
def _shutdown():
    scheduler.shutdown(wait=False)