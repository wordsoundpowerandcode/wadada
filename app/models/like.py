from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime, Enum
from datetime import datetime
from typing import Optional
import uuid
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

class LikeType(str, enum.Enum):
    LIKE = "like"
    SUPER_LIKE = "super_like"

class Like(SQLModel, table=True):
    __tablename__ = "likes"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    liker_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    liked_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    like_type: LikeType = LikeType.LIKE
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    
    # Relationships
    liker: Optional["Profile"] = Relationship(
        foreign_keys=[liker_id],
        sa_relationship_kwargs={"primaryjoin": "Like.liker_id == Profile.id"}
    )
    liked: Optional["Profile"] = Relationship(
        foreign_keys=[liked_id],
        sa_relationship_kwargs={"primaryjoin": "Like.liked_id == Profile.id"}
    )
    
    # Unique constraint: one like per user pair
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

