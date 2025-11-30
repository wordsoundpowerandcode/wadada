from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime, Enum, String
from datetime import datetime
from typing import Optional
import uuid
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

class VerificationType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    ID = "id"

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class Verification(SQLModel, table=True):
    __tablename__ = "verifications"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profiles.id", unique=True, index=True)
    verification_type: VerificationType
    status: VerificationStatus = VerificationStatus.PENDING
    media_url: Optional[str] = None  # URL to verification photo/video
    verification_code: Optional[str] = None  # For photo verification (selfie code)
    rejection_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    profile: Optional["Profile"] = Relationship()

