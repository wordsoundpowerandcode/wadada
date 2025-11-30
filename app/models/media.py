from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
import uuid
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

class MediaType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"

class UserMedia(SQLModel, table=True):
    __tablename__ = "user_media"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profiles.id")
    # Also store supabase_user_id for quick lookups
    supabase_user_id: str = Field(index=True)
    media_type: MediaType
    file_url: str
    file_name: str
    file_size: int  # in bytes
    duration: Optional[int] = None  # in seconds (for video/audio)
    mime_type: str
    is_intro_media: bool = False
    is_moderated: bool = False
    moderation_status: Optional[str] = None  # "approved", "rejected", "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    profile: Optional["Profile"] = Relationship(back_populates="media")
