from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from app.schemas.media import MediaResponse
from app.models.enums import (
    RelationshipType, Gender, Sexuality, RelationshipStatus,
    DrinkingHabit, SmokingHabit, BodyType, EducationLevel,
    Religion, ChildrenStatus, PetPreference, PersonalityType,
    LifestylePreference, CommunicationStyle
)

class ProfileBase(BaseModel):
    name: str
    email: EmailStr
    bio: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    # Demographics
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    sexuality: Optional[Sexuality] = None
    height_cm: Optional[int] = None
    body_type: Optional[BodyType] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    # Relationship & Dating
    relationship_status: Optional[RelationshipStatus] = None
    relationship_type_seeking: Optional[RelationshipType] = None
    dating_goals_timeline: Optional[str] = None
    # Work & Education
    occupation: Optional[str] = None
    company: Optional[str] = None
    education_level: Optional[EducationLevel] = None
    school: Optional[str] = None
    field_of_study: Optional[str] = None
    # Lifestyle & Habits
    drinking_habit: Optional[DrinkingHabit] = None
    smoking_habit: Optional[SmokingHabit] = None
    exercise_frequency: Optional[str] = None
    diet_preference: Optional[str] = None
    # Family & Pets
    children_status: Optional[ChildrenStatus] = None
    wants_more_children: Optional[bool] = None
    pet_preference: Optional[PetPreference] = None
    has_pets: Optional[bool] = None
    pet_types: Optional[List[str]] = None
    # Personal Values
    religion: Optional[Religion] = None
    religion_importance: Optional[str] = None
    political_views: Optional[str] = None
    values: Optional[List[str]] = None
    # Personality & Interests
    personality_type: Optional[PersonalityType] = None
    lifestyle_preference: Optional[LifestylePreference] = None
    communication_style: Optional[CommunicationStyle] = None
    hobbies: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    favorite_activities: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    # Match Preferences
    preferred_age_min: Optional[int] = None
    preferred_age_max: Optional[int] = None
    preferred_genders: Optional[List[str]] = None
    preferred_relationship_types: Optional[List[str]] = None
    max_distance_km: Optional[int] = None
    deal_breakers: Optional[List[str]] = None
    must_haves: Optional[List[str]] = None
    # Additional Matching Fields
    energy_level: Optional[str] = None
    social_activity_level: Optional[str] = None
    travel_frequency: Optional[str] = None
    work_life_balance: Optional[str] = None
    financial_situation: Optional[str] = None
    # Privacy & Discovery
    is_discoverable: Optional[bool] = None
    show_age: Optional[bool] = None
    show_distance: Optional[bool] = None
    show_last_active: Optional[bool] = None
    # Match weights
    match_score_weight_preferences: Optional[dict] = None

class ProfileResponse(ProfileBase):
    id: UUID
    supabase_user_id: str
    intro_media: Optional[MediaResponse] = None
    # Demographics
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    sexuality: Optional[Sexuality] = None
    height_cm: Optional[int] = None
    body_type: Optional[BodyType] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    # Relationship & Dating
    relationship_status: Optional[RelationshipStatus] = None
    relationship_type_seeking: Optional[RelationshipType] = None
    dating_goals_timeline: Optional[str] = None
    # Work & Education
    occupation: Optional[str] = None
    company: Optional[str] = None
    education_level: Optional[EducationLevel] = None
    school: Optional[str] = None
    field_of_study: Optional[str] = None
    # Lifestyle & Habits
    drinking_habit: Optional[DrinkingHabit] = None
    smoking_habit: Optional[SmokingHabit] = None
    exercise_frequency: Optional[str] = None
    diet_preference: Optional[str] = None
    # Family & Pets
    children_status: Optional[ChildrenStatus] = None
    wants_more_children: Optional[bool] = None
    pet_preference: Optional[PetPreference] = None
    has_pets: Optional[bool] = None
    pet_types: Optional[List[str]] = None
    # Personal Values
    religion: Optional[Religion] = None
    religion_importance: Optional[str] = None
    political_views: Optional[str] = None
    values: Optional[List[str]] = None
    # Personality & Interests
    personality_type: Optional[PersonalityType] = None
    lifestyle_preference: Optional[LifestylePreference] = None
    communication_style: Optional[CommunicationStyle] = None
    hobbies: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    favorite_activities: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    # Match Preferences
    preferred_age_min: Optional[int] = None
    preferred_age_max: Optional[int] = None
    preferred_genders: Optional[List[str]] = None
    preferred_relationship_types: Optional[List[str]] = None
    max_distance_km: Optional[int] = None
    deal_breakers: Optional[List[str]] = None
    must_haves: Optional[List[str]] = None
    # Additional Matching Fields
    energy_level: Optional[str] = None
    social_activity_level: Optional[str] = None
    travel_frequency: Optional[str] = None
    work_life_balance: Optional[str] = None
    financial_situation: Optional[str] = None
    # Compatibility & Matching
    profile_completion_percentage: Optional[int] = None
    last_active_at: Optional[datetime] = None
    is_verified: bool = False
    is_premium: bool = False
    # Privacy & Discovery
    is_discoverable: bool = True
    show_age: bool = True
    show_distance: bool = True
    show_last_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
