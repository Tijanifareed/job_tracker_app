from pydantic import BaseModel, EmailStr
class UserCreate(BaseModel):
     username: str
     email: EmailStr
     password: str
     
     
class UserLogin(BaseModel):
    email: EmailStr
    password: str     
    
class AddApplication(BaseModel):
    job_title: str
    company: str
    status: str = "Applied"
    notes: str | None = None
    job_description: str | None = None
    job_link: str | None = None   
     
     
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str   