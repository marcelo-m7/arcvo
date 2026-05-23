from hmac import compare_digest

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not compare_digest(payload.password, settings.app_admin_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    token = create_access_token("admin", expires_minutes=settings.app_jwt_expires_minutes)
    return LoginResponse(access_token=token, expires_minutes=settings.app_jwt_expires_minutes)
