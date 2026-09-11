import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class UserSignUpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: str = Field(..., description="Work email address")
    organization: str = Field(..., min_length=2, max_length=150, description="Organization / Startup / Entity name")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")
    terms_accepted: bool = Field(..., description="Consent to statutory procurement governance terms")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format")
        return clean

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters long")
        return stripped

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() or not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one number or special character")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Terms and statutory governance consent must be accepted")
        return v


class UserSignInRequest(BaseModel):
    email: str = Field(..., description="Work email address")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: Optional[bool] = Field(default=False, description="Extend session duration")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format")
        return clean


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    organization: str
    created_at: str


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
    message: str


class FirebaseSyncRequest(BaseModel):
    name: Optional[str] = Field(default=None, description="User full name")
    organization: Optional[str] = Field(default=None, description="Organization or startup name")
