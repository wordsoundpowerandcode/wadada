from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict

class SupabaseAuthService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.service_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    async def sign_up(self, email: str, password: str, name: str) -> Dict:
        """Sign up a new user"""
        response = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name
                }
            }
        })
        return response
    
    async def sign_in(self, email: str, password: str) -> Dict:
        """Sign in a user"""
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            user = self.client.auth.get_user(token)
            return user
        except Exception:
            return None
    
    async def get_user(self, token: str) -> Optional[Dict]:
        """Get user from token"""
        return await self.verify_token(token)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by Supabase user ID"""
        try:
            # Use admin API to get user
            response = self.service_client.auth.admin.get_user_by_id(user_id)
            return response
        except Exception:
            return None
    
    def get_oauth_url(self, provider: str, redirect_url: str) -> str:
        """Get OAuth URL for provider (Google, GitHub)"""
        return self.client.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": redirect_url
            }
        }).url
    
    async def get_oauth_user(self, code: str, provider: str) -> Optional[Dict]:
        """Exchange OAuth code for user session"""
        try:
            # This would typically be handled by the callback
            # For now, return None as Supabase handles this client-side
            return None
        except Exception:
            return None

