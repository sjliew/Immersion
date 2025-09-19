"""
API endpoints for tracking conversation completions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.middleware.auth import get_current_user
from app.services.supabase_service import supabase_service

router = APIRouter()


class RecordCompletionRequest(BaseModel):
    conversation_id: str
    sentences_practiced: int
    completion_percentage: Optional[float] = 100.0


class CompletionResponse(BaseModel):
    conversation_id: str
    sentences_practiced: int
    completion_percentage: float
    completed_at: str
    is_completed: bool = True


@router.post("/record")
async def record_completion(
    request: RecordCompletionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Record that a user completed a conversation"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            user = await supabase_service.get_or_create_user(
                auth_id=current_user['user_id'],
                email=current_user.get('email', ''),
                name=current_user.get('email', '').split('@')[0]
            )
        
        # Record completion
        completion = await supabase_service.record_conversation_completion(
            user_id=user['id'],
            conversation_id=request.conversation_id,
            sentences_practiced=request.sentences_practiced,
            completion_percentage=request.completion_percentage
        )
        
        if not completion:
            raise HTTPException(status_code=400, detail="Failed to record completion")
        
        # Make sure we return only serializable data
        completion_data = {
            "conversation_id": request.conversation_id,
            "sentences_practiced": request.sentences_practiced,
            "completion_percentage": request.completion_percentage,
            "is_completed": True
        }
        
        return {
            "status": "success",
            "data": completion_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-completions")
async def get_my_completions(current_user: dict = Depends(get_current_user)):
    """Get all conversation completions for the current user"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            return {
                "status": "success",
                "data": [],
                "count": 0
            }
        
        # Get completions
        completions = await supabase_service.get_user_completions(user['id'])
        
        return {
            "status": "success",
            "data": completions,
            "count": len(completions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-conversations")
async def get_available_conversations(current_user: dict = Depends(get_current_user)):
    """Get conversations that user hasn't completed yet"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            # Return all conversations if user doesn't exist yet
            all_conversations = await supabase_service.get_all_library_conversations()
            return {
                "status": "success",
                "data": all_conversations,
                "count": len(all_conversations)
            }
        
        # Get available (not completed) conversations
        available = await supabase_service.get_available_conversations(user['id'])
        
        return {
            "status": "success",
            "data": available,
            "count": len(available)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations-with-status")
async def get_conversations_with_status(current_user: dict = Depends(get_current_user)):
    """Get all library conversations with user's completion status"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            # Return all as not completed if user doesn't exist
            all_conversations = await supabase_service.get_all_library_conversations()
            for conv in all_conversations:
                conv['is_completed'] = False
                conv['completion_data'] = None
            
            return {
                "status": "success",
                "data": all_conversations,
                "total": len(all_conversations),
                "completed": 0
            }
        
        # Get conversations with status
        conversations = await supabase_service.get_conversation_with_completion_status(user['id'])
        completed_count = sum(1 for c in conversations if c.get('is_completed', False))
        
        return {
            "status": "success",
            "data": conversations,
            "total": len(conversations),
            "completed": completed_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset")
async def reset_completions(current_user: dict = Depends(get_current_user)):
    """Reset all conversation completions for the user"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            return {
                "status": "success",
                "message": "No completions to reset"
            }
        
        # Delete all completions for this user
        from app.config.supabase import supabase
        result = supabase.client.table('user_conversation_completions')\
            .delete()\
            .eq('user_id', user['id'])\
            .execute()
        
        # Reset sentence count in user_stats
        supabase.client.table('user_stats')\
            .update({'total_sentences': 0})\
            .eq('user_id', user['id'])\
            .execute()
        
        return {
            "status": "success",
            "message": "All completions reset successfully",
            "deleted_count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))