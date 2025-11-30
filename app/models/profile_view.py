from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime
from datetime import datetime
from typing import Optional
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

class ProfileView(SQLModel, table=True):
    __tablename__ = "profile_views"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    viewer_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    viewed_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    viewed_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    
    # Relationships
    viewer: Optional["Profile"] = Relationship(
        foreign_keys=[viewer_id],
        sa_relationship_kwargs={"primaryjoin": "ProfileView.viewer_id == Profile.id"}
    )
    viewed: Optional["Profile"] = Relationship(
        foreign_keys=[viewed_id],
        sa_relationship_kwargs={"primaryjoin": "ProfileView.viewed_id == Profile.id"}
    )

