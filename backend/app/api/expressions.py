from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.config.supabase import supabase
from app.middleware.auth import get_current_user

router = APIRouter()


class SaveExpressionRequest(BaseModel):
    expression: str
    translation: str
    context: Optional[str] = None
    category: Optional[str] = None


@router.post("/save")
async def save_expression(
    data: SaveExpressionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save an expression for later review"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Save expression
        saved = await supabase.save_expression(
            user_id=user['id'],
            expression=data.expression,
            translation=data.translation,
            context=data.context,
            category=data.category
        )
        
        if not saved:
            raise HTTPException(status_code=400, detail="Failed to save expression")
        
        return {"status": "success", "data": saved}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_saved_expressions(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get user's saved expressions"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get expressions
        expressions = await supabase.get_user_expressions(user['id'], limit)
        
        return {
            "status": "success",
            "data": expressions or [],
            "count": len(expressions) if expressions else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{expression_id}")
async def delete_expression(
    expression_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved expression"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete expression
        deleted = await supabase.delete_expression(expression_id, user['id'])
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Expression not found")
        
        return {"status": "success", "message": "Expression deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_expressions(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Search user's saved expressions"""
    try:
        # Get user profile
        user = await supabase.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Search in saved_expressions table
        result = supabase.client.table("saved_expressions")\
            .select("*")\
            .eq("user_id", user['id'])\
            .or_(f"expression.ilike.%{query}%,translation.ilike.%{query}%")\
            .order("created_at", desc=True)\
            .execute()
        
        return {
            "status": "success",
            "data": result.data or [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))