from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_profile
from app.models.profile import Profile
from app.services.matching_service import MatchingService
from app.schemas.profile import ProfileResponse
from typing import List

router = APIRouter(prefix="/matches", tags=["matches"])

@router.get("")
async def get_matches(
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """
    Get potential matches for current user.
    Returns ranked list of profiles based on compatibility score.
    """
    matching_service = MatchingService(db)
    matches = await matching_service.find_matches(profile, limit, offset)
    
    return {
        "matches": [
            {
                "profile": ProfileResponse.model_validate(m["profile"]),
                "match_percentage": m["match_percentage"],
                "score": round(m["score"], 2)
            }
            for m in matches
        ],
        "total": len(matches),
        "limit": limit,
        "offset": offset
    }

@router.get("/count")
async def get_match_count(
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db)
):
    """Get total count of potential matches"""
    matching_service = MatchingService(db)
    all_profiles = await matching_service._get_potential_profiles(profile)
    filtered = await matching_service._apply_filters(profile, all_profiles)
    
    return {
        "total_matches": len(filtered)
    }

