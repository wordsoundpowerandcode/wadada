from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT
    JWT_SECRET: str
    JWT_AUDIENCE: str = "authenticated"  # Supabase JWT audience
    
    # Storage
    STORAGE_BUCKET: str = "user-media"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/quicktime"
    ALLOWED_AUDIO_TYPES: str = "audio/mpeg,audio/mp3,audio/wav"
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # Content Moderation
    ENABLE_MODERATION: bool = False
    MODERATION_PROVIDER: str = "openai"  # openai, perspective
    
    # AI Services (for icebreakers)
    AI_PROVIDER: str = "openai"  # openai, gemini, deepseek
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # Credits & Pricing (in ZAR)
    CREDIT_COST_MESSAGE_UNMATCHED: int = 10
    CREDIT_COST_SUPER_LIKE: int = 5
    CREDIT_COST_VIEW_LIKERS: int = 20
    CREDIT_COST_BOOST: int = 15
    
    # Premium Pricing (in ZAR)
    PREMIUM_PRICE_MONTHLY: float = 99.99
    PREMIUM_PRICE_YEARLY: float = 999.99
    
    # Ozow Payment Gateway (for Next.js web app)
    OZOW_SITE_CODE: Optional[str] = None
    OZOW_PRIVATE_KEY: Optional[str] = None
    OZOW_API_KEY: Optional[str] = None
    OZOW_TEST_MODE: bool = True
    
    # Google Play In-App Purchases (for Flutter Android)
    GOOGLE_PLAY_PACKAGE_NAME: Optional[str] = None
    GOOGLE_PLAY_SERVICE_ACCOUNT_FILE: Optional[str] = None
    
    # Apple In-App Purchases (for Flutter iOS)
    APPLE_SHARED_SECRET: Optional[str] = None
    APPLE_BUNDLE_ID: Optional[str] = None
    
    @property
    def allowed_video_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_VIDEO_TYPES.split(",")]
    
    @property
    def allowed_audio_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_AUDIO_TYPES.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

