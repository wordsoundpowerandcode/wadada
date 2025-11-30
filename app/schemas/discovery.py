"""
Pydantic schemas for discovery endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.enums import (
    Gender, 
    RelationshipType, 
    EducationLevel,
    BodyType,
    DrinkingHabit,
    SmokingHabit,
    ChildrenStatus,
    Religion
)
from app.schemas.profile import ProfilePublicResponse


class DiscoveryFilters(BaseModel):
    """Filters for browsing profiles."""
    # Basic filters (available to all users)
    min_age: Optional[int] = Field(None, ge=18, le=100)
    max_age: Optional[int] = Field(None, ge=18, le=100)
    genders: Optional[List[Gender]] = None
    relationship_types: Optional[List[RelationshipType]] = None
    max_distance_km: Optional[int] = Field(None, ge=1, le=500)
    city: Optional[str] = None
    verified_only: bool = False
    
    # Premium filters (only for premium users)
    education_levels: Optional[List[EducationLevel]] = None
    min_height_cm: Optional[int] = Field(None, ge=100, le=250)
    max_height_cm: Optional[int] = Field(None, ge=100, le=250)
    body_types: Optional[List[BodyType]] = None
    drinking_habits: Optional[List[DrinkingHabit]] = None
    smoking_habits: Optional[List[SmokingHabit]] = None
    children_status: Optional[List[ChildrenStatus]] = None
    religions: Optional[List[Religion]] = None
    
    class Config:
        from_attributes = True


class DiscoveryResponse(BaseModel):
    """Response for discovery endpoints."""
    profiles: List[ProfilePublicResponse]
    total_count: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class MatchWithScore(BaseModel):
    """Profile with compatibility score."""
    profile: ProfilePublicResponse
    compatibility_score: float
    match_reasons: List[str] = []
    
    class Config:
        from_attributes = True


class DailyMatchesResponse(BaseModel):
    """Response for daily matches."""
    matches: List[dict]  # List of MatchWithScore-like dicts
    total_count: int
    refreshes_at: datetime
    
    class Config:
        from_attributes = True
