from supabase import create_client, Client
from .settings import settings


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        self.admin_client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    # User operations
    async def create_user_profile(self, auth_id: str, name: str, email: str):
        """Create user profile after authentication"""
        result = self.admin_client.table("users").insert({
            "auth_id": auth_id,
            "name": name,
            "email": email
        }).execute()
        return result.data[0] if result.data else None
    
    async def get_user_by_auth_id(self, auth_id: str):
        """Get user by their auth ID"""
        result = self.client.table("users").select("*").eq("auth_id", auth_id).execute()
        return result.data[0] if result.data else None
    
    async def get_user_by_email(self, email: str):
        """Get user by email"""
        result = self.client.table("users").select("*").eq("email", email).execute()
        return result.data[0] if result.data else None
    
    # Note: Conversations are generated on-the-fly and not stored in database for beta version
    
    # Saved expressions operations
    async def save_expression(self, user_id: str, expression: str, translation: str, 
                            context: str = None, category: str = None):
        """Save an expression for review"""
        result = self.client.table("saved_expressions").insert({
            "user_id": user_id,
            "expression": expression,
            "translation": translation,
            "context": context,
            "category": category
        }).execute()
        return result.data[0] if result.data else None
    
    async def get_user_expressions(self, user_id: str, limit: int = 50):
        """Get user's saved expressions"""
        result = self.client.table("saved_expressions").select("*").eq("user_id", user_id)\
            .order("created_at", desc=True).limit(limit).execute()
        return result.data
    
    async def delete_expression(self, expression_id: str, user_id: str):
        """Delete a saved expression"""
        result = self.client.table("saved_expressions").delete()\
            .eq("id", expression_id).eq("user_id", user_id).execute()
        return bool(result.data)
    
    # User stats operations
    async def get_user_stats(self, user_id: str):
        """Get user statistics"""
        result = self.client.table("user_stats").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    async def update_user_stats(self, user_id: str, sentences_practiced: int):
        """Update user stats after practice session"""
        from datetime import datetime, date
        
        # Update or create user stats
        current_stats = await self.get_user_stats(user_id)
        
        if current_stats:
            # Update existing stats
            new_total = current_stats['total_sentences'] + sentences_practiced
            result = self.client.table("user_stats").update({
                "total_sentences": new_total,
                "last_practice_date": date.today().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
        else:
            # Create new stats
            result = self.client.table("user_stats").insert({
                "user_id": user_id,
                "total_sentences": sentences_practiced,
                "total_expressions": 0,
                "current_streak": 1,
                "longest_streak": 1,
                "last_practice_date": date.today().isoformat()
            }).execute()
        
        return result.data[0] if result.data else None
    
    async def log_daily_practice(self, user_id: str, sentences_count: int):
        """Log daily practice for streak tracking"""
        from datetime import date
        
        today = date.today().isoformat()
        
        # Check if already practiced today
        existing = self.client.table("daily_practice_log").select("*")\
            .eq("user_id", user_id).eq("practice_date", today).execute()
        
        if existing.data:
            # Update existing log
            new_count = existing.data[0]['sentences_count'] + sentences_count
            result = self.client.table("daily_practice_log").update({
                "sentences_count": new_count
            }).eq("user_id", user_id).eq("practice_date", today).execute()
        else:
            # Create new log
            result = self.client.table("daily_practice_log").insert({
                "user_id": user_id,
                "practice_date": today,
                "sentences_count": sentences_count
            }).execute()
        
        # Update streak
        await self.update_streak(user_id)
        
        return result.data[0] if result.data else None
    
    async def update_streak(self, user_id: str):
        """Calculate and update user's streak"""
        from datetime import date, timedelta
        
        # Get practice logs for last 30 days
        start_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.client.table("daily_practice_log").select("practice_date")\
            .eq("user_id", user_id)\
            .gte("practice_date", start_date)\
            .order("practice_date", desc=True).execute()
        
        if not result.data:
            return 0
        
        # Calculate streak
        streak = 0
        expected_date = date.today()
        
        for log in result.data:
            log_date = date.fromisoformat(log['practice_date'])
            if log_date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break
        
        # Update user stats with new streak
        self.client.table("user_stats").update({
            "current_streak": streak,
            "longest_streak": self.client.rpc("greatest", {"a": streak, "b": "longest_streak"})
        }).eq("user_id", user_id).execute()
        
        return streak
    
    
    # Storage operations for audio
    async def upload_audio(self, file_name: str, audio_data: bytes, content_type: str = "audio/mpeg"):
        result = self.admin_client.storage.from_("audio").upload(
            file_name,
            audio_data,
            {"content-type": content_type}
        )
        if result:
            public_url = self.admin_client.storage.from_("audio").get_public_url(file_name)
            return public_url
        return None


# Create global instance
supabase = SupabaseService()