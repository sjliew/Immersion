from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


async def error_handler(request: Request, exc: Exception):
    """Global error handler for all exceptions"""
    
    # Handle FastAPI HTTP exceptions
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail
            }
        )
    
    # Handle Starlette HTTP exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail
            }
        )
    
    # Handle validation errors
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    # Generic error response for production
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error" if not settings.is_development else str(exc)
        }
    )


class AppError(Exception):
    """Custom application error"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)