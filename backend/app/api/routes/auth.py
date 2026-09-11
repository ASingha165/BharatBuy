from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.auth import (
    UserSignUpRequest,
    UserSignInRequest,
    UserResponse,
    AuthResponse,
    FirebaseSyncRequest
)
from backend.app.services.auth_service import AuthService
from backend.app.api.dependencies import get_auth_service

router = APIRouter()

def _extract_token_from_request(request: Request) -> Optional[str]:
    # 1. Check Authorization Bearer header (explicit credential takes precedence)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 2. Check HTTP-only cookie (fallback for browser sessions)
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None

def get_current_user_optional(
    request: Request,
    auth_svc: AuthService = Depends(get_auth_service)
) -> Optional[UserResponse]:
    token = _extract_token_from_request(request)
    if not token:
        return None
    user = auth_svc.get_current_user_from_token(token)
    if not user:
        return None
    return UserResponse(**user)

def get_current_user_required(
    request: Request,
    auth_svc: AuthService = Depends(get_auth_service)
) -> UserResponse:
    user = get_current_user_optional(request, auth_svc)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource."
        )
    return user

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: UserSignUpRequest,
    response: Response,
    auth_svc: AuthService = Depends(get_auth_service)
):
    if not settings.ENABLE_LEGACY_AUTH:
        logger.warning(f"[AUTH] Legacy direct signup blocked for {payload.email} (ENABLE_LEGACY_AUTH=False)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct password registration is disabled. Please use Firebase Authentication (/api/v1/auth/firebase-sync)."
        )

    logger.info(f"[AUTH] Processing signup request for email: {payload.email}")
    user_dict, token, error = auth_svc.signup_user(payload)
    if error:
        logger.warning(f"[AUTH] Signup failed for {payload.email}: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Set secure HTTP-only cookie
    max_age_seconds = settings.AUTH_TOKEN_EXPIRE_DAYS * 24 * 3600
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production environments
        path="/"
    )

    logger.info(f"[AUTH] User {payload.email} signed up successfully (id: {user_dict['id']})")
    return AuthResponse(
        user=UserResponse(**user_dict),
        token=token,
        message="Account created successfully"
    )

@router.post("/signin", response_model=AuthResponse)
def signin(
    payload: UserSignInRequest,
    response: Response,
    auth_svc: AuthService = Depends(get_auth_service)
):
    if not settings.ENABLE_LEGACY_AUTH:
        logger.warning(f"[AUTH] Legacy direct signin blocked for {payload.email} (ENABLE_LEGACY_AUTH=False)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct password signin is disabled. Please use Firebase Authentication (/api/v1/auth/firebase-sync)."
        )

    logger.info(f"[AUTH] Processing signin request for email: {payload.email}")
    user_dict, token, error = auth_svc.signin_user(payload)
    if error:
        logger.warning(f"[AUTH] Signin failed for {payload.email}: {error}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    # Set secure HTTP-only cookie (30 days if remember_me, else 7 days)
    days = 30 if payload.remember_me else settings.AUTH_TOKEN_EXPIRE_DAYS
    max_age_seconds = days * 24 * 3600
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    logger.info(f"[AUTH] User {payload.email} signed in successfully (id: {user_dict['id']})")
    return AuthResponse(
        user=UserResponse(**user_dict),
        token=token,
        message="Sign in successful"
    )

@router.post("/signout")
def signout(response: Response):
    logger.info("[AUTH] Processing signout request")
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/"
    )
    return {"message": "Sign out successful"}

@router.post("/firebase-sync", response_model=AuthResponse)
def firebase_sync(
    payload: FirebaseSyncRequest,
    request: Request,
    response: Response,
    auth_svc: AuthService = Depends(get_auth_service)
):
    token = _extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required"
        )
    user_dict, error = auth_svc.sync_firebase_user(
        token=token,
        name=payload.name,
        organization=payload.organization
    )
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    # Set secure HTTP-only cookie
    max_age_seconds = settings.AUTH_TOKEN_EXPIRE_DAYS * 24 * 3600
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    logger.info(f"[AUTH] Firebase user {user_dict['email']} synced successfully (id: {user_dict['id']})")
    return AuthResponse(
        user=UserResponse(**user_dict),
        token=token,
        message="Firebase account synchronized successfully"
    )

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: UserResponse = Depends(get_current_user_required)
):
    return current_user
