"""
API endpoints for character management and selection
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.middleware.auth import get_current_user, get_current_user_optional
from app.services.supabase_service import supabase_service

router = APIRouter()


class Character(BaseModel):
    id: str
    name: str
    emoji: Optional[str] = None
    location: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None


class CharacterSelection(BaseModel):
    character_id: str


class CharacterProgress(BaseModel):
    character_id: str
    character_name: str
    current_chapter: int
    total_chapters: int
    chapters_completed: int
    completion_percentage: float


@router.get("/list")
async def get_all_characters(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get all available characters for selection"""
    try:
        # Get characters from database
        result = supabase_service.client.table('characters')\
            .select("*")\
            .order('id')\
            .execute()
        
        # Return raw data for now to see what fields exist
        return {
            "status": "success",
            "data": result.data or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select")
async def select_character(
    selection: CharacterSelection,
    current_user: dict = Depends(get_current_user)
):
    """Select a character for the current user"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            user = await supabase_service.get_or_create_user(
                auth_id=current_user['user_id'],
                email=current_user.get('email', ''),
                name=current_user.get('email', '').split('@')[0]
            )
        
        # Update user's selected character
        result = supabase_service.client.table('users')\
            .update({
                'character_id': selection.character_id,
                'character_start_date': 'now()'
            })\
            .eq('id', user['id'])\
            .execute()
        
        # Initialize character progress tracking
        supabase_service.client.table('user_character_progress')\
            .upsert({
                'user_id': user['id'],
                'character_id': selection.character_id,
                'current_chapter': 1,
                'chapters_completed': 0,
                'started_at': 'now()',
                'last_played_at': 'now()'
            }, on_conflict='user_id,character_id')\
            .execute()
        
        return {
            "status": "success",
            "message": f"Character {selection.character_id} selected",
            "data": {
                "character_id": selection.character_id,
                "user_id": user['id']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
async def get_current_character(
    current_user: dict = Depends(get_current_user)
):
    """Get the user's currently selected character"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user or not user.get('character_id'):
            return {
                "status": "success",
                "data": None,
                "message": "No character selected"
            }
        
        # Get character details
        result = supabase_service.client.table('characters')\
            .select("*")\
            .eq('id', user['character_id'])\
            .single()\
            .execute()
        
        if not result.data:
            return {
                "status": "success",
                "data": None,
                "message": "Character not found"
            }
        
        char = result.data
        character = Character(
            id=char['id'],
            name=char['name'],
            emoji=char.get('emoji'),
            location=char.get('location'),
            age_group=char.get('age_group'),
            gender=char.get('gender')
        )
        
        return {
            "status": "success",
            "data": character
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_character_progress(
    current_user: dict = Depends(get_current_user)
):
    """Get user's progress in their current character's story"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user or not user.get('character_id'):
            return {
                "status": "success",
                "data": None,
                "message": "No character selected"
            }
        
        # Get progress from view
        result = supabase_service.client.table('user_story_progress')\
            .select("*")\
            .eq('user_id', user['id'])\
            .single()\
            .execute()
        
        if not result.data:
            # No progress yet, return initial state
            char_result = supabase_service.client.table('characters')\
                .select("name, chapter_count")\
                .eq('id', user['character_id'])\
                .single()\
                .execute()
            
            if char_result.data:
                return {
                    "status": "success",
                    "data": CharacterProgress(
                        character_id=user['character_id'],
                        character_name=char_result.data['name'],
                        current_chapter=1,
                        total_chapters=char_result.data['chapter_count'],
                        chapters_completed=0,
                        completion_percentage=0.0
                    )
                }
        
        progress_data = result.data
        progress = CharacterProgress(
            character_id=progress_data['character_id'],
            character_name=progress_data['character_name'],
            current_chapter=progress_data.get('current_chapter', 1),
            total_chapters=progress_data['total_chapters'],
            chapters_completed=progress_data.get('chapters_completed', 0),
            completion_percentage=progress_data.get('completion_percentage', 0.0)
        )
        
        return {
            "status": "success",
            "data": progress
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next-conversation")
async def get_next_story_conversation(
    current_user: dict = Depends(get_current_user)
):
    """Get the next conversation in the character's story"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get('character_id'):
            return {
                "status": "success",
                "data": None,
                "message": "Please select a character first"
            }
        
        # Call the database function to get next conversation
        result = supabase_service.client.rpc(
            'get_next_conversation_for_user',
            {'p_user_id': user['id']}
        ).execute()
        
        if not result.data or len(result.data) == 0:
            # User has completed all conversations for this character
            return {
                "status": "success",
                "data": None,
                "message": "All chapters completed! Great job!",
                "completed": True
            }
        
        next_conv = result.data[0]
        return {
            "status": "success",
            "data": {
                "conversation_id": next_conv['conversation_id'],
                "scenario": next_conv['scenario'],
                "chapter_name": next_conv['chapter_name'],
                "story_context": next_conv['story_context'],
                "story_order": next_conv['story_order']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-progress")
async def update_character_progress(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Update character progress after completing a conversation"""
    try:
        # Get user profile
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the conversation's story_order
        conv_result = supabase_service.client.table('conversations')\
            .select("character_id, story_order")\
            .eq('id', conversation_id)\
            .single()\
            .execute()
        
        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        character_id = conv_result.data['character_id']
        story_order = conv_result.data['story_order']
        
        # Update user's character progress
        result = supabase_service.client.table('user_character_progress')\
            .update({
                'current_chapter': story_order + 1,  # Move to next chapter
                'chapters_completed': story_order,
                'last_played_at': 'now()'
            })\
            .eq('user_id', user['id'])\
            .eq('character_id', character_id)\
            .execute()
        
        return {
            "status": "success",
            "message": "Progress updated",
            "data": {
                "chapters_completed": story_order,
                "current_chapter": story_order + 1
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))