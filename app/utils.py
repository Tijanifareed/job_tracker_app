import os
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/applications/login-app")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
     to_encode = data.copy()
     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
     to_encode.update({"exp": expire})
     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
     try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          email: str = payload.get("sub")
          if email is None:
               raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Could not validate credentials",
               )
          return email
     
     except JWTError:
         raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED, 
              detail="Could not validate credentials",
           )   