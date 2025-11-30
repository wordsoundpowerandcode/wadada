from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from app.models.message import MessageType, ReactionType
from app.schemas.profile import ProfileResponse

class MessageCreate(BaseModel):
    conversation_id: UUID
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender: ProfileResponse
    content: Optional[str] = None
    message_type: MessageType
    media_url: Optional[str] = None
    is_read: bool
    reactions: List["MessageReactionResponse"] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageReactionCreate(BaseModel):
    reaction_type: ReactionType

class MessageReactionResponse(BaseModel):
    id: UUID
    message_id: UUID
    profile: ProfileResponse
    reaction_type: ReactionType
    created_at: datetime
    
    class Config:
        from_attributes = True

# Update forward references
MessageResponse.model_rebuild()

