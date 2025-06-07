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
    DatabaseConfig,
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


class AutomationResponse(BaseModel):
    """Response for automation operations."""
    automation: Automation = Field(..., description="Automation details")
    message: str = Field(..., description="Response message")


# CreateAutomationRequest is imported from models.py


class UpdateAutomationRequest(BaseModel):
    """Request to update an existing automation."""
    name: Optional[str] = Field(default=None, description="Automation name")
    description: Optional[str] = Field(default=None, description="Automation description")
    base_path: Optional[str] = Field(default=None, description="Base path for the automation endpoints")
    db_config: Optional[DatabaseConfig] = Field(default=None, description="Database configuration")
    status: Optional[AutomationStatus] = Field(default=None, description="Automation status")
    tags: Optional[List[str]] = Field(default=None, description="Tags for the automation")
    version: Optional[str] = Field(default=None, description="Automation version")
    owner: Optional[str] = Field(default=None, description="Automation owner")
    
    def dict(self, exclude_unset=True):
        """Convert to dictionary, excluding unset fields."""
        return self.model_dump(exclude_unset=exclude_unset)


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
        paginated_automations = automations[skip:skip + limit]
        
        return AutomationListResponse(
            total=len(automations),
            skip=skip,
            limit=limit,
            automations=paginated_automations
        )
    except Exception as e:
        logger.error(f"Error listing automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: str = Path(..., title="The ID of the automation to get"),
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Get a specific automation by ID.
    """
    try:
        automation = await registry.get_automation_by_id(automation_id)
        if not automation:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        return AutomationResponse(
            automation=automation,
            message=f"Successfully retrieved automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(
    request: CreateAutomationRequest,
    manager: AutomationManager = Depends(get_automation_manager)
) -> AutomationResponse:
    """
    Create a new automation with optional DDD structure generation.
    """
    try:
        # Prepare metadata dictionary
        metadata = {}
        if request.tags:
            metadata['tags'] = request.tags
        if request.owner:
            metadata['owner'] = request.owner
        
        # Create automation using the AutomationManager
        automation = await manager.create_automation(
            name=request.name,
            description=request.description,
            version=request.version,
            base_path=request.base_path,
            metadata=metadata,
            generate_ddd_structure=request.generate_ddd_structure
        )
        
        # Set the database configuration if provided
        if request.db_config:
            automation.db_config = request.db_config
            await manager.automation_registry.update_automation(request.name, automation)
        
        logger.info(f"Created automation {automation.id}, DDD structure: {request.generate_ddd_structure}")
        
        return AutomationResponse(
            automation=automation,
            message=f"Successfully created automation {automation.id}{' with DDD structure' if request.generate_ddd_structure else ''}"
        )
    except AutomationError as e:
        logger.error(f"Error creating automation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    request: UpdateAutomationRequest,
    automation_id: str = Path(..., title="The ID of the automation to update"),
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Update an existing automation.
    """
    try:
        # Get existing automation
        existing = await registry.get_automation_by_id(automation_id)
        if not existing:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Update fields from request
        update_data = request.dict(exclude_unset=True)
        updated_automation = existing.copy(update=update_data)
        
        # Update the automation in registry
        result = await registry.update_automation(existing.name, updated_automation)
        
        return AutomationResponse(
            automation=result,
            message=f"Successfully updated automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error updating automation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automations/{automation_id}", response_model=AutomationResponse)
async def delete_automation(
    automation_id: str = Path(..., title="The ID of the automation to delete"),
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Delete an automation.
    """
    try:
        # Get existing automation
        existing = await registry.get_automation_by_id(automation_id)
        if not existing:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Delete the automation
        await registry.delete_automation(automation_id)
        
        return AutomationResponse(
            automation=existing,
            message=f"Successfully deleted automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error deleting automation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations/{automation_id}/activate", response_model=AutomationResponse)
async def activate_automation(
    automation_id: str = Path(..., title="The ID of the automation to activate"),
    registry: AutomationRegistry = Depends(get_registry),
    manager: AutomationManager = Depends(get_automation_manager)
) -> AutomationResponse:
    """
    Activate an automation.
    """
    try:
        # Get existing automation
        existing = await registry.get_automation_by_id(automation_id)
        if not existing:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Use the automation manager to activate (this will register the router)
        result = await manager.activate_automation(existing.name)
        
        return AutomationResponse(
            automation=result,
            message=f"Successfully activated automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error activating automation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations/{automation_id}/deactivate", response_model=AutomationResponse)
async def deactivate_automation(
    automation_id: str = Path(..., title="The ID of the automation to deactivate"),
    registry: AutomationRegistry = Depends(get_registry),
    manager: AutomationManager = Depends(get_automation_manager)
) -> AutomationResponse:
    """
    Deactivate an automation.
    """
    try:
        # Get existing automation
        existing = await registry.get_automation_by_id(automation_id)
        if not existing:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Use the automation manager to deactivate (this will remove the router)
        result = await manager.deactivate_automation(existing.name)
        
        return AutomationResponse(
            automation=result,
            message=f"Successfully deactivated automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error deactivating automation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automations/{automation_id}/endpoints", response_model=AutomationResponse)
async def add_endpoint(
    automation_id: str,
    endpoint: Endpoint,
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Add a new endpoint to an automation.
    """
    try:
        # Get existing automation
        automation = await registry.get_automation_by_id(automation_id)
        if not automation:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Add endpoint to automation
        automation.endpoints.append(endpoint)
        
        # Update the automation in registry
        result = await registry.update_automation(automation.name, automation)
        
        return AutomationResponse(
            automation=result,
            message=f"Successfully added endpoint {endpoint.path} to automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error adding endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automations/{automation_id}/endpoints/{endpoint_id}", response_model=AutomationResponse)
async def update_endpoint(
    automation_id: str,
    endpoint_id: str,
    updated_endpoint: Endpoint,
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Update an endpoint in an automation.
    """
    try:
        # Get existing automation
        automation = await registry.get_automation_by_id(automation_id)
        if not automation:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Find the endpoint
        for i, endpoint in enumerate(automation.endpoints):
            if endpoint.id == endpoint_id:
                # Update the endpoint
                automation.endpoints[i] = updated_endpoint
                
                # Update the automation in registry
                result = await registry.update_automation(automation.name, automation)
                
                return AutomationResponse(
                    automation=result,
                    message=f"Successfully updated endpoint {endpoint_id} in automation {automation_id}"
                )
        
        # If we get here, the endpoint wasn't found
        raise HTTPException(
            status_code=404, 
            detail=f"Endpoint with ID {endpoint_id} not found in automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error updating endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automations/{automation_id}/endpoints/{endpoint_id}", response_model=AutomationResponse)
async def delete_endpoint(
    automation_id: str,
    endpoint_id: str,
    registry: AutomationRegistry = Depends(get_registry)
) -> AutomationResponse:
    """
    Delete an endpoint from an automation.
    """
    try:
        # Get existing automation
        automation = await registry.get_automation_by_id(automation_id)
        if not automation:
            raise AutomationNotFoundError(f"Automation with ID {automation_id} not found")
        
        # Find and remove the endpoint
        for i, endpoint in enumerate(automation.endpoints):
            if endpoint.id == endpoint_id:
                # Remove the endpoint
                removed_endpoint = automation.endpoints.pop(i)
                
                # Update the automation in registry
                result = await registry.update_automation(automation.name, automation)
                
                return AutomationResponse(
                    automation=result,
                    message=f"Successfully deleted endpoint {endpoint_id} from automation {automation_id}"
                )
        
        # If we get here, the endpoint wasn't found
        raise HTTPException(
            status_code=404, 
            detail=f"Endpoint with ID {endpoint_id} not found in automation {automation_id}"
        )
    except AutomationNotFoundError as e:
        logger.error(f"Automation not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AutomationError as e:
        logger.error(f"Error deleting endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
