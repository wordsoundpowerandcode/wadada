from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationListResponse
from app.schemas.message import MessageResponse
from app.models.profile import Profile
from app.models.conversation import Conversation, ConversationParticipant
from app.models.message import Message
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationListResponse])
async def list_conversations(
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List user's conversations"""
    # Get conversations where user is a participant
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.profile_id == profile.id)
        .options(
            selectinload(Conversation.participant_relations).selectinload(ConversationParticipant.profile),
            selectinload(Conversation.messages)
        )
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    # Build response with unread count
    response_list = []
    for conv in conversations:
        # Get unread count
        unread_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.conversation_id == conv.id,
                    Message.sender_id != profile.id,
                    Message.is_read == False
                )
            )
        )
        unread_count = unread_result.scalar() or 0
        
        # Get last message
        last_message_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
            .options(selectinload(Message.sender))
        )
        last_message = last_message_result.scalar_one_or_none()
        
        # Get participants (excluding current user for display)
        participants = [p.profile for p in conv.participant_relations if p.profile_id != profile.id]
        
        response_list.append(ConversationListResponse(
            id=conv.id,
            participants=participants,
            last_message=MessageResponse.model_validate(last_message) if last_message else None,
            unread_count=unread_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        ))
    
    return response_list

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation"""
    # Check if conversation already exists with these participants
    participant_ids = set(conversation_data.participant_ids)
    participant_ids.add(profile.id)  # Include current user
    
    # Get existing conversations
    existing_conv_result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.profile_id == profile.id)
        .options(selectinload(Conversation.participant_relations))
    )
    existing_convs = existing_conv_result.scalars().all()
    
    # Check if conversation with same participants exists
    for conv in existing_convs:
        conv_participant_ids = {p.profile_id for p in conv.participant_relations}
        if conv_participant_ids == participant_ids:
            # Return existing conversation
            participants = [p.profile for p in conv.participant_relations]
            return ConversationResponse(
                id=conv.id,
                participants=participants,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
    
    # Create new conversation
    new_conversation = Conversation()
    db.add(new_conversation)
    await db.flush()
    
    # Add participants
    all_participant_ids = list(participant_ids)
    participant_profiles_result = await db.execute(
        select(Profile).where(Profile.id.in_(all_participant_ids))
    )
    participant_profiles = participant_profiles_result.scalars().all()
    
    for part_profile in participant_profiles:
        participant = ConversationParticipant(
            conversation_id=new_conversation.id,
            profile_id=part_profile.id
        )
        db.add(participant)
    
    await db.commit()
    await db.refresh(new_conversation)
    
    # Load participants for response
    await db.refresh(new_conversation, ["participant_relations"])
    participants = [p.profile for p in new_conversation.participant_relations]
    
    return ConversationResponse(
        id=new_conversation.id,
        participants=participants,
        created_at=new_conversation.created_at,
        updated_at=new_conversation.updated_at
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation details"""
    # Verify user is participant
    participant_result = await db.execute(
        select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.profile_id == profile.id
            )
        )
    )
    if not participant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    # Get conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.participant_relations).selectinload(ConversationParticipant.profile),
            selectinload(Conversation.messages).selectinload(Message.sender)
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get last message
    last_message_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(1)
        .options(selectinload(Message.sender))
    )
    last_message = last_message_result.scalar_one_or_none()
    
    participants = [p.profile for p in conversation.participant_relations]
    
    return ConversationResponse(
        id=conversation.id,
        participants=participants,
        last_message=MessageResponse.from_orm(last_message) if last_message else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get message history for a conversation"""
    # Verify user is participant
    participant_result = await db.execute(
        select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.profile_id == profile.id
            )
        )
    )
    if not participant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(
            selectinload(Message.sender),
            selectinload(Message.reactions).selectinload(MessageReaction.profile)
        )
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [MessageResponse.model_validate(msg) for msg in reversed(messages)]

