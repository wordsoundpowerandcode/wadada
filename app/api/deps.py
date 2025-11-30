"""
Authentication Dependencies

This module provides authentication dependencies that verify JWT tokens using
Supabase's JWKS endpoint: https://{SUPABASE_URL}/auth/v1/.well-known/jwks.json

Usage:
    - verify_jwt_token: Core dependency that verifies JWT and returns token data
    - get_current_user_id: Returns Supabase user ID from verified token
    - get_current_profile: Returns Profile object for authenticated user (most common)
    - get_optional_profile: Optional auth - returns Profile if authenticated, None otherwise

Example:
    @router.get("/protected")
    async def protected_route(profile: Profile = Depends(get_current_profile)):
        # User is authenticated and profile is available
        return {"message": f"Hello {profile.name}"}
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.jwt_verification import jwks_service
from app.models.profile import Profile
from sqlalchemy import select
from typing import Optional, Dict

security = HTTPBearer()

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Verify JWT token using Supabase JWKS endpoint.
    This is the core authentication dependency that all protected routes should use.
    
    Returns:
        Decoded JWT payload containing user information
        
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    token = credentials.credentials
    
    # Verify token using JWKS
    decoded_token = jwks_service.verify_token(token)
    
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return decoded_token

async def get_current_user_id(
    token_data: Dict = Depends(verify_jwt_token)
) -> str:
    """
    Extract Supabase user ID from verified JWT token.
    Use this dependency when you only need the user ID.
    
    Returns:
        Supabase user ID (sub claim from JWT)
    """
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

async def get_current_profile(
    token_data: Dict = Depends(verify_jwt_token),
    db: AsyncSession = Depends(get_db)
) -> Profile:
    """
    Verify JWT token and return current user's profile.
    This is the main dependency for routes that need the user's profile.
    
    Returns:
        Profile object for the authenticated user
        
    Raises:
        HTTPException: If profile not found
    """
    supabase_user_id = token_data.get("sub")
    
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get profile from database
    result = await db.execute(
        select(Profile).where(Profile.supabase_user_id == supabase_user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create your profile first."
        )
    
    return profile

async def get_optional_profile(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[Profile]:
    """
    Optional authentication - returns profile if token is valid, None otherwise.
    Use this for routes that work both with and without authentication.
    """
    if not credentials:
        return None
    
    try:
        token_data = await verify_jwt_token(credentials)
        supabase_user_id = token_data.get("sub")
        
        if not supabase_user_id:
            return None
        
        result = await db.execute(
            select(Profile).where(Profile.supabase_user_id == supabase_user_id)
        )
        return result.scalar_one_or_none()
    except HTTPException:
        return None

