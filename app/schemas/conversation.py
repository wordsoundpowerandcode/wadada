from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from app.schemas.profile import ProfileResponse
from app.schemas.message import MessageResponse

class ConversationCreate(BaseModel):
    participant_ids: List[UUID]  # List of profile IDs to start conversation with

class ConversationResponse(BaseModel):
    id: UUID
    participants: List[ProfileResponse]
    last_message: Optional[MessageResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConversationListResponse(BaseModel):
    id: UUID
    participants: List[ProfileResponse]
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

