"""
Advertisement API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional

from app.database import get_session
from app.api.deps import get_current_user
from app.models.profile import Profile
from app.models.ad import AdProvider, AdType, AdPlacement
from app.services.ad_service import AdService
from sqlmodel import select

router = APIRouter(prefix="/ads", tags=["ads"])


@router.get("/should-show/{placement}")
async def should_show_ad(
    placement: AdPlacement,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Check if an ad should be shown at this placement.
    Returns ad configuration if yes, null if no.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    ad_service = AdService()
    
    # Check if ad should be shown
    should_show = await ad_service.should_show_ad(
        profile_id=profile.id,
        placement=placement,
        session=session
    )
    
    if not should_show:
        return {"should_show": False, "ad_config": None}
    
    # Get ad config for user's platform
    # You can pass platform as query param
    # For now, we'll default to web
    ad_config = await ad_service.get_ad_config(
        placement=placement,
        platform="web",  # or get from query param
        session=session
    )
    
    return {
        "should_show": True,
        "ad_config": ad_config
    }


@router.post("/impression")
async def record_ad_impression(
    ad_provider: AdProvider,
    ad_type: AdType,
    ad_placement: AdPlacement,
    ad_unit_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Record that an ad was shown to the user.
    Call this when ad is displayed.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    ad_service = AdService()
    
    impression = await ad_service.record_impression(
        profile_id=profile.id,
        ad_provider=ad_provider,
        ad_type=ad_type,
        ad_placement=ad_placement,
        ad_unit_id=ad_unit_id,
        session=session
    )
    
    return {
        "success": True,
        "impression_id": impression.id
    }


@router.post("/click/{impression_id}")
async def record_ad_click(
    impression_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Record that user clicked on an ad.
    """
    ad_service = AdService()
    
    success = await ad_service.record_click(
        impression_id=impression_id,
        session=session
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Impression not found")
    
    return {"success": True}


@router.post("/rewarded/complete")
async def complete_rewarded_ad(
    ad_provider: AdProvider,
    ad_unit_id: str,
    reward_type: str,
    reward_amount: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Grant reward after user watches a rewarded ad.
    
    Reward types:
    - "credits": Grant credits
    - "super_like": Grant 1 super like
    - "boost": Grant 1 profile boost
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    ad_service = AdService()
    
    result = await ad_service.grant_rewarded_ad_reward(
        profile_id=profile.id,
        ad_provider=ad_provider,
        ad_unit_id=ad_unit_id,
        reward_type=reward_type,
        reward_amount=reward_amount,
        session=session
    )
    
    return result


@router.get("/stats")
async def get_ad_stats(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user's ad statistics.
    Shows how many ads they've seen and rewards earned.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    ad_service = AdService()
    
    stats = await ad_service.get_user_ad_stats(
        profile_id=profile.id,
        session=session
    )
    
    return stats
