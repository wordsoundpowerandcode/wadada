from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile, get_current_user_id
from app.schemas.media import MediaUploadResponse, MediaResponse
from app.models.profile import Profile
from app.models.media import UserMedia, MediaType
from app.services.supabase_storage import SupabaseStorageService
from app.utils.validators import validate_media_file
from sqlalchemy import select
from uuid import UUID

router = APIRouter(prefix="/media", tags=["media"])
storage_service = SupabaseStorageService()

@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    is_intro_media: bool = False,
    profile: Profile = Depends(get_current_profile),
    supabase_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Upload media file (video or audio)"""
    # Validate file
    validation_result = await validate_media_file(file)
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["error"]
        )
    
    # Determine media type
    mime_type = file.content_type
    if mime_type.startswith("video/"):
        media_type = MediaType.VIDEO
    else:
        media_type = MediaType.AUDIO
    
    # Upload to Supabase Storage
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    file_url = await storage_service.upload_file(
        file.file,
        supabase_user_id,  # Use Supabase user ID for folder structure
        mime_type,
        file_extension
    )
    
    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    # Create media record
    new_media = UserMedia(
        profile_id=profile.id,
        supabase_user_id=supabase_user_id,
        media_type=media_type,
        file_url=file_url,
        file_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        is_intro_media=is_intro_media
    )
    
    db.add(new_media)
    await db.commit()
    await db.refresh(new_media)
    
    return MediaUploadResponse.model_validate(new_media)

@router.put("/intro-media", response_model=MediaResponse)
async def update_intro_media(
    file: UploadFile = File(...),
    profile: Profile = Depends(get_current_profile),
    supabase_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user's introductory media"""
    # Delete old intro media if exists
    if profile.intro_media:
        await storage_service.delete_file(profile.intro_media.file_url)
        await db.delete(profile.intro_media)
        await db.flush()
    
    # Upload new media
    validation_result = await validate_media_file(file)
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["error"]
        )
    
    mime_type = file.content_type
    if mime_type.startswith("video/"):
        media_type = MediaType.VIDEO
    else:
        media_type = MediaType.AUDIO
    
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    file_url = await storage_service.upload_file(
        file.file,
        supabase_user_id,
        mime_type,
        file_extension
    )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    # Create new media record
    new_media = UserMedia(
        profile_id=profile.id,
        supabase_user_id=supabase_user_id,
        media_type=media_type,
        file_url=file_url,
        file_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        is_intro_media=True
    )
    
    db.add(new_media)
    await db.commit()
    await db.refresh(new_media)
    
    return MediaResponse.model_validate(new_media)

@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get media metadata"""
    result = await db.execute(
        select(UserMedia).where(UserMedia.id == media_id)
    )
    media = result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    return MediaResponse.model_validate(media)

