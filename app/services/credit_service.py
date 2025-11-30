from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.credit import CreditBalance, CreditTransaction, CreditTransactionType
from app.config import settings
from uuid import UUID
from typing import Optional

class CreditService:
    """Service for managing user credits"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_balance(self, profile_id: UUID) -> int:
        """Get current credit balance for a profile"""
        result = await self.db.execute(
            select(CreditBalance).where(CreditBalance.profile_id == profile_id)
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            # Create balance record if doesn't exist
            balance = CreditBalance(profile_id=profile_id, balance=0)
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)
        
        return balance.balance
    
    async def add_credits(
        self,
        profile_id: UUID,
        amount: int,
        transaction_type: CreditTransactionType,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> bool:
        """Add credits to a profile"""
        # Get or create balance
        result = await self.db.execute(
            select(CreditBalance).where(CreditBalance.profile_id == profile_id)
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            balance = CreditBalance(profile_id=profile_id, balance=0, total_earned=0)
            self.db.add(balance)
        
        # Update balance
        balance.balance += amount
        balance.total_earned += amount
        
        # Create transaction record
        transaction = CreditTransaction(
            profile_id=profile_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id
        )
        self.db.add(transaction)
        
        await self.db.commit()
        return True
    
    async def deduct_credits(
        self,
        profile_id: UUID,
        amount: int,
        transaction_type: CreditTransactionType,
        description: Optional[str] = None
    ) -> bool:
        """Deduct credits from a profile"""
        balance = await self.get_balance(profile_id)
        
        if balance < amount:
            return False
        
        # Get balance record
        result = await self.db.execute(
            select(CreditBalance).where(CreditBalance.profile_id == profile_id)
        )
        balance_record = result.scalar_one()
        
        # Update balance
        balance_record.balance -= amount
        balance_record.total_spent += amount
        
        # Create transaction record
        transaction = CreditTransaction(
            profile_id=profile_id,
            transaction_type=transaction_type,
            amount=-amount,  # Negative for deduction
            description=description
        )
        self.db.add(transaction)
        
        await self.db.commit()
        return True
    
    async def check_and_deduct_credits(
        self,
        profile_id: UUID,
        transaction_type: CreditTransactionType
    ) -> bool:
        """Check if user has enough credits and deduct if yes"""
        cost = self._get_credit_cost(transaction_type)
        
        if cost == 0:
            return True  # Free action
        
        balance = await self.get_balance(profile_id)
        
        if balance < cost:
            return False
        
        return await self.deduct_credits(
            profile_id,
            cost,
            transaction_type,
            description=f"Used credits for {transaction_type.value}"
        )
    
    def _get_credit_cost(self, transaction_type: CreditTransactionType) -> int:
        """Get credit cost for a transaction type"""
        costs = {
            CreditTransactionType.MESSAGE_UNMATCHED: settings.CREDIT_COST_MESSAGE_UNMATCHED,
            CreditTransactionType.SUPER_LIKE: settings.CREDIT_COST_SUPER_LIKE,
            CreditTransactionType.VIEW_LIKERS: settings.CREDIT_COST_VIEW_LIKERS,
            CreditTransactionType.BOOST: settings.CREDIT_COST_BOOST,
        }
        return costs.get(transaction_type, 0)
    
    async def get_transaction_history(
        self,
        profile_id: UUID,
        limit: int = 50
    ):
        """Get credit transaction history"""
        result = await self.db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.profile_id == profile_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

