from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import DateTime, Integer, Float, ARRAY, String
from datetime import datetime, date
from typing import Optional, List
import uuid
from typing import TYPE_CHECKING
from app.models.enums import (
    RelationshipType, Gender, Sexuality, RelationshipStatus,
    DrinkingHabit, SmokingHabit, BodyType, EducationLevel,
    Religion, ChildrenStatus, PetPreference, PersonalityType,
    LifestylePreference, CommunicationStyle
)

if TYPE_CHECKING:
    from app.models.media import UserMedia
    from app.models.conversation import ConversationParticipant, Conversation
    from app.models.message import Message, MessageReaction
    from app.models.like import Like
    from app.models.profile_view import ProfileView
    from app.models.verification import Verification
    from app.models.credit import CreditBalance, CreditTransaction

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"
    
    # Basic Info (existing)
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    supabase_user_id: str = Field(unique=True, index=True)
    name: str
    email: str = Field(index=True)
    bio: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Demographics
    date_of_birth: Optional[date] = None  # Calculate age from this
    age: Optional[int] = None  # Computed field or stored
    gender: Optional[Gender] = None
    sexuality: Optional[Sexuality] = None
    height_cm: Optional[int] = None  # Height in centimeters
    body_type: Optional[BodyType] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    latitude: Optional[float] = None  # For distance-based matching
    longitude: Optional[float] = None  # For distance-based matching
    timezone: Optional[str] = None
    
    # Relationship & Dating
    relationship_status: Optional[RelationshipStatus] = None
    relationship_type_seeking: Optional[RelationshipType] = None
    dating_goals_timeline: Optional[str] = None  # "asap", "within_year", "no_rush", etc.
    
    # Work & Education
    occupation: Optional[str] = None
    company: Optional[str] = None
    education_level: Optional[EducationLevel] = None
    school: Optional[str] = None
    field_of_study: Optional[str] = None
    
    # Lifestyle & Habits
    drinking_habit: Optional[DrinkingHabit] = None
    smoking_habit: Optional[SmokingHabit] = None
    exercise_frequency: Optional[str] = None  # "daily", "few_times_week", "weekly", "rarely", "never"
    diet_preference: Optional[str] = None  # "vegetarian", "vegan", "omnivore", "keto", etc.
    
    # Family & Pets
    children_status: Optional[ChildrenStatus] = None
    wants_more_children: Optional[bool] = None
    pet_preference: Optional[PetPreference] = None
    has_pets: Optional[bool] = None
    pet_types: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["dog", "cat", "bird"]
    
    # Personal Values
    religion: Optional[Religion] = None
    religion_importance: Optional[str] = None  # "very_important", "somewhat", "not_important"
    political_views: Optional[str] = None  # "liberal", "moderate", "conservative", "apolitical", etc.
    values: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["family", "career", "adventure"]
    
    # Personality & Interests
    personality_type: Optional[PersonalityType] = None
    lifestyle_preference: Optional[LifestylePreference] = None
    communication_style: Optional[CommunicationStyle] = None
    hobbies: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["reading", "hiking", "cooking"]
    interests: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # More specific interests
    favorite_activities: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    languages_spoken: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["english", "spanish"]
    
    # Match Preferences (what they're looking for)
    preferred_age_min: Optional[int] = None
    preferred_age_max: Optional[int] = None
    preferred_genders: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # Can match multiple
    preferred_relationship_types: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    max_distance_km: Optional[int] = None  # Maximum distance for matches in kilometers
    deal_breakers: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["smoking", "no_kids"]
    must_haves: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # ["same_religion", "similar_values"]
    
    # Additional Matching Fields
    energy_level: Optional[str] = None  # "low", "medium", "high"
    social_activity_level: Optional[str] = None  # "very_social", "moderate", "prefer_small_groups", "mostly_solo"
    travel_frequency: Optional[str] = None  # "frequently", "occasionally", "rarely", "never"
    work_life_balance: Optional[str] = None  # "work_focused", "balanced", "life_focused"
    financial_situation: Optional[str] = None  # "stable", "growing", "comfortable", "prefer_not_to_say"
    
    # Compatibility & Matching
    profile_completion_percentage: Optional[int] = Field(default=0)  # 0-100
    last_active_at: Optional[datetime] = None  # For showing "active now" or "active X hours ago"
    is_verified: bool = False  # Profile verification status
    is_premium: bool = False  # Premium membership
    match_score_weight_preferences: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # User-defined weights
    
    # Privacy & Discovery
    is_discoverable: bool = True  # Can be found in searches
    show_age: bool = True
    show_distance: bool = True
    show_last_active: bool = True
    
    # Verification
    is_photo_verified: bool = False
    is_video_verified: bool = False
    verification_status: Optional[str] = None  # "pending", "approved", "rejected"
    
    # Credits & Premium
    credit_balance: int = Field(default=0)
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    
    # Analytics
    profile_views_count: int = Field(default=0)
    likes_received_count: int = Field(default=0)
    matches_count: int = Field(default=0)
    
    # Relationships (existing)
    intro_media: Optional["UserMedia"] = Relationship(
        back_populates="profile",
        sa_relationship_kwargs={
            "foreign_keys": "UserMedia.profile_id",
            "primaryjoin": "and_(Profile.id == UserMedia.profile_id, UserMedia.is_intro_media == True)",
            "uselist": False
        }
    )
    media: List["UserMedia"] = Relationship(back_populates="profile")
    conversations: List["ConversationParticipant"] = Relationship(
        back_populates="profile",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Many-to-many relationship through association table
    conversation_list: List["Conversation"] = Relationship(
        back_populates="participants",
        sa_relationship_kwargs={"secondary": "conversation_participants"}
    )
    sent_messages: List["Message"] = Relationship(back_populates="sender")
    message_reactions: List["MessageReaction"] = Relationship(
        back_populates="profile",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Likes
    likes_sent: List["Like"] = Relationship(
        foreign_keys="Like.liker_id",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes_received: List["Like"] = Relationship(
        foreign_keys="Like.liked_id",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Profile views
    profile_views_sent: List["ProfileView"] = Relationship(
        foreign_keys="ProfileView.viewer_id",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    profile_views_received: List["ProfileView"] = Relationship(
        foreign_keys="ProfileView.viewed_id",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Verification
    verification: Optional["Verification"] = Relationship(
        back_populates="profile",
        uselist=False
    )
    # Credits
    credit_balance_record: Optional["CreditBalance"] = Relationship(
        back_populates="profile",
        uselist=False
    )
    credit_transactions: List["CreditTransaction"] = Relationship(
        back_populates="profile",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
