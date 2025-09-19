# Express Language Learning Backend - Python/FastAPI

Backend API for Express language learning app, built with Python, FastAPI, and Supabase.

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-4/3.5 + Whisper
- **Authentication**: JWT
- **Caching**: Redis (optional)

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anon key
- `SUPABASE_SERVICE_KEY`: Supabase service key
- `OPENAI_API_KEY`: OpenAI API key
- `JWT_SECRET_KEY`: Secret key for JWT (min 32 characters)

### 3. Supabase Database Setup

Run these SQL commands in your Supabase SQL editor:

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id TEXT UNIQUE NOT NULL,
  email TEXT,
  english_level TEXT DEFAULT 'intermediate',
  native_language TEXT DEFAULT 'korean',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  scenario TEXT,
  difficulty_level INTEGER,
  dialogue JSONB,
  thoughts JSONB,
  completed BOOLEAN DEFAULT FALSE,
  success_rate DECIMAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Expressions table
CREATE TABLE expressions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  conversation_id UUID REFERENCES conversations(id),
  korean_thought TEXT,
  english_expression TEXT,
  context TEXT,
  audio_url TEXT,
  mastery_level INTEGER DEFAULT 0,
  practice_count INTEGER DEFAULT 0,
  last_practiced TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User progress table
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) UNIQUE,
  total_conversations INTEGER DEFAULT 0,
  total_minutes INTEGER DEFAULT 0,
  expressions_saved INTEGER DEFAULT 0,
  expressions_mastered INTEGER DEFAULT 0,
  current_streak INTEGER DEFAULT 0,
  longest_streak INTEGER DEFAULT 0,
  last_practice_date DATE,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Thought attempts table
CREATE TABLE thought_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  conversation_id UUID REFERENCES conversations(id),
  korean_thought TEXT,
  expected_english TEXT,
  user_transcription TEXT,
  success_score DECIMAL,
  attempt_number INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. Create Storage Bucket

In Supabase Dashboard:
1. Go to Storage
2. Create bucket named `audio`
3. Make it public or configure RLS

### 5. Running the Server

Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the built-in runner:
```bash
python -m app.main
```

Production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/users` - Create/login user

### Conversations
- `POST /api/conversations/generate` - Generate AI conversation
- `GET /api/conversations/{id}` - Get conversation
- `POST /api/conversations/{id}/attempt` - Submit thought attempt
- `PUT /api/conversations/{id}/complete` - Complete conversation

### Expressions
- `POST /api/expressions` - Save expression
- `GET /api/expressions/user/{user_id}` - Get user expressions
- `PUT /api/expressions/{id}` - Update expression
- `DELETE /api/expressions/{id}` - Delete expression

### Progress
- `GET /api/progress/{user_id}` - Get progress
- `PUT /api/progress/{user_id}` - Update progress
- `GET /api/progress/streak/status` - Get streak status

### Audio
- `POST /api/audio/transcribe` - Speech to text
- `POST /api/audio/synthesize` - Text to speech

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── config/           # Configuration
│   ├── middleware/       # Auth, error handling
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── ai/          # GPT-4 conversation generation
│   │   └── audio/       # Speech processing
│   └── main.py          # FastAPI app
├── requirements.txt
└── .env
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-device-123"}'
```

## Production Deployment

1. Use a process manager (systemd, supervisor)
2. Set up reverse proxy (nginx)
3. Configure SSL/TLS
4. Set `ENVIRONMENT=production`
5. Use PostgreSQL connection pooling
6. Monitor API costs (OpenAI)

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### Supabase Connection
- Verify URL and keys in `.env`
- Check Supabase service status

### OpenAI API
- Verify API key has credits
- Check rate limits

## Notes

- Redis is optional for development
- All endpoints return consistent JSON responses
- JWT tokens expire after 7 days
- Audio files stored in Supabase Storage