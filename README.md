# FastAPI Dating Application with Supabase

A modern dating application built with FastAPI, SQLModel, and Supabase integration.

## Features

- **Authentication**: Supabase Auth with email/password and OAuth (Google, GitHub)
- **Profile Management**: User profiles with required introductory media (video/audio)
- **Media Upload**: Secure media storage using Supabase Storage
- **Real-time Messaging**: Full-featured messaging system with Supabase Realtime
- **Message Reactions**: React to messages with emojis (like, heart, laugh, etc.)
- **Read Receipts**: Track message read status
- **Typing Indicators**: Real-time typing indicators in conversations

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLModel**: SQL databases in Python, designed for simplicity, compatibility, and robustness
- **Supabase**: Backend-as-a-Service for Auth, Database, Storage, and Realtime
- **Alembic**: Database migration tool with async support
- **PostgreSQL**: Database (via Supabase)

## Project Structure

```
wadada/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection setup
│   ├── models/                 # SQLModel database models
│   ├── schemas/                # Pydantic schemas for API
│   ├── api/                    # API routes
│   ├── services/               # Supabase services
│   └── utils/                  # Utility functions
├── migrations/                 # Alembic migration files
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- Supabase account and project
- PostgreSQL database (via Supabase)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxxxx.supabase.co:5432/postgres

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT
JWT_SECRET=your-jwt-secret-key
JWT_ALGORITHM=HS256

# Storage
STORAGE_BUCKET=user-media
MAX_FILE_SIZE=52428800
ALLOWED_VIDEO_TYPES=video/mp4,video/quicktime
ALLOWED_AUDIO_TYPES=audio/mpeg,audio/mp3,audio/wav

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### 4. Setup Supabase

1. Create a Supabase project
2. Create a storage bucket named `user-media` (or update `STORAGE_BUCKET` in `.env`)
3. Configure OAuth providers in Supabase Dashboard (if using OAuth)
4. Set up Row Level Security (RLS) policies as needed

### 5. Run Database Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /auth/signup` - Sign up with email/password
- `POST /auth/login` - Login with email/password
- `GET /auth/oauth/{provider}` - OAuth login (Google/GitHub)
- `GET /auth/oauth/{provider}/callback` - OAuth callback
- `POST /auth/refresh` - Refresh JWT token

### Profiles
- `POST /profiles` - Create profile
- `GET /profiles/me` - Get current user's profile
- `PUT /profiles/me` - Update profile
- `GET /profiles/{profile_id}` - Get public profile

### Media
- `POST /media/upload` - Upload media file
- `PUT /media/intro-media` - Update introductory media
- `GET /media/{media_id}` - Get media metadata

### Conversations
- `GET /conversations` - List user's conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{conversation_id}` - Get conversation details
- `GET /conversations/{conversation_id}/messages` - Get message history

### Messages
- `POST /messages` - Send message
- `POST /messages/{message_id}/reactions` - Add reaction to message
- `DELETE /messages/{message_id}/reactions/{reaction_id}` - Remove reaction
- `PUT /messages/{message_id}/read` - Mark message as read

## Database Models

- **Profile**: User profiles linked to Supabase Auth users
- **UserMedia**: Media files (videos/audio) associated with profiles
- **Conversation**: Chat conversations between users
- **ConversationParticipant**: Many-to-many relationship with metadata
- **Message**: Messages in conversations
- **MessageReaction**: Reactions to messages

## Development

### Running Tests

```bash
pytest
```

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

Ensure all environment variables are set in your production environment. Use secure methods like:
- Environment variables in your hosting platform
- Secrets management services
- `.env` files (not recommended for production)

## License

MIT

