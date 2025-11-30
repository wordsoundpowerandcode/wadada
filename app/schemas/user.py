from pydantic import BaseModel, EmailStr
from app.schemas.profile import ProfileResponse

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ProfileResponse

