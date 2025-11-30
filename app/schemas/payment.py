"""
Pydantic schemas for payment endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

from app.models.payment import PaymentType, PaymentProvider, PaymentStatus


class CreditPackageResponse(BaseModel):
    """Response for credit package."""
    id: int
    name: str
    credits: int
    price: float
    bonus_credits: int
    is_popular: bool
    total_credits: int = 0
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_credits = self.credits + self.bonus_credits


class PremiumPlanResponse(BaseModel):
    """Response for premium plan."""
    id: int
    name: str
    plan_type: PaymentType
    duration_days: int
    price: float
    original_price: Optional[float] = None
    is_popular: bool
    features: List[str]
    savings: Optional[float] = None
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.original_price:
            self.savings = self.original_price - self.price


class PaymentInitiateRequest(BaseModel):
    """Request to initiate a payment."""
    credit_package_id: Optional[int] = None
    premium_plan_id: Optional[int] = None
    
    # URLs for Ozow (web only)
    success_url: str
    cancel_url: str
    error_url: str
    notify_url: str
    
    class Config:
        from_attributes = True


class PaymentInitiateResponse(BaseModel):
    """Response for payment initiation."""
    payment_id: int
    payment_url: str
    payment_data: Dict[str, str]
    transaction_reference: str
    
    class Config:
        from_attributes = True


class PaymentWebhookData(BaseModel):
    """Ozow webhook data."""
    SiteCode: str
    TransactionId: str
    TransactionReference: str
    Amount: str
    Status: str
    Optional1: Optional[str] = None
    Optional2: Optional[str] = None
    Optional3: Optional[str] = None
    Optional4: Optional[str] = None
    Optional5: Optional[str] = None
    CurrencyCode: str
    IsTest: str
    StatusMessage: Optional[str] = None
    HashCheck: str
    
    class Config:
        from_attributes = True


class IAPVerifyRequest(BaseModel):
    """Request to verify an IAP purchase."""
    payment_type: PaymentType
    
    # For Google Play
    product_id: Optional[str] = None
    purchase_token: Optional[str] = None
    
    # For Apple
    receipt_data: Optional[str] = None
    
    # Credits amount (for credit purchases)
    credits_amount: Optional[int] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Response for payment details."""
    id: int
    profile_id: int
    payment_type: PaymentType
    payment_provider: PaymentProvider
    amount: float
    currency: str
    credits_amount: Optional[int] = None
    status: PaymentStatus
    status_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Response for subscription details."""
    id: int
    profile_id: int
    plan_type: PaymentType
    payment_provider: PaymentProvider
    is_active: bool
    auto_renew: bool
    started_at: datetime
    expires_at: datetime
    cancelled_at: Optional[datetime] = None
    days_remaining: int = 0
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.is_active:
            delta = self.expires_at - datetime.utcnow()
            self.days_remaining = max(0, delta.days)
