"""
Common dependencies for API endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional

# Simple bearer token security for now
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """
    Get current user from auth token.
    For now, returns a dummy user for testing.
    In production, this would validate the JWT token.
    """
    # For testing, allow requests without authentication
    if not credentials:
        return {
            "id": "test-user",
            "email": "test@flowplane.ai",
            "is_active": True
        }
    
    # In production, validate the token here
    # For now, just return a test user
    return {
        "id": "authenticated-user",
        "email": "user@flowplane.ai",
        "is_active": True
    }