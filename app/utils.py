from email.mime.text import MIMEText
import os
import random
import smtplib
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import cloudinary
import cloudinary.uploader
from sqlalchemy.orm import Session


from app import database, models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/applications/login-app")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
     try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          email: str = payload.get("sub")
          user = db.query(models.User).filter(models.User.email == email).first()
          if not user:
               raise HTTPException(status_code=401, detail="Invalid credentials")
          return user
     
     except JWTError:
         raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED, 
              detail="Could not validate credentials",
           )   
         
    


def create_access_token(data: dict, expires_delta: timedelta = None):
     to_encode = data.copy()
     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
     to_encode.update({"exp": expire})
     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def genarate_reset_token():
     return str(random.randint(100000, 999999))


def send_mail(subject, body, to_email, ):
     msg = MIMEText(body)
     msg['Subject'] = subject
     msg['From'] = os.getenv("EMAIL_USER")
     msg['To'] = to_email
     
     # Gmail SMTP server 
     smtp_server = "smtp.gmail.com"
     smtp_port = 587
     
     with smtplib.SMTP(smtp_server, smtp_port) as server:
          server.starttls()
          server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
          server.sendmail(os.getenv("EMAIL_USER"), to_email, msg.as_string())    
          
