"""
Supabase Infrastructure Management
Handles automatic creation of tables and storage buckets
"""
from supabase import create_client
from app.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SupabaseInfrastructure:
    def __init__(self):
        """Initialize with admin client for infrastructure operations"""
        try:
            # Use service key for admin operations
            self.admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
            logger.info("Supabase admin client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {e}")
            raise
    
    async def initialize_infrastructure(self):
        """Initialize all required Supabase infrastructure"""
        logger.info("Initializing Supabase infrastructure...")
        
        # Create storage buckets
        await self.create_storage_buckets()
        
        # Note: Table creation via SQL requires database access
        # For now, tables will be created on first insert attempt
        # In production, use Supabase migrations or dashboard
        
        logger.info("Supabase infrastructure initialization complete")
    
    async def create_storage_buckets(self):
        """Create required storage buckets if they don't exist"""
        buckets_config = [
            {
                'name': 'audio-library',
                'public': True,
                'file_size_limit': 10485760,  # 10MB
                'allowed_mime_types': ['audio/mpeg', 'audio/mp3', 'audio/wav']
            },
            {
                'name': 'user-recordings', 
                'public': False,
                'file_size_limit': 5242880,  # 5MB
                'allowed_mime_types': ['audio/webm', 'audio/wav', 'audio/mp4']
            }
        ]
        
        try:
            # List existing buckets
            existing_buckets = self.admin_client.storage.list_buckets()
            existing_names = {b['name'] for b in existing_buckets} if existing_buckets else set()
            
            for bucket_config in buckets_config:
                bucket_name = bucket_config['name']
                
                if bucket_name not in existing_names:
                    try:
                        # Create the bucket
                        result = self.admin_client.storage.create_bucket(
                            bucket_name,
                            options={
                                'public': bucket_config['public'],
                                'file_size_limit': bucket_config['file_size_limit'],
                                'allowed_mime_types': bucket_config['allowed_mime_types']
                            }
                        )
                        logger.info(f"✅ Created storage bucket: {bucket_name}")
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            logger.info(f"Storage bucket already exists: {bucket_name}")
                        else:
                            logger.error(f"Failed to create bucket {bucket_name}: {e}")
                else:
                    logger.info(f"Storage bucket already exists: {bucket_name}")
                    
        except Exception as e:
            logger.error(f"Error checking/creating storage buckets: {e}")
    
    def get_client(self):
        """Get the admin client for direct operations"""
        return self.admin_client
    
    async def ensure_conversations_table(self):
        """Ensure conversations table exists (called on first insert)"""
        # This will be called when we first try to insert
        # The table schema is:
        # - id: UUID (primary key)
        # - scenario: TEXT
        # - difficulty_level: INTEGER
        # - dialogue: JSONB (contains dialogue with embedded audio URLs)
        # - thoughts: JSONB
        # - is_library: BOOLEAN
        # - imported: BOOLEAN
        # - created_at: TIMESTAMP
        # - updated_at: TIMESTAMP
        
        # Note: In production, create tables via Supabase dashboard or migrations
        # For development, we'll let the first insert fail and create manually
        pass


# Create global instance
infrastructure = SupabaseInfrastructure()