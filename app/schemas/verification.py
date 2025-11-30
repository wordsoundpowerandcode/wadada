"""
Pydantic schemas for verification endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.verification import VerificationType, VerificationStatus


class VerificationCodeResponse(BaseModel):
    """Response for verification code request."""
    verification_code: str
    expires_at: datetime
    
    class Config:
        from_attributes = True


class VerificationResponse(BaseModel):
    """Response for verification operations."""
    id: int
    profile_id: int
    verification_type: VerificationType
    status: VerificationStatus
    media_url: Optional[str] = None
    verification_code: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerificationStatusResponse(BaseModel):
    """Response for verification status check."""
    photo_verification: Optional[VerificationResponse] = None
    video_verification: Optional[VerificationResponse] = None
    is_photo_verified: bool
    is_video_verified: bool
    
    class Config:
        from_attributes = True
