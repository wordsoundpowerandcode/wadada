"""
Verification API routes for photo and video verification.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional
import secrets
import string
from datetime import datetime

from app.database import get_session
from app.api.deps import get_current_user
from app.models.profile import Profile
from app.models.verification import Verification, VerificationType, VerificationStatus
from app.services.supabase_storage import SupabaseStorageService
from app.services.content_moderation import ContentModerationService
from app.schemas.verification import (
    VerificationResponse,
    VerificationStatusResponse,
    VerificationCodeResponse
)

router = APIRouter(prefix="/verification", tags=["verification"])


def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code."""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


@router.post("/photo/request-code", response_model=VerificationCodeResponse)
async def request_photo_verification_code(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Request a verification code for photo verification.
    User will need to take a selfie holding a paper with this code.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if there's already a pending photo verification
    result = await session.execute(
        select(Verification).where(
            Verification.profile_id == profile.id,
            Verification.verification_type == VerificationType.PHOTO,
            Verification.status == VerificationStatus.PENDING
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return VerificationCodeResponse(
            verification_code=existing.verification_code,
            expires_at=existing.created_at
        )
    
    # Generate new verification code
    code = generate_verification_code()
    
    # Create verification record
    verification = Verification(
        profile_id=profile.id,
        verification_type=VerificationType.PHOTO,
        verification_code=code,
        status=VerificationStatus.PENDING
    )
    
    session.add(verification)
    await session.commit()
    await session.refresh(verification)
    
    return VerificationCodeResponse(
        verification_code=code,
        expires_at=verification.created_at
    )


@router.post("/photo/upload", response_model=VerificationResponse)
async def upload_photo_verification(
    file: UploadFile = File(...),
    verification_code: str = Form(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    storage_service: SupabaseStorageService = Depends(),
    moderation_service: ContentModerationService = Depends()
):
    """
    Upload a selfie with verification code for photo verification.
    The photo should show the user holding a paper with the verification code.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Find verification record with matching code
    result = await session.execute(
        select(Verification).where(
            Verification.profile_id == profile.id,
            Verification.verification_type == VerificationType.PHOTO,
            Verification.verification_code == verification_code.upper(),
            Verification.status == VerificationStatus.PENDING
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(
            status_code=404, 
            detail="Invalid or expired verification code"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Moderate image content
    is_appropriate, reason = await moderation_service.moderate_image(file_content)
    
    if not is_appropriate:
        verification.status = VerificationStatus.REJECTED
        verification.rejection_reason = f"Content moderation failed: {reason}"
        await session.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Image rejected: {reason}"
        )
    
    # Upload to Supabase Storage
    file_path = f"verification/photo/{profile.id}/{verification.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_content=file_content,
        file_name=file_path,
        content_type=file.content_type
    )
    
    # Update verification record
    verification.media_url = url
    verification.submitted_at = datetime.utcnow()
    # In production, you might want manual review or AI-based code detection
    # For now, we'll auto-approve if content moderation passes
    verification.status = VerificationStatus.APPROVED
    verification.verified_at = datetime.utcnow()
    
    # Update profile verification status
    profile.is_photo_verified = True
    
    await session.commit()
    await session.refresh(verification)
    
    return VerificationResponse.from_orm(verification)


@router.post("/video/upload", response_model=VerificationResponse)
async def upload_video_verification(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    storage_service: SupabaseStorageService = Depends(),
    moderation_service: ContentModerationService = Depends()
):
    """
    Upload a video for verification (30-60 seconds).
    This is the intro video required for profile activation.
    """
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Video file too large. Maximum size is 50MB"
        )
    
    # TODO: Validate video duration (30-60 seconds)
    # This would require video processing library like ffmpeg
    
    # Moderate video content
    is_appropriate, reason = await moderation_service.moderate_video(file_content)
    
    if not is_appropriate:
        raise HTTPException(
            status_code=400,
            detail=f"Video rejected: {reason}"
        )
    
    # Upload to Supabase Storage
    file_path = f"verification/video/{profile.id}/{datetime.utcnow().timestamp()}_{file.filename}"
    url = await storage_service.upload_file(
        file_content=file_content,
        file_name=file_path,
        content_type=file.content_type
    )
    
    # Create or update verification record
    result = await session.execute(
        select(Verification).where(
            Verification.profile_id == profile.id,
            Verification.verification_type == VerificationType.VIDEO
        )
    )
    verification = result.scalar_one_or_none()
    
    if verification:
        # Update existing
        verification.media_url = url
        verification.submitted_at = datetime.utcnow()
        verification.status = VerificationStatus.PENDING
    else:
        # Create new
        verification = Verification(
            profile_id=profile.id,
            verification_type=VerificationType.VIDEO,
            media_url=url,
            submitted_at=datetime.utcnow(),
            status=VerificationStatus.PENDING
        )
        session.add(verification)
    
    await session.commit()
    await session.refresh(verification)
    
    return VerificationResponse.from_orm(verification)


@router.get("/status", response_model=VerificationStatusResponse)
async def get_verification_status(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the current verification status for the user.
    Returns status for both photo and video verification.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get photo verification
    result = await session.execute(
        select(Verification)
        .where(
            Verification.profile_id == profile.id,
            Verification.verification_type == VerificationType.PHOTO
        )
        .order_by(Verification.created_at.desc())
    )
    photo_verification = result.scalar_one_or_none()
    
    # Get video verification
    result = await session.execute(
        select(Verification)
        .where(
            Verification.profile_id == profile.id,
            Verification.verification_type == VerificationType.VIDEO
        )
        .order_by(Verification.created_at.desc())
    )
    video_verification = result.scalar_one_or_none()
    
    return VerificationStatusResponse(
        photo_verification=VerificationResponse.from_orm(photo_verification) if photo_verification else None,
        video_verification=VerificationResponse.from_orm(video_verification) if video_verification else None,
        is_photo_verified=profile.is_photo_verified,
        is_video_verified=profile.is_video_verified
    )


@router.put("/{verification_id}/approve", response_model=VerificationResponse)
async def approve_verification(
    verification_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Approve a verification (admin only).
    In production, add admin role check.
    """
    # TODO: Add admin role check
    # For now, we'll allow the user to approve their own (for testing)
    
    result = await session.execute(
        select(Verification).where(Verification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Get profile
    result = await session.execute(
        select(Profile).where(Profile.id == verification.profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update verification
    verification.status = VerificationStatus.APPROVED
    verification.verified_at = datetime.utcnow()
    
    # Update profile verification flags
    if verification.verification_type == VerificationType.PHOTO:
        profile.is_photo_verified = True
    elif verification.verification_type == VerificationType.VIDEO:
        profile.is_video_verified = True
    
    await session.commit()
    await session.refresh(verification)
    
    return VerificationResponse.from_orm(verification)


@router.put("/{verification_id}/reject", response_model=VerificationResponse)
async def reject_verification(
    verification_id: int,
    reason: str = Form(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Reject a verification (admin only).
    In production, add admin role check.
    """
    # TODO: Add admin role check
    
    result = await session.execute(
        select(Verification).where(Verification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Update verification
    verification.status = VerificationStatus.REJECTED
    verification.rejection_reason = reason
    
    await session.commit()
    await session.refresh(verification)
    
    return VerificationResponse.from_orm(verification)
