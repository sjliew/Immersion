"""
Supabase service for database operations with authentication support
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    # ========== User Management ==========
    
    async def get_or_create_user(self, auth_id: str, email: str, name: Optional[str] = None) -> Dict:
        """Get existing user or create new one"""
        try:
            # First try to get existing user
            result = self.client.table('users').select("*").eq('auth_id', auth_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            # Create new user
            user_data = {
                'auth_id': auth_id,
                'email': email,
                'name': name or email.split('@')[0]
            }
            
            result = self.client.table('users').insert(user_data).execute()
            
            if result.data:
                # Create initial user_stats record
                self.client.table('user_stats').insert({
                    'user_id': result.data[0]['id'],
                    'total_sentences': 0,
                    'total_expressions': 0,
                    'current_streak': 0,
                    'longest_streak': 0
                }).execute()
                
                return result.data[0]
            
            raise Exception("Failed to create user")
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            raise e
    
    async def get_user_by_auth_id(self, auth_id: str) -> Optional[Dict]:
        """Get user by auth_id"""
        try:
            result = self.client.table('users').select("*").eq('auth_id', auth_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by auth_id: {str(e)}")
            return None
    
    async def update_user_profile(self, user_id: str, updates: Dict) -> Dict:
        """Update user profile"""
        try:
            result = self.client.table('users').update(updates).eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise e
    
    # ========== Conversation Completions ==========
    
    async def record_conversation_completion(
        self, 
        user_id: str, 
        conversation_id: str, 
        sentences_practiced: int,
        completion_percentage: float = 100.0
    ) -> Dict:
        """Record that a user completed a conversation"""
        try:
            completion_data = {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            # Upsert (insert or update if exists)
            result = self.client.table('user_conversation_completions').upsert(
                completion_data,
                on_conflict='user_id,conversation_id'
            ).execute()
            
            # Update user progress
            await self.update_user_stats(user_id, sentences_practiced)
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error recording completion: {str(e)}")
            raise e
    
    async def get_user_completions(self, user_id: str) -> List[Dict]:
        """Get all conversation completions for a user"""
        try:
            result = self.client.table('user_conversation_completions')\
                .select("*")\
                .eq('user_id', user_id)\
                .order('completed_at', desc=True)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user completions: {str(e)}")
            return []
    
    async def get_available_conversations(self, user_id: str) -> List[Dict]:
        """Get conversations that user hasn't completed yet"""
        try:
            # Get all library conversations
            all_convs = self.client.table('conversations')\
                .select("*")\
                .eq('is_library', True)\
                .execute()
            
            # Get user's completed conversation IDs
            completions = self.client.table('user_conversation_completions')\
                .select("conversation_id")\
                .eq('user_id', user_id)\
                .execute()
            
            completed_ids = [c['conversation_id'] for c in (completions.data or [])]
            
            # Filter out completed ones
            available = [
                conv for conv in (all_convs.data or [])
                if conv['id'] not in completed_ids
            ]
            
            return available
            
        except Exception as e:
            logger.error(f"Error getting available conversations: {str(e)}")
            return []
    
    # ========== User Progress & Stats ==========
    
    async def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        try:
            result = self.client.table('user_stats')\
                .select("*")\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                # Create default stats if not exist
                default_stats = {
                    'user_id': user_id,
                    'total_sentences': 0,
                    'total_expressions': 0,
                    'current_streak': 0,
                    'longest_streak': 0,
                    'last_practice_date': None
                }
                result = self.client.table('user_stats').insert(default_stats).execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}
    
    async def update_user_stats(self, user_id: str, sentences_practiced: int = 0) -> Dict:
        """Update user statistics after practice"""
        try:
            # Get current stats
            current = await self.get_user_stats(user_id)
            
            # Calculate streak
            today = date.today()
            last_practice = current.get('last_practice_date')
            current_streak = current.get('current_streak', 0)
            
            if last_practice:
                last_date = datetime.fromisoformat(last_practice).date()
                days_diff = (today - last_date).days
                
                if days_diff == 0:
                    # Same day, keep streak
                    pass
                elif days_diff == 1:
                    # Consecutive day
                    current_streak += 1
                else:
                    # Streak broken
                    current_streak = 1
            else:
                # First practice
                current_streak = 1
            
            # Get total conversations count first
            completions_result = self.client.table('user_conversation_completions')\
                .select("conversation_id")\
                .eq('user_id', user_id)\
                .execute()
            # Count of completions is not needed as total_conversations doesn't exist
            
            # Update stats
            updates = {
                'total_sentences': current.get('total_sentences', 0) + sentences_practiced,
                'current_streak': current_streak,
                'longest_streak': max(current_streak, current.get('longest_streak', 0)),
                'last_practice_date': today.isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('user_stats')\
                .update(updates)\
                .eq('user_id', user_id)\
                .execute()
            
            # Log daily practice
            await self.log_daily_practice(user_id, sentences_practiced)
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")
            return {}
    
    async def log_daily_practice(self, user_id: str, sentences_count: int) -> None:
        """Log daily practice for streak tracking"""
        try:
            today = date.today()
            
            # Check if entry exists for today
            existing = self.client.table('daily_practice_log')\
                .select("*")\
                .eq('user_id', user_id)\
                .eq('practice_date', today.isoformat())\
                .execute()
            
            if existing.data:
                # Update existing entry
                updates = {
                    'sentences_count': existing.data[0]['sentences_count'] + sentences_count,
                    'conversations_count': existing.data[0]['conversations_count'] + 1
                }
                self.client.table('daily_practice_log')\
                    .update(updates)\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Create new entry
                self.client.table('daily_practice_log').insert({
                    'user_id': user_id,
                    'practice_date': today.isoformat(),
                    'sentences_count': sentences_count,
                    'conversations_count': 1
                }).execute()
                
        except Exception as e:
            logger.error(f"Error logging daily practice: {str(e)}")
    
    # ========== Expressions ==========
    
    async def save_expression(
        self, 
        user_id: str, 
        expression: str, 
        translation: str,
        context: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """Save an expression for a user"""
        try:
            expression_data = {
                'user_id': user_id,
                'english_expression': expression,
                'korean_thought': translation,
                'context': context,
                'conversation_id': conversation_id,
                'mastery_level': 0,
                'practice_count': 0
            }
            
            result = self.client.table('saved_expressions').insert(expression_data).execute()
            
            # Update user stats
            stats = await self.get_user_stats(user_id)
            self.client.table('user_stats')\
                .update({'total_expressions': stats.get('total_expressions', 0) + 1})\
                .eq('user_id', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving expression: {str(e)}")
            raise e
    
    async def get_user_expressions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get saved expressions for a user"""
        try:
            result = self.client.table('saved_expressions')\
                .select("*")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting expressions: {str(e)}")
            return []
    
    async def delete_expression(self, expression_id: str, user_id: str) -> bool:
        """Delete an expression"""
        try:
            result = self.client.table('saved_expressions')\
                .delete()\
                .eq('id', expression_id)\
                .eq('user_id', user_id)\
                .execute()
            
            # Update user stats
            if result.data:
                stats = await self.get_user_stats(user_id)
                self.client.table('user_stats')\
                    .update({'total_expressions': max(0, stats.get('total_expressions', 1) - 1)})\
                    .eq('user_id', user_id)\
                    .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deleting expression: {str(e)}")
            return False
    
    # ========== Conversations ==========
    
    async def get_all_library_conversations(self) -> List[Dict]:
        """Get all library conversations"""
        try:
            result = self.client.table('conversations')\
                .select("*")\
                .eq('is_library', True)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting library conversations: {str(e)}")
            return []
    
    async def get_conversation_with_completion_status(self, user_id: str) -> List[Dict]:
        """Get all conversations with user's completion status"""
        try:
            # Get all library conversations
            conversations = await self.get_all_library_conversations()
            
            # Get user's completions
            completions = await self.get_user_completions(user_id)
            completion_map = {c['conversation_id']: c for c in completions}
            
            # Add completion status to each conversation
            for conv in conversations:
                if conv['id'] in completion_map:
                    conv['is_completed'] = True
                    conv['completion_data'] = completion_map[conv['id']]
                else:
                    conv['is_completed'] = False
                    conv['completion_data'] = None
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations with status: {str(e)}")
            return []


# Create singleton instance
supabase_service = SupabaseService()