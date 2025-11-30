from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime, Integer, String
from datetime import datetime
from typing import Optional
import uuid
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

class CreditTransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    MESSAGE_UNMATCHED = "message_unmatched"
    SUPER_LIKE = "super_like"
    VIEW_LIKERS = "view_likers"
    BOOST = "boost"
    REFUND = "refund"
    BONUS = "bonus"

class CreditTransaction(SQLModel, table=True):
    __tablename__ = "credit_transactions"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    transaction_type: CreditTransactionType
    amount: int  # Positive for credits added, negative for credits used
    description: Optional[str] = None
    reference_id: Optional[str] = None  # For payment references
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow))
    
    # Relationships
    profile: Optional["Profile"] = Relationship()

class CreditBalance(SQLModel, table=True):
    __tablename__ = "credit_balances"
    
    profile_id: uuid.UUID = Field(foreign_key="profiles.id", primary_key=True)
    balance: int = Field(default=0)  # Current credit balance
    total_earned: int = Field(default=0)  # Total credits ever earned
    total_spent: int = Field(default=0)  # Total credits ever spent
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    profile: Optional["Profile"] = Relationship()

