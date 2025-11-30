"""
Advertisement models for monetizing free users.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AdProvider(str, Enum):
    """Ad network providers."""
    GOOGLE_ADMOB = "google_admob"  # Mobile ads (Flutter)
    GOOGLE_ADSENSE = "google_adsense"  # Web ads (Next.js)
    FACEBOOK_AUDIENCE = "facebook_audience"  # Facebook Audience Network
    CUSTOM = "custom"  # Your own ad campaigns


class AdType(str, Enum):
    """Types of ads."""
    BANNER = "banner"  # Small banner at top/bottom
    INTERSTITIAL = "interstitial"  # Full-screen between actions
    REWARDED = "rewarded"  # Watch ad to get credits/features
    NATIVE = "native"  # Blends with app content


class AdPlacement(str, Enum):
    """Where ads are shown."""
    DISCOVERY_FEED = "discovery_feed"  # Between profile cards
    PROFILE_VIEW = "profile_view"  # On profile pages
    MESSAGES_LIST = "messages_list"  # In conversations list
    AFTER_LIKE = "after_like"  # After liking someone
    AFTER_MATCH = "after_match"  # After getting a match
    APP_OPEN = "app_open"  # When opening app


class AdImpression(SQLModel, table=True):
    """Track ad impressions for analytics and revenue."""
    __tablename__ = "ad_impressions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    
    # Ad details
    ad_provider: AdProvider
    ad_type: AdType
    ad_placement: AdPlacement
    ad_unit_id: str  # Provider's ad unit ID
    
    # Revenue tracking
    estimated_revenue: Optional[float] = None  # In ZAR
    
    # Interaction
    was_clicked: bool = Field(default=False)
    
    # Timestamps
    shown_at: datetime = Field(default_factory=datetime.utcnow)
    clicked_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[dict] = Field(default=None, sa_column_kwargs={"type_": "JSON"})


class AdReward(SQLModel, table=True):
    """Track rewarded ad completions."""
    __tablename__ = "ad_rewards"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    
    # Ad details
    ad_provider: AdProvider
    ad_unit_id: str
    
    # Reward
    reward_type: str  # "credits", "super_like", "boost"
    reward_amount: int  # Number of credits or 1 for features
    
    # Status
    was_granted: bool = Field(default=False)
    
    # Timestamps
    watched_at: datetime = Field(default_factory=datetime.utcnow)
    granted_at: Optional[datetime] = None


class AdConfig(SQLModel, table=True):
    """Configuration for ad placements (admin managed)."""
    __tablename__ = "ad_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Placement details
    placement: AdPlacement
    ad_type: AdType
    ad_provider: AdProvider
    
    # Provider IDs
    admob_unit_id: Optional[str] = None  # For Flutter/Android
    admob_ios_unit_id: Optional[str] = None  # For Flutter/iOS
    adsense_unit_id: Optional[str] = None  # For Next.js
    
    # Frequency control
    show_every_n_views: int = Field(default=5)  # Show ad every N profile views
    min_seconds_between: int = Field(default=30)  # Minimum seconds between ads
    
    # Targeting
    show_to_free_users_only: bool = Field(default=True)
    
    # Status
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
