import jwt
from jwt import PyJWKClient
from app.config import settings
from typing import Optional, Dict

class JWKSVerificationService:
    """Service for verifying JWT tokens using Supabase JWKS endpoint"""
    
    def __init__(self):
        # Construct JWKS URL from Supabase URL
        self.jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        # Cache the JWKS client
        self._jwks_client: Optional[PyJWKClient] = None
    
    @property
    def jwks_client(self) -> PyJWKClient:
        """Get or create JWKS client (cached)"""
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self.jwks_url)
        return self._jwks_client
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token using JWKS and return decoded payload
        
        Returns:
            Dict with user information if token is valid, None otherwise
        """
        try:
            # Get the signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify the token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "HS256"],  # Supabase uses ES256, but support both
                audience=settings.JWT_AUDIENCE,  # Supabase JWT audience
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                }
            )
            
            return decoded_token
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID (sub claim) from verified token
        
        Returns:
            Supabase user ID if token is valid, None otherwise
        """
        decoded = self.verify_token(token)
        if decoded:
            return decoded.get("sub")  # 'sub' is the user ID in Supabase JWT
        return None
    
    def get_user_email_from_token(self, token: str) -> Optional[str]:
        """
        Extract user email from verified token
        
        Returns:
            User email if token is valid, None otherwise
        """
        decoded = self.verify_token(token)
        if decoded:
            return decoded.get("email")
        return None

# Global instance
jwks_service = JWKSVerificationService()

