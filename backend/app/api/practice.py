from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.config.supabase import supabase
from app.middleware.auth import get_current_user

router = APIRouter()


class PracticeSessionComplete(BaseModel):
    sentences_practiced: int


@router.post("/complete")
async def complete_practice_session(
    data: PracticeSessionComplete,
    current_user: dict = Depends(get_current_user)
):
    """Log completion of a practice session"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user stats
        updated_stats = await supabase.update_user_stats(
            user_id=user['id'],
            sentences_practiced=data.sentences_practiced
        )
        
        # Log daily practice
        await supabase.log_daily_practice(
            user_id=user['id'],
            sentences_count=data.sentences_practiced
        )
        
        return {
            "status": "success",
            "data": {
                "stats": updated_stats,
                "sentences_practiced": data.sentences_practiced
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-check")
async def daily_app_check(current_user: dict = Depends(get_current_user)):
    """Check daily app open and update streak"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Call the database function to update streak
        result = supabase.client.rpc('update_user_streak', {'p_user_id': user['id']}).execute()
        
        if result.data and len(result.data) > 0:
            streak_data = result.data[0]
            
            # Get updated user data for full stats
            updated_user = supabase.client.table('users').select('*').eq('id', user['id']).single().execute()
            
            return {
                "status": "success",
                "data": {
                    "streak_increased": streak_data.get('streak_increased', False),
                    "current_streak": streak_data.get('new_streak', 0),
                    "is_first_today": streak_data.get('is_first_today', False),
                    "longest_streak": updated_user.data.get('longest_streak', 0) if updated_user.data else 0
                }
            }
        else:
            return {
                "status": "success",
                "data": {
                    "streak_increased": False,
                    "current_streak": 0,
                    "is_first_today": False,
                    "longest_streak": 0
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streak")
async def get_user_streak(current_user: dict = Depends(get_current_user)):
    """Get current user's practice streak"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user data directly from users table for streak info
        user_data = supabase.client.table('users').select('current_streak, longest_streak, last_app_open_date').eq('id', user['id']).single().execute()
        
        if not user_data.data:
            return {
                "status": "success",
                "data": {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_app_open_date": None
                }
            }
        
        return {
            "status": "success",
            "data": {
                "current_streak": user_data.data.get('current_streak', 0),
                "longest_streak": user_data.data.get('longest_streak', 0),
                "last_app_open_date": user_data.data.get('last_app_open_date')
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_practice_history(
    current_user: dict = Depends(get_current_user),
    days: int = 30
):
    """Get user's practice history for the last N days"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get practice logs
        from datetime import date, timedelta
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase.client.table("daily_practice_log")\
            .select("*")\
            .eq("user_id", user['id'])\
            .gte("practice_date", start_date)\
            .order("practice_date", desc=True)\
            .execute()
        
        return {
            "status": "success",
            "data": result.data or [],
            "days_requested": days,
            "days_practiced": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))