from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from app.models import ProgressUpdate
from app.config.supabase import supabase
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/{user_id}")
async def get_user_progress(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user's progress statistics"""
    try:
        # Verify user is accessing their own progress
        if current_user["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        progress = await supabase.get_user_progress(user_id)
        
        # Create initial progress if doesn't exist
        if not progress:
            progress = await supabase.update_user_progress(user_id, {
                "total_sentences": 0,
                "total_expressions": 0,
                "current_streak": 0,
                "longest_streak": 0
            })
        
        # Calculate additional stats
        today = datetime.utcnow().date()
        last_practice = datetime.fromisoformat(progress["last_practice_date"]) if progress.get("last_practice_date") else None
        
        stats = {
            **progress,
            "practiced_today": last_practice and last_practice.date() == today,
            "average_daily_sentences": progress.get("total_sentences", 0) // max(1, 1),
            "mastery_rate": 0  # Removed expressions_mastered field
        }
        
        return {"status": "success", "data": stats}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}")
async def update_progress(
    user_id: str,
    update_data: ProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's progress"""
    try:
        # Verify user is updating their own progress
        if current_user["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Get current progress
        current_progress = await supabase.get_user_progress(user_id)
        
        if not current_progress:
            current_progress = {
                "total_sentences": 0,
                "total_expressions": 0,
                "current_streak": 0,
                "longest_streak": 0
            }
        
        # Calculate updates
        updates = {}
        
        if update_data.sentences_practiced:
            updates["total_sentences"] = current_progress.get("total_sentences", 0) + update_data.sentences_practiced
        
        # Removed total_conversations - not a column in user_stats
        
        if update_data.expressions_saved is not None:
            updates["total_expressions"] = current_progress.get("total_expressions", 0) + update_data.expressions_saved
        
        # Removed expressions_mastered field
        
        # Update streak
        today = datetime.utcnow().date()
        last_practice = datetime.fromisoformat(current_progress["last_practice_date"]) if current_progress.get("last_practice_date") else None
        
        if last_practice:
            days_since_last = (today - last_practice.date()).days
            
            if days_since_last == 1:
                updates["current_streak"] = current_progress["current_streak"] + 1
            elif days_since_last > 1:
                updates["current_streak"] = 1
            # If same day, don't update streak
        else:
            updates["current_streak"] = 1
        
        # Update longest streak
        if updates.get("current_streak", 0) > current_progress["longest_streak"]:
            updates["longest_streak"] = updates["current_streak"]
        
        updates["last_practice_date"] = today.isoformat()
        
        updated_progress = await supabase.update_user_progress(user_id, updates)
        
        return {"status": "success", "data": updated_progress}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streak/status")
async def get_streak_status(
    current_user: dict = Depends(get_current_user)
):
    """Get user's streak status"""
    try:
        progress = await supabase.get_user_progress(current_user["user_id"])
        
        if not progress:
            return {
                "status": "success",
                "data": {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "practiced_today": False,
                    "streak_at_risk": False
                }
            }
        
        today = datetime.utcnow().date()
        last_practice = datetime.fromisoformat(progress["last_practice_date"]) if progress.get("last_practice_date") else None
        
        practiced_today = last_practice and last_practice.date() == today
        yesterday = today - timedelta(days=1)
        streak_at_risk = not practiced_today and last_practice and last_practice.date() == yesterday
        
        return {
            "status": "success",
            "data": {
                "current_streak": progress["current_streak"],
                "longest_streak": progress["longest_streak"],
                "practiced_today": practiced_today,
                "streak_at_risk": streak_at_risk,
                "last_practice_date": progress.get("last_practice_date")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/top")
async def get_leaderboard(period: str = "week"):
    """Get top users leaderboard"""
    try:
        date_filter = datetime.utcnow()
        
        if period == "week":
            date_filter = date_filter - timedelta(days=7)
        elif period == "month":
            date_filter = date_filter - timedelta(days=30)
        
        result = supabase.client.table("user_stats")\
            .select("user_id, total_sentences, total_expressions, current_streak")\
            .gte("last_practice_date", date_filter.isoformat())\
            .order("total_sentences", desc=True)\
            .limit(20)\
            .execute()
        
        return {
            "status": "success",
            "data": result.data,
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))