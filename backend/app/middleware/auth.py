from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from app.config import settings


security = HTTPBearer(auto_error=False)


def get_supabase_client():
    """Get Supabase client instance"""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )


async def verify_supabase_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify Supabase auth token and return user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    supabase = get_supabase_client()
    
    try:
        # Import asyncio for timeout
        import asyncio
        
        # Verify token with Supabase (with timeout)
        try:
            # Run the sync function with a timeout
            user_response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: supabase.auth.get_user(token)
                ),
                timeout=5.0  # 5 second timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication timeout",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user_response.user.id,
            "email": user_response.user.email,
            "user": user_response.user
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user from Supabase token"""
    return await verify_supabase_token(credentials)


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Optional authentication - returns user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await verify_supabase_token(credentials)
    except:
        return None


# Alias for backward compatibility
get_current_user_optional = optional_auth

# Backward compatibility - will be removed
def create_access_token(user_id: str, device_id: str = None) -> str:
    """Deprecated - Supabase handles tokens now"""
    # This is just for backward compatibility
    # Real auth is handled by Supabase
    return "supabase-handles-this"