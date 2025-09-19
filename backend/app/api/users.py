from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.config.supabase import supabase
from app.middleware.auth import get_current_user
from app.services.supabase_service import supabase_service

router = APIRouter()


class UserProfileCreate(BaseModel):
    auth_id: str
    name: str
    email: str

class UserCharacterUpdate(BaseModel):
    character_name: str
    character_emoji: str
    character_location: str
    character_age_group: str
    character_gender: str
    character_start_date: str


@router.post("/profile")
async def create_user_profile(
    data: UserProfileCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create user profile after authentication"""
    try:
        # Use the authenticated user's ID
        auth_id = current_user['user_id']
        email = current_user.get('email', data.email)
        
        # Get or create user profile
        profile = await supabase_service.get_or_create_user(
            auth_id=auth_id,
            email=email,
            name=data.name
        )
        
        return {"status": "success", "data": profile}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        
        if not user:
            # Auto-create profile if it doesn't exist
            user = await supabase_service.get_or_create_user(
                auth_id=current_user['user_id'],
                email=current_user.get('email', ''),
                name=current_user.get('email', '').split('@')[0]
            )
        
        return {"status": "success", "data": user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/character")
async def update_user_character(
    data: UserCharacterUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's character selection"""
    try:
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find character by name
        character_result = supabase.client.table('characters').select('id').eq('name', data.character_name).execute()
        if not character_result.data:
            raise HTTPException(status_code=404, detail=f"Character '{data.character_name}' not found")
        
        character_id = character_result.data[0]['id']
        
        # Update user with character ID and start date
        result = supabase.client.table('users').update({
            'character_id': character_id,
            'character_start_date': data.character_start_date
        }).eq('id', user['id']).execute()
        
        return {"status": "success", "data": result.data[0] if result.data else None}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/character")
async def get_user_character(current_user: dict = Depends(get_current_user)):
    """Get user's character data"""
    try:
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's character_id and character_start_date
        user_result = supabase.client.table('users').select(
            'character_id, character_start_date'
        ).eq('id', user['id']).single().execute()
        
        if not user_result.data or not user_result.data.get('character_id'):
            return {"status": "success", "data": None}
        
        # Get character data from characters table
        character_result = supabase.client.table('characters').select(
            'id, name, emoji, location, age_group, gender'
        ).eq('id', user_result.data['character_id']).single().execute()
        
        if not character_result.data:
            return {"status": "success", "data": None}
        
        # Combine data for frontend compatibility
        character_data = {
            'character_name': character_result.data['name'],
            'character_emoji': character_result.data.get('emoji', '👤'),
            'character_location': character_result.data.get('location', 'new-york'),
            'character_age_group': character_result.data.get('age_group', '25-34'),
            'character_gender': character_result.data.get('gender', 'neutral'),
            'character_start_date': user_result.data.get('character_start_date')
        }
        
        # Calculate day number
        from datetime import datetime
        if character_data.get('character_start_date'):
            start_date = datetime.fromisoformat(character_data['character_start_date'].replace('Z', '+00:00'))
            days_elapsed = (datetime.now() - start_date).days + 1
            character_data['day_number'] = days_elapsed
        else:
            character_data['day_number'] = 1
        
        return {"status": "success", "data": character_data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics for main screen"""
    try:
        # Get user profile first
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            # Auto-create if doesn't exist
            user = await supabase_service.get_or_create_user(
                auth_id=current_user['user_id'],
                email=current_user.get('email', ''),
                name=current_user.get('email', '').split('@')[0]
            )
        
        # Get stats
        stats = await supabase_service.get_user_stats(user['id'])
        
        # Get saved expressions count
        expressions = await supabase_service.get_user_expressions(user['id'])
        
        # Get completion count
        completions = await supabase_service.get_user_completions(user['id'])
        
        # Get streak data directly from users table
        user_data = supabase.client.table('users').select('current_streak, longest_streak, last_app_open_date').eq('id', user['id']).single().execute()
        
        # Add additional stats
        stats["total_expressions"] = len(expressions) if expressions else 0
        stats["completed_conversations"] = len(completions)
        
        # Add streak data
        if user_data.data:
            stats["current_streak"] = user_data.data.get('current_streak', 0)
            stats["longest_streak"] = user_data.data.get('longest_streak', 0)
            stats["last_app_open_date"] = user_data.data.get('last_app_open_date')
        else:
            stats["current_streak"] = 0
            stats["longest_streak"] = 0
            stats["last_app_open_date"] = None
        
        return {"status": "success", "data": stats}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))