from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Column
from sqlalchemy import DateTime
from datetime import datetime
from typing import Optional, List
import uuid
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.conversation import Conversation

class MessageType(str, enum.Enum):
    TEXT = "text"
    MEDIA = "media"

class ReactionType(str, enum.Enum):
    LIKE = "like"
    HEART = "heart"
    LAUGH = "laugh"
    SAD = "sad"
    ANGRY = "angry"
    WOW = "wow"

class Message(SQLModel, table=True):
    __tablename__ = "messages"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id")
    sender_id: uuid.UUID = Field(foreign_key="profiles.id")
    content: Optional[str] = None  # Nullable for media messages
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None  # For media messages
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
    sender: Optional["Profile"] = Relationship(back_populates="sent_messages")
    reactions: List["MessageReaction"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class MessageReaction(SQLModel, table=True):
    __tablename__ = "message_reactions"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="messages.id")
    profile_id: uuid.UUID = Field(foreign_key="profiles.id")
    reaction_type: ReactionType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    message: Optional["Message"] = Relationship(back_populates="reactions")
    profile: Optional["Profile"] = Relationship(back_populates="message_reactions")
    
    # Unique constraint: one reaction type per profile per message
    __table_args__ = (
        UniqueConstraint('message_id', 'profile_id', 'reaction_type', name='uq_message_reaction'),
    )
