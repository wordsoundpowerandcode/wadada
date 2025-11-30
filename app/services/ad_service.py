"""
Ad service for managing advertisements and rewarded ads.
"""
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, Dict
from datetime import datetime, timedelta

from app.models.ad import (
    AdImpression,
    AdReward,
    AdConfig,
    AdProvider,
    AdType,
    AdPlacement
)
from app.models.profile import Profile
from app.models.credit import CreditTransaction, TransactionType
from app.services.credit_service import CreditService


class AdService:
    """Service for managing ads and rewards."""
    
    async def should_show_ad(
        self,
        profile_id: int,
        placement: AdPlacement,
        session: AsyncSession
    ) -> bool:
        """
        Determine if an ad should be shown to the user at this placement.
        """
        # Get user's profile
        result = await session.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return False
        
        # Premium users don't see ads
        if profile.is_premium:
            return False
        
        # Get ad config for this placement
        result = await session.execute(
            select(AdConfig).where(
                AdConfig.placement == placement,
                AdConfig.is_active == True
            )
        )
        ad_config = result.scalar_one_or_none()
        
        if not ad_config:
            return False
        
        # Check frequency - has user seen ad recently?
        min_time = datetime.utcnow() - timedelta(seconds=ad_config.min_seconds_between)
        result = await session.execute(
            select(AdImpression).where(
                AdImpression.profile_id == profile_id,
                AdImpression.ad_placement == placement,
                AdImpression.shown_at >= min_time
            )
        )
        recent_ad = result.scalar_one_or_none()
        
        if recent_ad:
            return False  # Too soon
        
        # Check view count - show every N views
        result = await session.execute(
            select(AdImpression).where(
                AdImpression.profile_id == profile_id,
                AdImpression.ad_placement == placement
            )
        )
        total_views = len(result.scalars().all())
        
        # Show ad if it's time based on frequency
        return total_views % ad_config.show_every_n_views == 0
    
    async def get_ad_config(
        self,
        placement: AdPlacement,
        platform: str,  # "web", "android", "ios"
        session: AsyncSession
    ) -> Optional[Dict]:
        """
        Get ad configuration for a specific placement and platform.
        """
        result = await session.execute(
            select(AdConfig).where(
                AdConfig.placement == placement,
                AdConfig.is_active == True
            )
        )
        ad_config = result.scalar_one_or_none()
        
        if not ad_config:
            return None
        
        # Return appropriate ad unit ID based on platform
        ad_unit_id = None
        if platform == "web":
            ad_unit_id = ad_config.adsense_unit_id
        elif platform == "android":
            ad_unit_id = ad_config.admob_unit_id
        elif platform == "ios":
            ad_unit_id = ad_config.admob_ios_unit_id
        
        if not ad_unit_id:
            return None
        
        return {
            "placement": ad_config.placement,
            "ad_type": ad_config.ad_type,
            "ad_provider": ad_config.ad_provider,
            "ad_unit_id": ad_unit_id,
            "show_every_n_views": ad_config.show_every_n_views
        }
    
    async def record_impression(
        self,
        profile_id: int,
        ad_provider: AdProvider,
        ad_type: AdType,
        ad_placement: AdPlacement,
        ad_unit_id: str,
        session: AsyncSession
    ) -> AdImpression:
        """
        Record that an ad was shown to a user.
        """
        impression = AdImpression(
            profile_id=profile_id,
            ad_provider=ad_provider,
            ad_type=ad_type,
            ad_placement=ad_placement,
            ad_unit_id=ad_unit_id
        )
        
        session.add(impression)
        await session.commit()
        await session.refresh(impression)
        
        return impression
    
    async def record_click(
        self,
        impression_id: int,
        session: AsyncSession
    ) -> bool:
        """
        Record that a user clicked on an ad.
        """
        result = await session.execute(
            select(AdImpression).where(AdImpression.id == impression_id)
        )
        impression = result.scalar_one_or_none()
        
        if not impression:
            return False
        
        impression.was_clicked = True
        impression.clicked_at = datetime.utcnow()
        
        await session.commit()
        return True
    
    async def grant_rewarded_ad_reward(
        self,
        profile_id: int,
        ad_provider: AdProvider,
        ad_unit_id: str,
        reward_type: str,
        reward_amount: int,
        session: AsyncSession
    ) -> Dict:
        """
        Grant reward for watching a rewarded ad.
        """
        # Create reward record
        ad_reward = AdReward(
            profile_id=profile_id,
            ad_provider=ad_provider,
            ad_unit_id=ad_unit_id,
            reward_type=reward_type,
            reward_amount=reward_amount,
            was_granted=True,
            granted_at=datetime.utcnow()
        )
        
        session.add(ad_reward)
        
        # Grant the actual reward
        if reward_type == "credits":
            # Add credits to user's account
            credit_service = CreditService()
            await credit_service.add_credits(
                profile_id=profile_id,
                amount=reward_amount,
                transaction_type=TransactionType.REWARD,
                description=f"Rewarded ad - {reward_amount} credits",
                session=session
            )
        
        elif reward_type == "super_like":
            # Grant super like (you'd implement this in your like service)
            # For now, we'll just record it
            pass
        
        elif reward_type == "boost":
            # Grant profile boost (you'd implement this in your profile service)
            # For now, we'll just record it
            pass
        
        await session.commit()
        
        return {
            "success": True,
            "reward_type": reward_type,
            "reward_amount": reward_amount,
            "message": f"You earned {reward_amount} {reward_type}!"
        }
    
    async def get_user_ad_stats(
        self,
        profile_id: int,
        session: AsyncSession
    ) -> Dict:
        """
        Get ad statistics for a user.
        """
        # Total impressions
        result = await session.execute(
            select(AdImpression).where(AdImpression.profile_id == profile_id)
        )
        impressions = result.scalars().all()
        
        # Total clicks
        clicks = sum(1 for imp in impressions if imp.was_clicked)
        
        # Total rewards
        result = await session.execute(
            select(AdReward).where(AdReward.profile_id == profile_id)
        )
        rewards = result.scalars().all()
        
        total_credits_earned = sum(
            r.reward_amount for r in rewards 
            if r.reward_type == "credits" and r.was_granted
        )
        
        return {
            "total_impressions": len(impressions),
            "total_clicks": clicks,
            "total_rewards_watched": len(rewards),
            "total_credits_earned": total_credits_earned
        }
