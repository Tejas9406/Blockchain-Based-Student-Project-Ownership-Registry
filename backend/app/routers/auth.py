from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.error import ApiErrorResponse
from app.schemas.user import (
    LoginResponseData,
    RefreshTokenRequest,
    RefreshTokenResponseData,
    UserProfileResponse,
    UserRegisterRequest,
    UserLoginRequest,
    UserSummaryResponse,
)
from app.services.user_service import (
    authenticate_user,
    refresh_access_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[UserProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Creates a new student account, hashes the plaintext password with Argon2id, and returns the public user profile.",
    responses={
        status.HTTP_201_CREATED: {
            "model": ApiResponse[UserProfileResponse],
            "description": "User successfully registered.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "An account with the submitted email address already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Validation failure in request payload.",
        },
    },
)
def register(
    request: Request,
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    user = register_user(db=db, request=payload)
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=UserProfileResponse.model_validate(user),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials, verifies Argon2id password hash, and issues a JWT access token and refresh token.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[LoginResponseData],
            "description": "User successfully authenticated.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Invalid authentication credentials.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Validation failure in request payload.",
        },
    },
)
def login(
    request: Request,
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[LoginResponseData]:
    user, access_token, refresh_token_str, expires_in = authenticate_user(
        db=db, request=payload
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=LoginResponseData(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=expires_in,
            user=UserSummaryResponse.model_validate(user),
        ),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshTokenResponseData],
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Validates a refresh token and issues a new access token and rotated refresh token.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[RefreshTokenResponseData],
            "description": "Tokens successfully refreshed.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Invalid or expired refresh token.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Validation failure in request payload.",
        },
    },
)
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[RefreshTokenResponseData]:
    access_token, new_refresh_token, expires_in = refresh_access_token(
        db=db, refresh_token_str=payload.refresh_token
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=RefreshTokenResponseData(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expires_in,
        ),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Retrieves the profile summary of the currently authenticated user using a Bearer access token.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[UserSummaryResponse],
            "description": "User profile successfully retrieved.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Missing, expired, or invalid access token.",
        },
    },
)
def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserSummaryResponse]:
    request_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )
