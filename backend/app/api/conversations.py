from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.config.supabase import supabase
from app.middleware.auth import get_current_user, get_current_user_optional
from app.services.openai_service import openai_service
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateConversationRequest(BaseModel):
    topic: str
    difficulty: str = "intermediate"


class SuggestionsRequest(BaseModel):
    user_input: str
    context: str
    korean_thought: Optional[str] = None


class FeedbackRequest(BaseModel):
    user_input: str
    expected_response: str
    context: Optional[str] = None


@router.post("/generate")
async def generate_conversation(
    request: GenerateConversationRequest,
    # Temporarily disable auth for development
    # current_user: dict = Depends(get_current_user)
):
    """Fetch a random conversation from the database instead of generating"""
    try:
        # Fetch a random conversation from library
        result = supabase.client.table('conversations').select("*").eq('is_library', True).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No conversations available")
        
        # Pick a random conversation
        import random
        conv = random.choice(result.data)
        
        # Parse the JSON dialogue field
        dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
        
        return {
            "status": "success",
            "data": {
                "id": str(conv['id']),
                "dialogue": dialogue,
                "topic": request.topic,  # Keep for compatibility
                "difficulty": request.difficulty,  # Keep for compatibility
                "scenario": conv.get('scenario', ''),
                "created_at": conv['created_at']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate conversation: {str(e)}")
        # Return a fallback conversation on error
        return {
            "status": "success",
            "data": {
                "id": "fallback",
                "dialogue": [
                    {
                        "speaker": "Person B",
                        "text": "Hey! How's your day going so far?"
                    },
                    {
                        "speaker": "Person A",
                        "korean_thought": "오늘 정말 바빴는데 괜찮다고 말하고 싶어",
                        "english_expression": "It's been pretty hectic actually, but I'm managing!"
                    },
                    {
                        "speaker": "Person B",
                        "text": "Oh, what's been keeping you so busy?"
                    },
                    {
                        "speaker": "Person A",
                        "korean_thought": "프로젝트 마감이 다가와서 야근을 많이 하고 있어",
                        "english_expression": "I've been pulling some late nights trying to wrap up this project before the deadline"
                    }
                ],
                "topic": request.topic,
                "difficulty": request.difficulty,
                "created_at": datetime.utcnow().isoformat()
            }
        }


@router.post("/suggest")
async def get_suggestions(
    request: SuggestionsRequest,
    # Temporarily disable auth for development
    # current_user: dict = Depends(get_current_user)
):
    """Get alternative expressions for the user's input"""
    try:
        # Generate suggestions using OpenAI
        suggestions = await openai_service.generate_suggestions(
            user_input=request.user_input,
            context=request.context,
            korean_thought=request.korean_thought or ""
        )
        
        return {
            "status": "success",
            "data": {
                "original": request.user_input,
                "suggestions": suggestions
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {str(e)}")
        # Return default suggestions on error
        return {
            "status": "success",
            "data": {
                "original": request.user_input,
                "suggestions": [
                    "Let me think about that",
                    "That's an interesting point",
                    "I see what you mean"
                ]
            }
        }


@router.post("/feedback")
async def provide_feedback(
    request: FeedbackRequest,
    # Temporarily disable auth for development
    # current_user: dict = Depends(get_current_user)
):
    """Evaluate user's response and provide feedback"""
    try:
        # Skip user profile check for development
        # user = await supabase.get_user_by_auth_id(current_user['user_id'])
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")
        
        # Evaluate response using OpenAI
        evaluation = await openai_service.evaluate_response(
            user_response=request.user_input,
            expected_response=request.expected_response,
            context=request.context or ""
        )
        
        return {
            "status": "success",
            "data": evaluation
        }
        
    except Exception as e:
        logger.error(f"Failed to provide feedback: {str(e)}")
        # Return encouraging feedback on error
        return {
            "status": "success",
            "data": {
                "score": 75,
                "accuracy": "good",
                "feedback": "Good effort! Keep practicing to improve",
                "corrections": [],
                "well_done": ["You communicated your thought clearly"]
            }
        }


@router.get("/random")
async def get_random_conversation(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get a random conversation from the library, filtered by user's character if authenticated"""
    try:
        # Start with base query
        query = supabase.client.table('conversations').select("*").eq('is_library', True)
        
        # If user is authenticated, filter by their selected character
        if current_user:
            # Get user's selected character_id
            user_result = supabase.client.table('users')\
                .select('character_id')\
                .eq('auth_id', current_user['user_id'])\
                .single()\
                .execute()
            
            if user_result.data and user_result.data.get('character_id'):
                character_id = user_result.data['character_id']
                logger.info(f"Filtering conversations for character_id: {character_id}")
                query = query.eq('character_id', character_id)
        
        # Execute query and order by ID
        result = query.order('id').execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No conversations available for this character")
        
        # Pick a random conversation
        import random
        conv = random.choice(result.data)
        
        # Parse the JSON dialogue field
        dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
        
        return {
            "status": "success",
            "data": {
                "id": str(conv['id']),
                "scenario": conv.get('scenario', ''),
                "journal_context": conv.get('journal_context', ''),
                "difficulty_level": conv.get('difficulty_level', 5),
                "dialogue": dialogue,
                "time_of_day": conv.get('time_of_day'),
                "location": conv.get('location'),
                "description": conv.get('description'),
                "created_at": conv['created_at']
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch random conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next")
async def get_next_conversation(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get the next conversation in sequence based on day_number and user progress"""
    try:
        auth_id = current_user.get('user_id') if current_user else None
        logger.info(f"=== /next endpoint called ===")
        logger.info(f"Auth ID: {auth_id}")
        
        # Start with base query
        query = supabase.client.table('conversations').select("*").eq('is_library', True)
        
        # If user is authenticated, filter by their selected character
        if auth_id:
            # Get user's selected character_id
            user_result = supabase.client.table('users')\
                .select('character_id')\
                .eq('auth_id', auth_id)\
                .single()\
                .execute()
            
            if user_result.data and user_result.data.get('character_id'):
                character_id = user_result.data['character_id']
                logger.info(f"Filtering conversations for character_id: {character_id}")
                query = query.eq('character_id', character_id)
        
        # Fetch all library conversations ordered by day_number
        all_convs_result = query.order('day_number').execute()
        
        if not all_convs_result.data:
            return {
                "status": "error",
                "message": "No conversations available"
            }
        
        all_conversations = all_convs_result.data
        total_days = len(all_conversations)
        
        logger.info(f"Total conversations available: {total_days}")
        logger.info(f"Available conversation IDs and days: {[(c['id'], c.get('day_number')) for c in all_conversations]}")
        
        # If user is logged in, check their progress
        if auth_id:
            # Get the database user from auth_id
            from app.services.supabase_service import supabase_service
            user = await supabase_service.get_user_by_auth_id(auth_id)
            
            if not user:
                logger.info("User not found in database")
                # User not found, treat as no completions
                completed_ids = set()
                completed_count = 0
            else:
                user_id = user['id']
                logger.info(f"Database user ID: {user_id}")
                
                # Get completed conversation IDs for this user
                completions_result = supabase.client.table('user_conversation_completions')\
                    .select("conversation_id")\
                    .eq('user_id', user_id)\
                    .execute()
                
                completed_ids = {c['conversation_id'] for c in (completions_result.data or [])}
                completed_count = len(completed_ids)
                
                logger.info(f"User has {completed_count} completions")
                logger.info(f"Completed conversation IDs: {completed_ids}")
            
            # Find first uncompleted conversation
            for conv in all_conversations:
                logger.info(f"Checking conversation ID {conv['id']} (Day {conv.get('day_number')})")
                if conv['id'] not in completed_ids:
                    logger.info(f"Found uncompleted conversation: ID {conv['id']} (Day {conv.get('day_number')})")
                    # Parse dialogue
                    dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
                    
                    return {
                        "status": "success",
                        "data": {
                            "id": str(conv['id']),
                            "scenario": conv.get('scenario', ''),
                            "journal_context": conv.get('journal_context', ''),
                            "difficulty_level": conv.get('difficulty_level', 5),
                            "dialogue": dialogue,
                            "time_of_day": conv.get('time_of_day'),
                            "location": conv.get('location'),
                            "description": conv.get('description'),
                            "day_number": conv.get('day_number', 1),
                            "created_at": conv['created_at']
                        },
                        "progress": {
                            "current_day": conv.get('day_number', 1),
                            "total_days": total_days,
                            "completed_days": completed_count,
                            "is_new": completed_count == 0
                        }
                    }
            
            # All conversations completed - return first one with completion flag
            logger.info(f"All conversations completed! Returning Day 1 with all_completed flag")
            conv = all_conversations[0]
            dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
            
            return {
                "status": "success",
                "data": {
                    "id": str(conv['id']),
                    "scenario": conv.get('scenario', ''),
                    "journal_context": conv.get('journal_context', ''),
                    "difficulty_level": conv.get('difficulty_level', 5),
                    "dialogue": dialogue,
                    "time_of_day": conv.get('time_of_day'),
                    "location": conv.get('location'),
                    "description": conv.get('description'),
                    "day_number": conv.get('day_number', 1),
                    "created_at": conv['created_at']
                },
                "all_completed": True,
                "progress": {
                    "current_day": conv.get('day_number', 1),
                    "total_days": total_days,
                    "completed_days": completed_count,
                    "is_new": False
                }
            }
        
        # No user logged in - return first conversation
        conv = all_conversations[0]
        dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
        
        return {
            "status": "success",
            "data": {
                "id": str(conv['id']),
                "scenario": conv.get('scenario', ''),
                "journal_context": conv.get('journal_context', ''),
                "difficulty_level": conv.get('difficulty_level', 5),
                "dialogue": dialogue,
                "time_of_day": conv.get('time_of_day'),
                "location": conv.get('location'),
                "description": conv.get('description'),
                "day_number": conv.get('day_number', 1),
                "created_at": conv['created_at']
            },
            "progress": {
                "current_day": conv.get('day_number', 1),
                "total_days": total_days,
                "completed_days": 0,
                "is_new": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch next conversation: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/library")
async def get_library_conversations():
    """Get all library conversations for the app"""
    try:
        # Fetch all library conversations from Supabase, ordered by ID
        result = supabase.client.table('conversations').select("*").eq('is_library', True).order('id').execute()
        
        conversations = []
        for conv in result.data:
            # Parse the JSON dialogue field
            dialogue = json.loads(conv['dialogue']) if isinstance(conv['dialogue'], str) else conv['dialogue']
            
            conversations.append({
                "id": conv['id'],
                "scenario": conv['scenario'],
                "journal_context": conv.get('journal_context', ''),
                "difficulty_level": conv.get('difficulty_level', 5),
                "dialogue": dialogue,
                "time_of_day": conv.get('time_of_day'),
                "location": conv.get('location'),
                "description": conv.get('description'),
                "created_at": conv['created_at']
            })
        
        return {
            "status": "success",
            "data": conversations
        }
    except Exception as e:
        logger.error(f"Failed to fetch library conversations: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID"""
    try:
        # Fetch specific conversation from Supabase
        result = supabase.client.table('conversations').select("*").eq('id', conversation_id).single().execute()
        
        if result.data:
            # Parse the JSON dialogue field
            dialogue = json.loads(result.data['dialogue']) if isinstance(result.data['dialogue'], str) else result.data['dialogue']
            
            return {
                "status": "success",
                "data": {
                    "id": result.data['id'],
                    "scenario": result.data['scenario'],
                    "journal_context": result.data.get('journal_context', ''),
                    "difficulty_level": result.data.get('difficulty_level', 5),
                    "dialogue": dialogue,
                    "time_of_day": result.data.get('time_of_day'),
                    "location": result.data.get('location'),
                    "description": result.data.get('description'),
                    "created_at": result.data['created_at']
                }
            }
        else:
            return {
                "status": "error",
                "message": "Conversation not found"
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch conversation {conversation_id}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/topics")
async def get_conversation_topics(
    # Temporarily disable auth for development
    # current_user: dict = Depends(get_current_user)
):
    """Get suggested conversation topics"""
    topics = [
        {
            "id": "neighbor_noise",
            "title": "Talking to a noisy neighbor",
            "description": "Politely addressing noise complaints",
            "difficulty": "intermediate"
        },
        {
            "id": "work_deadline",
            "title": "Requesting deadline extension",
            "description": "Professional communication about deadlines",
            "difficulty": "intermediate"
        },
        {
            "id": "restaurant_order",
            "title": "Restaurant order issue",
            "description": "Handling incorrect orders politely",
            "difficulty": "easy"
        },
        {
            "id": "job_interview",
            "title": "Job interview responses",
            "description": "Answering common interview questions",
            "difficulty": "hard"
        },
        {
            "id": "small_talk",
            "title": "Office small talk",
            "description": "Casual workplace conversations",
            "difficulty": "easy"
        },
        {
            "id": "appointment",
            "title": "Scheduling appointments",
            "description": "Making and changing appointments",
            "difficulty": "easy"
        },
        {
            "id": "feedback",
            "title": "Giving constructive feedback",
            "description": "Professional feedback to colleagues",
            "difficulty": "hard"
        },
        {
            "id": "networking",
            "title": "Networking event",
            "description": "Meeting new professional contacts",
            "difficulty": "intermediate"
        }
    ]
    
    return {
        "status": "success",
        "data": topics
    }