"""
Discovery API routes for finding matches.
Includes daily matches, browse with filters, nearby profiles, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_, or_, func
from typing import Optional, List
from datetime import datetime, timedelta
import random

from app.database import get_session
from app.api.deps import get_current_user
from app.models.profile import Profile
from app.models.like import Like
from app.models.enums import Gender, RelationshipType
from app.services.matching_service import MatchingService
from app.schemas.profile import ProfilePublicResponse
from app.schemas.discovery import (
    DiscoveryFilters,
    DiscoveryResponse,
    DailyMatchesResponse
)

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/daily-matches", response_model=DailyMatchesResponse)
async def get_daily_matches(
    limit: int = Query(default=20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    matching_service: MatchingService = Depends()
):
    """
    Get curated daily matches for the user.
    Returns 10-20 high-quality matches based on compatibility.
    Refreshes daily.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get profiles the user has already liked or passed on today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(Like.liked_id).where(
            Like.liker_id == profile.id,
            Like.created_at >= today_start
        )
    )
    seen_today = [row[0] for row in result.all()]
    
    # Get potential matches
    matches = await matching_service.get_potential_matches(
        profile=profile,
        session=session,
        limit=limit * 2,  # Get more to filter out seen profiles
        exclude_profile_ids=seen_today
    )
    
    # Filter out profiles seen today
    filtered_matches = [m for m in matches if m["profile"].id not in seen_today]
    
    # Limit to requested amount
    daily_matches = filtered_matches[:limit]
    
    # Convert to response format
    match_profiles = []
    for match in daily_matches:
        profile_data = ProfilePublicResponse.from_orm(match["profile"])
        match_profiles.append({
            "profile": profile_data,
            "compatibility_score": match["score"],
            "match_reasons": match.get("reasons", [])
        })
    
    return DailyMatchesResponse(
        matches=match_profiles,
        total_count=len(match_profiles),
        refreshes_at=today_start + timedelta(days=1)
    )


@router.post("/browse", response_model=DiscoveryResponse)
async def browse_profiles(
    filters: DiscoveryFilters,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Browse profiles with advanced filters.
    Premium users get access to more filters.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Build query
    query = select(Profile).where(
        Profile.id != user_profile.id,
        Profile.is_discoverable == True
    )
    
    # Apply filters
    if filters.min_age:
        query = query.where(Profile.age >= filters.min_age)
    
    if filters.max_age:
        query = query.where(Profile.age <= filters.max_age)
    
    if filters.genders:
        query = query.where(Profile.gender.in_(filters.genders))
    
    if filters.relationship_types:
        query = query.where(Profile.relationship_type_seeking.in_(filters.relationship_types))
    
    if filters.max_distance_km and user_profile.latitude and user_profile.longitude:
        # Calculate distance using Haversine formula
        # Note: This is approximate. For production, use PostGIS
        lat_diff = func.abs(Profile.latitude - user_profile.latitude)
        lon_diff = func.abs(Profile.longitude - user_profile.longitude)
        # Rough approximation: 1 degree ≈ 111 km
        distance = func.sqrt(
            func.pow(lat_diff * 111, 2) + 
            func.pow(lon_diff * 111 * func.cos(func.radians(user_profile.latitude)), 2)
        )
        query = query.where(distance <= filters.max_distance_km)
    
    if filters.city:
        query = query.where(Profile.current_city.ilike(f"%{filters.city}%"))
    
    if filters.verified_only:
        query = query.where(
            or_(
                Profile.is_photo_verified == True,
                Profile.is_video_verified == True
            )
        )
    
    # Premium filters (only for premium users)
    if user_profile.is_premium:
        if filters.education_levels:
            query = query.where(Profile.education_level.in_(filters.education_levels))
        
        if filters.min_height_cm:
            query = query.where(Profile.height_cm >= filters.min_height_cm)
        
        if filters.max_height_cm:
            query = query.where(Profile.height_cm <= filters.max_height_cm)
        
        if filters.body_types:
            query = query.where(Profile.body_type.in_(filters.body_types))
        
        if filters.drinking_habits:
            query = query.where(Profile.drinking_habit.in_(filters.drinking_habits))
        
        if filters.smoking_habits:
            query = query.where(Profile.smoking_habit.in_(filters.smoking_habits))
        
        if filters.children_status:
            query = query.where(Profile.children_status.in_(filters.children_status))
        
        if filters.religions:
            query = query.where(Profile.religion.in_(filters.religions))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    total_count = result.scalar_one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()
    
    # Convert to response format
    profile_responses = [ProfilePublicResponse.from_orm(p) for p in profiles]
    
    return DiscoveryResponse(
        profiles=profile_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/nearby", response_model=DiscoveryResponse)
async def get_nearby_profiles(
    radius_km: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get profiles near the user's location (South Africa specific).
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not user_profile.latitude or not user_profile.longitude:
        raise HTTPException(
            status_code=400,
            detail="Location not set. Please update your profile with location."
        )
    
    # Query nearby profiles
    # Using approximate distance calculation
    lat_diff = func.abs(Profile.latitude - user_profile.latitude)
    lon_diff = func.abs(Profile.longitude - user_profile.longitude)
    distance = func.sqrt(
        func.pow(lat_diff * 111, 2) + 
        func.pow(lon_diff * 111 * func.cos(func.radians(user_profile.latitude)), 2)
    )
    
    query = select(Profile).where(
        Profile.id != user_profile.id,
        Profile.is_discoverable == True,
        Profile.latitude.isnot(None),
        Profile.longitude.isnot(None),
        distance <= radius_km
    ).order_by(distance)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    total_count = result.scalar_one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()
    
    # Convert to response format
    profile_responses = [ProfilePublicResponse.from_orm(p) for p in profiles]
    
    return DiscoveryResponse(
        profiles=profile_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/recently-active", response_model=DiscoveryResponse)
async def get_recently_active(
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get recently active profiles.
    Shows profiles that were active in the last X hours.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Query recently active profiles
    query = select(Profile).where(
        Profile.id != user_profile.id,
        Profile.is_discoverable == True,
        Profile.last_active_at >= cutoff_time
    ).order_by(Profile.last_active_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    total_count = result.scalar_one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()
    
    # Convert to response format
    profile_responses = [ProfilePublicResponse.from_orm(p) for p in profiles]
    
    return DiscoveryResponse(
        profiles=profile_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/new-profiles", response_model=DiscoveryResponse)
async def get_new_profiles(
    days: int = Query(default=7, ge=1, le=30),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get new profiles that joined recently.
    Shows profiles created in the last X days.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    # Query new profiles
    query = select(Profile).where(
        Profile.id != user_profile.id,
        Profile.is_discoverable == True,
        Profile.created_at >= cutoff_time
    ).order_by(Profile.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    total_count = result.scalar_one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()
    
    # Convert to response format
    profile_responses = [ProfilePublicResponse.from_orm(p) for p in profiles]
    
    return DiscoveryResponse(
        profiles=profile_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/random", response_model=DiscoveryResponse)
async def get_random_profiles(
    limit: int = Query(default=20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get random profiles for exploration.
    Good for when users want to see something different.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Query random profiles
    # Using ORDER BY RANDOM() - not ideal for large datasets
    # For production, consider using a better random sampling method
    query = select(Profile).where(
        Profile.id != user_profile.id,
        Profile.is_discoverable == True
    ).order_by(func.random()).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    profiles = result.scalars().all()
    
    # Convert to response format
    profile_responses = [ProfilePublicResponse.from_orm(p) for p in profiles]
    
    return DiscoveryResponse(
        profiles=profile_responses,
        total_count=len(profile_responses),
        skip=0,
        limit=limit
    )
