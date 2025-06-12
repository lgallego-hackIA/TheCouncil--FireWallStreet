"""
Domain models for automations and endpoints.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field


class HttpMethod(str, Enum):
    """HTTP methods for endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"



class AutomationStatus(str, Enum):
    """Status of an automation."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class ParamType(str, Enum):
    """Parameter types for endpoint parameters."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    FILE = "file"


class EndpointParameter(BaseModel):
    """Parameter for an endpoint."""
    name: str
    type: ParamType = ParamType.STRING
    description: str
    required: bool = True
    default: Optional[Any] = None


class Endpoint(BaseModel):
    """Endpoint configuration for an automation."""
    path: str
    method: HttpMethod
    summary: str
    description: str
    parameters: List[EndpointParameter] = Field(default_factory=list)
    response_model_name: Optional[str] = None  # Name of the response model class
    handler_path: Optional[str] = None  # Path to handler implementation
    requires_auth: bool = True
    active: bool = True
    wrap_response: bool = False
    single_item: bool = False  # For GET requests, indicates if this returns a single item
    id_field: Optional[str] = "id"  # Field to use as the identifier



class Automation(BaseModel):
    """Automation configuration."""
    id: str
    name: str
    description: str
    version: str
    base_path: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: AutomationStatus = AutomationStatus.DRAFT
    endpoints: List[Endpoint] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_endpoint(self, endpoint: Endpoint) -> None:
        """Add an endpoint to the automation."""
        self.endpoints.append(endpoint)
        self.updated_at = datetime.now()
    
    def remove_endpoint(self, path: str, method: HttpMethod) -> bool:
        """
        Remove an endpoint from the automation.
        
        Args:
            path: The path of the endpoint to remove
            method: The HTTP method of the endpoint to remove
            
        Returns:
            True if the endpoint was removed, False if it wasn't found
        """
        original_length = len(self.endpoints)
        self.endpoints = [
            e for e in self.endpoints 
            if not (e.path == path and e.method == method)
        ]
        
        if len(self.endpoints) < original_length:
            self.updated_at = datetime.now()
            return True
        
        return False
    
    def update_endpoint(self, path: str, method: HttpMethod, updated_endpoint: Endpoint) -> bool:
        """
        Update an endpoint in the automation.
        
        Args:
            path: The path of the endpoint to update
            method: The HTTP method of the endpoint to update
            updated_endpoint: The updated endpoint configuration
            
        Returns:
            True if the endpoint was updated, False if it wasn't found
        """
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.path == path and endpoint.method == method:
                self.endpoints[i] = updated_endpoint
                self.updated_at = datetime.now()
                return True
        
        return False
