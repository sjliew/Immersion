from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EnglishLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Speaker(str, Enum):
    user = "user"
    neighbor = "neighbor"
    colleague = "colleague"
    friend = "friend"
    stranger = "stranger"


# User Models
class UserCreate(BaseModel):
    device_id: str
    email: Optional[str] = None


class User(BaseModel):
    id: str
    device_id: str
    email: Optional[str] = None
    created_at: datetime


class UserResponse(BaseModel):
    user: User
    token: str


# Conversation Models
class ConversationTurn(BaseModel):
    id: int
    speaker: Speaker
    text: Optional[str] = None
    audio_url: Optional[str] = None
    korean_thought: Optional[str] = None
    english_hint: Optional[str] = None


class ThoughtChallenge(BaseModel):
    id: str
    korean_thought: str
    english_expression: str
    difficulty_points: List[str]
    context: str


class ConversationCreate(BaseModel):
    scenario: Optional[str] = None
    difficulty_level: int = Field(ge=1, le=10, default=5)
    context: Optional[str] = None


class Conversation(BaseModel):
    id: str
    user_id: str
    scenario: str
    difficulty_level: int
    dialogue: List[ConversationTurn]
    thoughts: List[ThoughtChallenge]
    completed: bool = False
    success_rate: Optional[float] = None
    created_at: datetime


# Expression Models
class ExpressionCreate(BaseModel):
    conversation_id: Optional[str] = None
    korean_thought: str
    english_expression: str
    context: str
    audio_url: Optional[str] = None


class Expression(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    korean_thought: str
    english_expression: str
    context: str
    audio_url: Optional[str] = None
    mastery_level: int = 0
    practice_count: int = 0
    last_practiced: Optional[datetime] = None
    created_at: datetime


class ExpressionUpdate(BaseModel):
    mastery_level: Optional[int] = Field(None, ge=0, le=5)
    practice_count: Optional[int] = Field(None, ge=0)


# Thought Attempt Models
class ThoughtAttemptCreate(BaseModel):
    korean_thought: str
    expected_english: str
    user_transcription: str
    attempt_number: int = 1


class ThoughtAttempt(BaseModel):
    id: str
    user_id: str
    conversation_id: str
    korean_thought: str
    expected_english: str
    user_transcription: str
    success_score: float
    attempt_number: int
    created_at: datetime


class AttemptEvaluation(BaseModel):
    score: float
    feedback: str
    improvements: List[str]


# Progress Models
class UserProgress(BaseModel):
    user_id: str
    total_conversations: int = 0
    total_minutes: int = 0
    expressions_saved: int = 0
    expressions_mastered: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_practice_date: Optional[datetime] = None
    updated_at: datetime


class ProgressUpdate(BaseModel):
    minutes_practiced: Optional[int] = Field(None, ge=0)
    expressions_saved: Optional[int] = Field(None, ge=0)
    expressions_mastered: Optional[int] = Field(None, ge=0)
    conversation_completed: Optional[bool] = None


class ProgressStats(BaseModel):
    user_id: str
    total_conversations: int
    total_minutes: int
    expressions_saved: int
    expressions_mastered: int
    current_streak: int
    longest_streak: int
    practiced_today: bool
    average_daily_minutes: int
    mastery_rate: int
    last_practice_date: Optional[datetime] = None


# Audio Models
class TranscribeRequest(BaseModel):
    audio: Optional[str] = None  # Base64 encoded audio
    audio_url: Optional[str] = None  # URL to audio file
    language: str = "en"


class TranscriptionResult(BaseModel):
    text: str
    confidence: float
    words: Optional[List[Dict[str, Any]]] = None


class SynthesizeRequest(BaseModel):
    text: str = Field(..., max_length=1000)
    voice: str = Field(default="nova", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")
    upload: bool = False


# Generation Parameters
class GenerationParams(BaseModel):
    user_id: str
    difficulty_level: int = Field(ge=1, le=10, default=5)
    scenario: Optional[str] = None
    context: Optional[str] = None
    recent_topics: Optional[List[str]] = None
    mastered_expressions: Optional[List[str]] = None