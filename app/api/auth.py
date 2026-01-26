from fastapi import APIRouter, Depends, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, get_current_user
from app.models.user import User
from datetime import datetime

from fastapi.responses import RedirectResponse
import urllib.parse

router = APIRouter()
settings = get_settings()

@router.post("/token")
async def google_token_exchange(id_token_str: str):
    """
    Exchange a Google ID Token for internal Access and Refresh tokens.
    Strictly restricted to @hikigai.ai emails.
    """
    try:
        # Verify the ID token from Google
        id_info = id_token.verify_oauth2_token(
            id_token_str, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google token")
            
        # Domain restriction
        if not email.endswith(f"@{settings.ALLOWED_DOMAIN}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Access denied. Only @{settings.ALLOWED_DOMAIN} accounts allowed."
            )
            
        # Find or create user
        user = await User.find_one(User.email == email)
        if not user:
            user = User(
                email=email,
                full_name=id_info.get("name"),
                picture=id_info.get("picture"),
                last_login=datetime.utcnow()
            )
            await user.insert()
        else:
            user.last_login = datetime.utcnow()
            await user.save()
            
        # Create internal tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "name": user.full_name,
                "picture": user.picture
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

@router.post("/refresh")
async def refresh_access_token(token: str):
    """Refreshes an access token using a valid refresh token"""
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
        new_access_token = create_access_token(data={"sub": email})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Log out the current user.
    Updates last_logout timestamp to revoke all existing tokens.
    """
    current_user.last_logout = datetime.utcnow()
    await current_user.save()
    return {"message": "Successfully logged out. All existing tokens have been revoked."}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get profile of currently logged in user"""
    return current_user
