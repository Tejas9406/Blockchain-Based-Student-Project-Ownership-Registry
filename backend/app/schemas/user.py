from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """Permitted user roles."""
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    ADMIN = "ADMIN"
    VERIFIER = "VERIFIER"


class UserRegisterRequest(BaseModel):
    """
    Schema for user registration request payload.
    Conforms to API_CONTRACT.md / FRONTEND_BACKEND_CONTRACT.md.
    Strictly forbids accepting internal UUID, password hashes, timestamps, or role escalation.
    """
    email: EmailStr = Field(..., description="Valid institutional or personal email address")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full legal name")
    institution_id: str = Field(..., min_length=2, max_length=100, description="College / University ID")
    institution_name: Optional[str] = Field(default=None, max_length=255, description="College / University name")
    department: str = Field(..., min_length=2, max_length=100, description="Academic department")
    role: Optional[Literal["STUDENT"]] = Field(
        default="STUDENT",
        description="User role (defaults to STUDENT; public registration cannot escalate roles)"
    )
    wallet_address: Optional[str] = Field(default=None, max_length=42, description="Optional 0x... EVM wallet address")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or whitespace-only.")
        return v

    @field_validator("full_name", "institution_id", "department")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace.")
        return trimmed


class UserLoginRequest(BaseModel):
    """
    Schema for user login credentials.
    Strictly accepts only email and plaintext password.
    Disallows internal IDs, password hashes, roles, wallet addresses, or admin fields.
    """
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserSummaryResponse(BaseModel):
    """
    Public User summary returned upon authentication.
    Strictly excludes internal UUID, password, and password_hash.
    """
    public_id: str = Field(..., description="Public user identifier (USR-YYYYMM-XXXXX)")
    email: str = Field(..., description="Normalized email address")
    full_name: str = Field(..., description="Full legal name of the user")
    role: str = Field(..., description="Assigned role")
    institution_id: str = Field(..., description="Institutional student/faculty ID")
    department: str = Field(..., description="Academic department")

    model_config = ConfigDict(from_attributes=True)


class LoginResponseData(BaseModel):
    """
    Payload returned in data field upon successful login (API_CONTRACT.md Section 4.2).
    """
    access_token: str = Field(..., description="JWT Bearer access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Access token lifetime in seconds")
    user: UserSummaryResponse = Field(..., description="Authenticated user summary")


class RefreshTokenRequest(BaseModel):
    """
    Schema for token refresh request payload (API_CONTRACT.md Section 4.3).
    """
    refresh_token: str = Field(..., min_length=1, description="Valid JWT refresh token")


class RefreshTokenResponseData(BaseModel):
    """
    Payload returned in data field upon successful token refresh.
    """
    access_token: str = Field(..., description="Newly issued JWT access token")
    refresh_token: str = Field(..., description="Newly rotated JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Access token lifetime in seconds")


class UserProfileResponse(BaseModel):
    """
    Public User Profile response schema.
    Strictly excludes internal database UUID, password, and password_hash.
    """
    public_id: str = Field(..., description="Public user identifier (USR-YYYYMM-XXXXX)")
    email: str = Field(..., description="Normalized email address")
    full_name: str = Field(..., description="Full legal name of the user")
    institution_id: str = Field(..., description="Institutional student/faculty ID")
    institution_name: Optional[str] = Field(default=None, description="Institution name")
    department: str = Field(..., description="Academic department")
    role: str = Field(..., description="Assigned role")
    wallet_address: Optional[str] = Field(default=None, description="EVM wallet address")
    is_verified: bool = Field(default=False, description="Whether institutional email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)
