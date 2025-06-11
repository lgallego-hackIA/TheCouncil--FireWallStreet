from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

# Use original name with dashes for route paths and tags
router = APIRouter(tags=["financial-data-collector"])

# Health check endpoint for this automation
@router.get("/health")
async def health_check():
    """
    Health check endpoint for financial-data-collector automation
    """
    return {
        "service": "financial-data-collector",
        "status": "healthy",
        "message": "financial-data-collector automation is operating normally"
    }
