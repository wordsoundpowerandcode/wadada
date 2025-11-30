from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile
from app.models.profile import Profile
from app.models.like import Like, LikeType
from app.models.credit import CreditBalance, CreditTransaction, CreditTransactionType
from app.services.credit_service import CreditService
from sqlalchemy import select, and_, or_
from uuid import UUID
from typing import List

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("/{profile_id}")
async def like_profile(
    profile_id: UUID,
    like_type: LikeType = LikeType.LIKE,
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Like or super like a profile"""
    # Check if already liked
    existing_like = await db.execute(
        select(Like).where(
            and_(
                Like.liker_id == current_profile.id,
                Like.liked_id == profile_id
            )
        )
    )
    if existing_like.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already liked"
        )
    
    # Check if trying to like own profile
    if profile_id == current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot like your own profile"
        )
    
    # Check if super like and deduct credits
    if like_type == LikeType.SUPER_LIKE:
        credit_service = CreditService(db)
        has_credits = await credit_service.check_and_deduct_credits(
            current_profile.id,
            CreditTransactionType.SUPER_LIKE
        )
        if not has_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits for super like"
            )
    
    # Create like
    new_like = Like(
        liker_id=current_profile.id,
        liked_id=profile_id,
        like_type=like_type
    )
    db.add(new_like)
    
    # Update liked profile's likes count
    liked_profile_result = await db.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    liked_profile = liked_profile_result.scalar_one_or_none()
    if liked_profile:
        liked_profile.likes_received_count += 1
    
    # Check for mutual like (match)
    mutual_like = await db.execute(
        select(Like).where(
            and_(
                Like.liker_id == profile_id,
                Like.liked_id == current_profile.id
            )
        )
    )
    is_match = mutual_like.scalar_one_or_none() is not None
    
    if is_match:
        # Update match counts for both profiles
        current_profile.matches_count += 1
        if liked_profile:
            liked_profile.matches_count += 1
    
    await db.commit()
    
    return {
        "liked": True,
        "like_type": like_type.value,
        "is_match": is_match,
        "message": "It's a match!" if is_match else "Like sent"
    }

@router.delete("/{profile_id}")
async def unlike_profile(
    profile_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Unlike a profile"""
    like_result = await db.execute(
        select(Like).where(
            and_(
                Like.liker_id == current_profile.id,
                Like.liked_id == profile_id
            )
        )
    )
    like = like_result.scalar_one_or_none()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )
    
    await db.delete(like)
    await db.commit()
    
    return {"unliked": True}

@router.get("/received")
async def get_likes_received(
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get profiles that liked current user"""
    likes_result = await db.execute(
        select(Like).where(Like.liked_id == current_profile.id)
        .order_by(Like.created_at.desc())
    )
    likes = likes_result.scalars().all()
    
    # Get profiles
    liker_ids = [like.liker_id for like in likes]
    profiles_result = await db.execute(
        select(Profile).where(Profile.id.in_(liker_ids))
    )
    profiles = {p.id: p for p in profiles_result.scalars().all()}
    
    return {
        "likes": [
            {
                "profile_id": str(like.liker_id),
                "like_type": like.like_type.value,
                "created_at": like.created_at.isoformat(),
                "profile": {
                    "name": profiles[like.liker_id].name,
                    "age": profiles[like.liker_id].age,
                    "bio": profiles[like.liker_id].bio
                } if like.liker_id in profiles else None
            }
            for like in likes
        ],
        "total": len(likes)
    }

@router.get("/sent")
async def get_likes_sent(
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get profiles current user has liked"""
    likes_result = await db.execute(
        select(Like).where(Like.liker_id == current_profile.id)
        .order_by(Like.created_at.desc())
    )
    likes = likes_result.scalars().all()
    
    return {
        "likes": [
            {
                "profile_id": str(like.liked_id),
                "like_type": like.like_type.value,
                "created_at": like.created_at.isoformat()
            }
            for like in likes
        ],
        "total": len(likes)
    }

@router.get("/matches")
async def get_matches(
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get mutual matches (both users liked each other)"""
    # Get likes where current user liked someone
    my_likes_result = await db.execute(
        select(Like).where(Like.liker_id == current_profile.id)
    )
    my_likes = {like.liked_id for like in my_likes_result.scalars().all()}
    
    # Get likes where someone liked current user
    their_likes_result = await db.execute(
        select(Like).where(Like.liked_id == current_profile.id)
    )
    their_likes = {like.liker_id for like in their_likes_result.scalars().all()}
    
    # Find mutual likes (matches)
    match_ids = my_likes & their_likes
    
    # Get match profiles
    if match_ids:
        profiles_result = await db.execute(
            select(Profile).where(Profile.id.in_(match_ids))
        )
        match_profiles = profiles_result.scalars().all()
    else:
        match_profiles = []
    
    return {
        "matches": [
            {
                "profile_id": str(p.id),
                "name": p.name,
                "age": p.age,
                "bio": p.bio
            }
            for p in match_profiles
        ],
        "total": len(match_profiles)
    }

