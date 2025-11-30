from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Table, ForeignKey, DateTime
from datetime import datetime
from typing import List, Optional
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.message import Message

# Association table for many-to-many relationship between Profile and Conversation
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

conversation_participants = Table(
    "conversation_participants",
    SQLModel.metadata,
    Column("conversation_id", PG_UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True),
    Column("profile_id", PG_UUID(as_uuid=True), ForeignKey("profiles.id"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow),
    Column("last_read_at", DateTime, nullable=True)
)

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Many-to-many relationship with Profile through association table
    participants: List["Profile"] = Relationship(
        back_populates="conversation_list",
        sa_relationship_kwargs={"secondary": conversation_participants}
    )
    # Direct relationship through ConversationParticipant for additional metadata
    participant_relations: List["ConversationParticipant"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Message.created_at"
        }
    )

class ConversationParticipant(SQLModel, table=True):
    __tablename__ = "conversation_participants_metadata"
    
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id", primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profiles.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_read_at: Optional[datetime] = None
    
    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="participant_relations")
    profile: Optional["Profile"] = Relationship(back_populates="conversations")
