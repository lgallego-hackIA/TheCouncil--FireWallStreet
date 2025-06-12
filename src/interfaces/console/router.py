"""
Console router for automation management commands.
"""
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.application.automation_registry.registry import AutomationRegistry
from src.application.automation_manager import AutomationManager
from src.domain.automation.models import (
    Automation, 
    AutomationStatus, 
    Endpoint,
    HttpMethod,
)
from src.interfaces.console.models import (
    CreateAutomationRequest,
    EndpointRequest,
    EndpointResponse,
    EndpointListResponse,
    MessageResponse
)
from src.shared.exceptions import (
    AutomationError, 
    AutomationNotFoundError
)

logger = logging.getLogger(__name__)

# Create console router
router = APIRouter(tags=["console"])


# Dependency to get AutomationRegistry
async def get_registry() -> AutomationRegistry:
    """Get the automation registry."""
    from src.main import automation_registry
    return automation_registry


async def get_automation_manager() -> AutomationManager:
    """Get the automation manager."""
    from src.main import automation_manager
    return automation_manager


# Response models
class AutomationListResponse(BaseModel):
    """Response for listing automations."""
    total: int = Field(..., description="Total number of automations")
    skip: int = Field(..., description="Number of automations skipped")
    limit: int = Field(..., description="Maximum number of automations returned")
    automations: List[Automation] = Field(..., description="List of automations")


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for the console API.
    """
    return {
        "service": "console",
        "status": "healthy",
        "message": "Console API is operating normally"
    }


@router.get("/automations", response_model=AutomationListResponse)
async def list_automations(
    status: Optional[AutomationStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationListResponse:
    """
    List all registered automations with optional filtering and pagination.
    """
    try:
        automations = await registry.get_all_automations()
        # Filter by status if specified
        if status:
            automations = [a for a in automations if a.status == status]
        
        # Apply pagination
        total_automations = len(automations)
        paginated_automations = automations[skip:skip + limit]
        
        return AutomationListResponse(
            total=total_automations,
            skip=skip,
            limit=limit,
            automations=paginated_automations
        )
    except Exception as e:
        logger.error(f"Error listing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))










