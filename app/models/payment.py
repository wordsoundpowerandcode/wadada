"""
Payment integration models for credits and premium subscriptions.
Supports Ozow (for web/Next.js) and In-App Purchases (for Flutter).
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentProvider(str, Enum):
    """Payment provider types."""
    OZOW = "ozow"  # For Next.js web app
    GOOGLE_PLAY = "google_play"  # For Android IAP
    APPLE_IAP = "apple_iap"  # For iOS IAP


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    """Type of payment."""
    CREDITS = "credits"
    PREMIUM_DAILY = "premium_daily"
    PREMIUM_WEEKLY = "premium_weekly"
    PREMIUM_MONTHLY = "premium_monthly"
    PREMIUM_YEARLY = "premium_yearly"


class Payment(SQLModel, table=True):
    """Payment transaction record."""
    __tablename__ = "payments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    
    # Payment details
    payment_type: PaymentType
    payment_provider: PaymentProvider
    amount: float  # Amount in ZAR
    currency: str = Field(default="ZAR")
    
    # Credits (if applicable)
    credits_amount: Optional[int] = None
    
    # Provider-specific IDs
    ozow_transaction_id: Optional[str] = Field(default=None, index=True)
    ozow_site_code: Optional[str] = None
    google_play_order_id: Optional[str] = Field(default=None, index=True)
    google_play_purchase_token: Optional[str] = None
    apple_transaction_id: Optional[str] = Field(default=None, index=True)
    apple_receipt_data: Optional[str] = None
    
    # Status
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    status_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[dict] = Field(default=None, sa_column_kwargs={"type_": "JSON"})


class Subscription(SQLModel, table=True):
    """Premium subscription record."""
    __tablename__ = "subscriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True, unique=True)
    
    # Subscription details
    plan_type: PaymentType  # premium_monthly or premium_yearly
    payment_provider: PaymentProvider
    
    # Status
    is_active: bool = Field(default=True)
    auto_renew: bool = Field(default=True)
    
    # Dates
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    cancelled_at: Optional[datetime] = None
    
    # Provider-specific subscription IDs
    ozow_subscription_id: Optional[str] = None
    google_play_subscription_id: Optional[str] = None
    apple_subscription_id: Optional[str] = None
    
    # Payment reference
    last_payment_id: Optional[int] = Field(default=None, foreign_key="payments.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreditPackage(SQLModel, table=True):
    """Available credit packages for purchase."""
    __tablename__ = "credit_packages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Package details
    name: str  # e.g., "Starter Pack", "Popular Pack", "Best Value"
    credits: int  # Number of credits
    price: float  # Price in ZAR
    
    # Bonus
    bonus_credits: int = Field(default=0)  # Extra credits for this package
    
    # Display
    is_popular: bool = Field(default=False)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PremiumPlan(SQLModel, table=True):
    """Available premium subscription plans."""
    __tablename__ = "premium_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Plan details
    name: str  # e.g., "Monthly Premium", "Yearly Premium"
    plan_type: PaymentType
    duration_days: int  # 30 for monthly, 365 for yearly
    price: float  # Price in ZAR
    
    # Discount
    original_price: Optional[float] = None  # For showing savings
    
    # Display
    is_popular: bool = Field(default=False)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    
    # Features (JSON array of feature descriptions)
    features: list = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
