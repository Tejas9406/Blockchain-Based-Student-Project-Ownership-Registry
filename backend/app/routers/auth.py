from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ApiErrorResponse, ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.user import (
    LoginResponseData,
    UserProfileResponse,
    UserRegisterRequest,
    UserLoginRequest,
    UserSummaryResponse,
)
from app.services.user_service import authenticate_user, register_user

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
    }
)
def register(
    request: Request,
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[UserProfileResponse]:
    user = register_user(db=db, request=payload)
    request_id = getattr(request.state, "request_id", None)
    
    return ApiResponse(
        success=True,
        data=UserProfileResponse.model_validate(user),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id
        )
    )


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials, verifies Argon2id password hash, and issues a JWT access token.",
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
    }
)
def login(
    request: Request,
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[LoginResponseData]:
    user, access_token, expires_in = authenticate_user(db=db, request=payload)
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=LoginResponseData(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserSummaryResponse.model_validate(user)
        ),
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id
        )
    )
