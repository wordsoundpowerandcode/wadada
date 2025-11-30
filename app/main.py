from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    auth, 
    profiles, 
    media, 
    conversations, 
    messages, 
    matches, 
    likes,
    verification,
    discovery,
    payments,
    ads
)

app = FastAPI(
    title="Dating App API",
    description="FastAPI dating application with Supabase integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(media.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(matches.router)
app.include_router(likes.router)
app.include_router(verification.router)
app.include_router(discovery.router)
app.include_router(payments.router)
app.include_router(ads.router)

@app.get("/")
async def root():
    return {"message": "Dating App API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
