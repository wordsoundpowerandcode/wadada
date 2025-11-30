from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, TokenResponse
from app.schemas.profile import ProfileResponse
from app.services.supabase_auth import SupabaseAuthService
from app.models.profile import Profile
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = SupabaseAuthService()

@router.post("/signup", response_model=TokenResponse)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Sign up a new user"""
    # Check if profile exists (user already registered)
    result = await db.execute(
        select(Profile).where(Profile.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user in Supabase Auth
    supabase_response = await auth_service.sign_up(
        user_data.email,
        user_data.password,
        user_data.name
    )
    
    if not supabase_response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    # Create profile in database linked to Supabase Auth user
    new_profile = Profile(
        supabase_user_id=supabase_response.user.id,
        email=user_data.email,
        name=user_data.name
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    return TokenResponse(
        access_token=supabase_response.session.access_token,
        user=ProfileResponse.model_validate(new_profile)
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    supabase_response = await auth_service.sign_in(email, password)
    
    if not supabase_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get profile from database
    result = await db.execute(
        select(Profile).where(Profile.supabase_user_id == supabase_response.user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # Profile doesn't exist, create it (edge case - user exists in Supabase but not in our DB)
        profile = Profile(
            supabase_user_id=supabase_response.user.id,
            email=supabase_response.user.email,
            name=supabase_response.user.user_metadata.get("name", "User")
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    
    return TokenResponse(
        access_token=supabase_response.session.access_token,
        user=ProfileResponse.model_validate(profile)
    )

@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login flow"""
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider. Supported: google, github"
        )
    
    # Get redirect URL from request
    redirect_url = str(request.url).replace("/oauth/", "/oauth/callback/")
    redirect_url = redirect_url.replace(f"/{provider}", f"/{provider}")
    
    oauth_url = auth_service.get_oauth_url(provider, redirect_url)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=oauth_url)

@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback"""
    # Note: Supabase handles OAuth callbacks client-side typically
    # This endpoint would need to be adjusted based on your OAuth flow
    # For now, return a message indicating the user should use the client SDK
    return {
        "message": "OAuth callback received. Please use Supabase client SDK for OAuth flow.",
        "provider": provider,
        "code": code
    }

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh JWT token"""
    # Supabase handles token refresh client-side
    # This endpoint can be used if you want server-side refresh
    try:
        from supabase import create_client
        from app.config import settings
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        response = client.auth.refresh_session(refresh_token)
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )

