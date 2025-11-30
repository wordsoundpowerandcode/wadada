from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.media import MediaType

class MediaUploadResponse(BaseModel):
    id: UUID
    file_url: str
    media_type: MediaType
    file_name: str
    file_size: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MediaResponse(MediaUploadResponse):
    duration: Optional[int] = None
    is_intro_media: bool
    moderation_status: Optional[str] = None

