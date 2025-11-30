from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile
from app.schemas.message import MessageCreate, MessageResponse, MessageReactionCreate, MessageReactionResponse
from app.models.profile import Profile
from app.models.conversation import ConversationParticipant
from app.models.message import Message, MessageReaction, MessageType
from app.services.supabase_realtime import SupabaseRealtimeService
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from uuid import UUID

router = APIRouter(prefix="/messages", tags=["messages"])
realtime_service = SupabaseRealtimeService()

@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Send a message"""
    # Verify user is participant in conversation
    participant_result = await db.execute(
        select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == message_data.conversation_id,
                ConversationParticipant.profile_id == profile.id
            )
        )
    )
    if not participant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    # Validate message content
    if message_data.message_type == MessageType.TEXT and not message_data.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text message must have content"
        )
    
    if message_data.message_type == MessageType.MEDIA and not message_data.media_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media message must have media_url"
        )
    
    # Create message
    new_message = Message(
        conversation_id=message_data.conversation_id,
        sender_id=profile.id,
        content=message_data.content,
        message_type=message_data.message_type,
        media_url=message_data.media_url
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    # Load sender for response
    await db.refresh(new_message, ["sender"])
    
    # Broadcast via Supabase Realtime (this would typically be handled client-side)
    # For server-side, you could use Supabase's REST API to trigger realtime events
    
    return MessageResponse.model_validate(new_message)

@router.post("/{message_id}/reactions", response_model=MessageReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reaction(
    message_id: UUID,
    reaction_data: MessageReactionCreate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Add reaction to a message"""
    # Get message
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if reaction already exists
    existing_reaction_result = await db.execute(
        select(MessageReaction).where(
            and_(
                MessageReaction.message_id == message_id,
                MessageReaction.profile_id == profile.id,
                MessageReaction.reaction_type == reaction_data.reaction_type
            )
        )
    )
    existing_reaction = existing_reaction_result.scalar_one_or_none()
    
    if existing_reaction:
        # Reaction already exists, return it
        await db.refresh(existing_reaction, ["profile"])
        return MessageReactionResponse.model_validate(existing_reaction)
    
    # Create new reaction
    new_reaction = MessageReaction(
        message_id=message_id,
        profile_id=profile.id,
        reaction_type=reaction_data.reaction_type
    )
    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)
    
    # Load profile for response
    await db.refresh(new_reaction, ["profile"])
    
    return MessageReactionResponse.model_validate(new_reaction)

@router.delete("/{message_id}/reactions/{reaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    message_id: UUID,
    reaction_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Remove reaction from a message"""
    # Get reaction
    result = await db.execute(
        select(MessageReaction).where(
            and_(
                MessageReaction.id == reaction_id,
                MessageReaction.message_id == message_id,
                MessageReaction.profile_id == profile.id
            )
        )
    )
    reaction = result.scalar_one_or_none()
    
    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )
    
    await db.delete(reaction)
    await db.commit()
    
    return None

@router.put("/{message_id}/read", response_model=MessageResponse)
async def mark_message_read(
    message_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Mark message as read"""
    # Get message
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Verify user is participant in conversation
    participant_result = await db.execute(
        select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == message.conversation_id,
                ConversationParticipant.profile_id == profile.id
            )
        )
    )
    if not participant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    # Mark as read
    message.is_read = True
    
    # Update last_read_at in conversation participant
    participant = participant_result.scalar_one()
    from datetime import datetime
    participant.last_read_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    await db.refresh(message, ["sender"])
    
    return MessageResponse.model_validate(message)

