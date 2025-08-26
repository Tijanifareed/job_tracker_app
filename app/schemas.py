from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Enum

class UserCreate(BaseModel):
     username: str
     email: EmailStr
     password: str
     
     
class UserLogin(BaseModel):
    email: EmailStr
    password: str     
    
class ApplicationStatus(str, Enum):
    applied = "Applied"
    interview = "Interview"
    offer = "Offer"
    rejected = "Rejected"    
    
class AddApplicationRequest(BaseModel):
    job_title: str
    company: str
    status: str = ApplicationStatus.applied
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None
    job_link: Optional[HttpUrl] = None
    
class UpdateApplicationRequest(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None
    job_link: Optional[HttpUrl] = None    
    

     
     
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str  
    
class AddResumeRequest(BaseModel):
    title: str
    file_url: str
    public_id: str     