"""
Pydantic models for the console interface API.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from src.domain.automation.models import (
    Automation,
    Endpoint, 
    HttpMethod,
    ParamType,
    EndpointParameter
)


class EndpointRequest(BaseModel):
    """Request to create or update an endpoint."""
    path: str = Field(..., description="Endpoint path (e.g., /users/{id})")
    method: HttpMethod = Field(..., description="HTTP method")
    summary: str = Field(..., description="Short summary of endpoint purpose")
    description: Optional[str] = Field(default="", description="Detailed description")
    parameters: List[EndpointParameter] = Field(default=[], description="Endpoint parameters")
    active: bool = Field(default=True, description="Whether the endpoint is active")
    requires_auth: bool = Field(default=False, description="Whether authentication is required")
    wrap_response: bool = Field(default=False, description="Whether to wrap the response in a data object")
    single_item: bool = Field(default=False, description="Whether this endpoint returns a single item")
    id_field: Optional[str] = Field(default=None, description="Field to use as ID for single item endpoints")


class EndpointResponse(BaseModel):
    """Response for endpoint operations."""
    endpoint: Endpoint
    message: str


class EndpointListResponse(BaseModel):
    """Response for listing endpoints."""
    total: int
    endpoints: List[Endpoint]
    automation_id: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class CreateAutomationRequest(BaseModel):
    """Request to create a new automation."""
    name: str = Field(..., description="Unique name for the automation")
    description: str = Field(..., description="Description of the automation's purpose")
    base_path: str = Field(..., description="Base path for all endpoints (e.g., /api/v1)")
    version: str = Field("1.0.0", description="Version of the automation")
    endpoints: List[EndpointRequest] = Field(default=[], description="List of endpoints for this automation")
    tags: List[str] = Field(default=[], description="Tags for categorizing the automation")
    owner: str = Field("system", description="Owner of the automation")
    generate_ddd_structure: bool = Field(False, description="Whether to generate DDD structure files for the automation")
