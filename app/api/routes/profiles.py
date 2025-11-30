from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile, get_current_user_id
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.models.profile import Profile
from sqlalchemy import select
from uuid import UUID

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    supabase_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create user profile (called after signup if profile wasn't created)"""
    # Check if profile exists
    result = await db.execute(
        select(Profile).where(Profile.supabase_user_id == supabase_user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists"
        )
    
    # Get user info from Supabase Auth
    from app.services.supabase_auth import SupabaseAuthService
    auth_service = SupabaseAuthService()
    user_data = await auth_service.get_user_by_id(supabase_user_id)
    
    # Extract email and name from user_data or use provided data
    email = profile_data.email
    name = profile_data.name
    
    if user_data and hasattr(user_data, 'user'):
        email = email or user_data.user.email
        name = name or user_data.user.user_metadata.get("name", "User")
    
    new_profile = Profile(
        supabase_user_id=supabase_user_id,
        email=email,
        name=name,
        bio=profile_data.bio
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    return ProfileResponse.model_validate(new_profile)

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    profile: Profile = Depends(get_current_profile)
):
    """Get current user's profile"""
    return ProfileResponse.model_validate(profile)

@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    from datetime import datetime
    
    # Update basic fields
    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    
    # Update all other fields from ProfileUpdate
    update_fields = [
        'date_of_birth', 'age', 'gender', 'sexuality', 'height_cm', 'body_type',
        'current_city', 'current_country', 'latitude', 'longitude', 'timezone',
        'relationship_status', 'relationship_type_seeking', 'dating_goals_timeline',
        'occupation', 'company', 'education_level', 'school', 'field_of_study',
        'drinking_habit', 'smoking_habit', 'exercise_frequency', 'diet_preference',
        'children_status', 'wants_more_children', 'pet_preference', 'has_pets', 'pet_types',
        'religion', 'religion_importance', 'political_views', 'values',
        'personality_type', 'lifestyle_preference', 'communication_style',
        'hobbies', 'interests', 'favorite_activities', 'languages_spoken',
        'preferred_age_min', 'preferred_age_max', 'preferred_genders',
        'preferred_relationship_types', 'max_distance_km', 'deal_breakers', 'must_haves',
        'energy_level', 'social_activity_level', 'travel_frequency',
        'work_life_balance', 'financial_situation',
        'is_discoverable', 'show_age', 'show_distance', 'show_last_active',
        'match_score_weight_preferences'
    ]
    
    for field in update_fields:
        value = getattr(profile_data, field, None)
        if value is not None:
            setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    
    # Update profile completion percentage
    profile.profile_completion_percentage = calculate_profile_completion(profile)
    
    await db.commit()
    await db.refresh(profile)
    
    return ProfileResponse.model_validate(profile)

def calculate_profile_completion(profile: Profile) -> int:
    """Calculate profile completion percentage"""
    total_fields = 30  # Total number of important fields
    completed_fields = 0
    
    # Basic info
    if profile.name: completed_fields += 1
    if profile.bio: completed_fields += 1
    if profile.intro_media: completed_fields += 1
    
    # Demographics
    if profile.age or profile.date_of_birth: completed_fields += 1
    if profile.gender: completed_fields += 1
    if profile.height_cm: completed_fields += 1
    if profile.current_city: completed_fields += 1
    
    # Relationship
    if profile.relationship_type_seeking: completed_fields += 1
    
    # Work & Education
    if profile.occupation: completed_fields += 1
    if profile.education_level: completed_fields += 1
    
    # Lifestyle
    if profile.drinking_habit: completed_fields += 1
    if profile.smoking_habit: completed_fields += 1
    if profile.exercise_frequency: completed_fields += 1
    
    # Family
    if profile.children_status: completed_fields += 1
    if profile.pet_preference: completed_fields += 1
    
    # Values
    if profile.religion: completed_fields += 1
    if profile.values: completed_fields += 1
    
    # Personality
    if profile.personality_type: completed_fields += 1
    if profile.lifestyle_preference: completed_fields += 1
    if profile.communication_style: completed_fields += 1
    
    # Interests
    if profile.hobbies: completed_fields += 1
    if profile.interests: completed_fields += 1
    
    # Preferences
    if profile.preferred_age_min and profile.preferred_age_max: completed_fields += 1
    if profile.preferred_genders: completed_fields += 1
    if profile.max_distance_km: completed_fields += 1
    
    # Additional
    if profile.energy_level: completed_fields += 1
    if profile.social_activity_level: completed_fields += 1
    if profile.travel_frequency: completed_fields += 1
    if profile.work_life_balance: completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a user's public profile"""
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileResponse.model_validate(profile)

