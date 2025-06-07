"""
Dynamic endpoint handler for processing automation requests.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union

from fastapi import BackgroundTasks, Request, Response, status
from pydantic import BaseModel, ValidationError, create_model
from starlette.datastructures import FormData, UploadFile

from src.domain.automation.models import Automation, Endpoint, HttpMethod, EndpointParameter, ParamType
from src.infrastructure.database_factory import DatabaseFactory
from src.shared.exceptions import DatabaseError, ValidationError as TheCouncilValidationError

logger = logging.getLogger(__name__)


class EndpointHandler:
    """
    Handler for processing dynamic endpoint requests.
    
    This class is responsible for:
    1. Validating incoming requests against endpoint definitions
    2. Processing data based on automation logic
    3. Interacting with the appropriate database
    4. Formatting and returning responses
    """

    def __init__(self, database_factory: DatabaseFactory = None):
        """
        Initialize the endpoint handler.
        
        Args:
            database_factory: Factory for creating database repositories
        """
        self.database_factory = database_factory or DatabaseFactory()

    async def handle_request(
        self, 
        request: Request, 
        automation: Automation, 
        endpoint: Endpoint,
        background_tasks: BackgroundTasks = None
    ) -> Response:
        """
        Handle a request to a dynamic endpoint.
        
        Args:
            request: The incoming FastAPI request
            automation: The automation that the endpoint belongs to
            endpoint: The specific endpoint configuration
            background_tasks: Optional background tasks queue
            
        Returns:
            Response object
        """
        logger.debug(f"Handling request for endpoint: {endpoint.path}")

        try:
            # 1. Extract and validate parameters
            params = await self._extract_parameters(request, endpoint)
            
            # 2. Execute the request processing logic
            result = await self._process_request(automation, endpoint, params, background_tasks)
            
            # 3. Format the response
            response_data = self._format_response(endpoint, result)
            
            # 4. Return the response with appropriate status code
            status_code = self._get_success_status_code(endpoint.method)
            return Response(
                content=json.dumps(response_data),
                media_type="application/json",
                status_code=status_code
            )
            
        except TheCouncilValidationError as e:
            logger.error(f"Validation error: {e}")
            return Response(
                content=json.dumps({"error": str(e), "type": "validation_error"}),
                media_type="application/json",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return Response(
                content=json.dumps({"error": str(e), "type": "database_error"}),
                media_type="application/json",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return Response(
                content=json.dumps({"error": "Internal server error", "type": "server_error"}),
                media_type="application/json",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _extract_parameters(self, request: Request, endpoint: Endpoint) -> Dict[str, Any]:
        """
        Extract and validate parameters from the request.
        
        Args:
            request: The incoming request
            endpoint: The endpoint configuration
            
        Returns:
            Dictionary of validated parameters
            
        Raises:
            ValidationError: If parameter validation fails
        """
        params = {}
        
        # Create a dynamic validation model based on endpoint parameters
        fields = {}
        for param in endpoint.parameters:
            # Convert parameter type to Pydantic field type
            field_type = self._get_field_type(param.type)
            
            # Add the field to our dynamic model
            fields[param.name] = (
                field_type,
                ... if param.required else None
            )
        
        # Create a Pydantic model for validation
        ValidationModel = create_model('ValidationModel', **fields) if fields else None

        # Extract path parameters
        path_params = request.path_params
        for param_name, param_value in path_params.items():
            params[param_name] = param_value

        # Extract query parameters
        query_params = dict(request.query_params)
        for param_name, param_value in query_params.items():
            params[param_name] = param_value

        # Extract body parameters for POST, PUT, PATCH
        if endpoint.method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        params.update(body)
                except json.JSONDecodeError:
                    raise TheCouncilValidationError("Invalid JSON body")
                    
            elif "application/x-www-form-urlencoded" in content_type:
                form_data = await request.form()
                for key, value in form_data.items():
                    params[key] = value
                    
            elif "multipart/form-data" in content_type:
                form_data = await request.form()
                for key, value in form_data.items():
                    if isinstance(value, UploadFile):
                        # Store file content for now
                        params[key] = value
                    else:
                        params[key] = value

        # Validate parameters against the endpoint configuration
        if ValidationModel:
            try:
                validated_data = ValidationModel(**params)
                return validated_data.dict()
            except ValidationError as e:
                # Convert Pydantic validation error to our custom error
                error_msgs = []
                for error in e.errors():
                    loc = ".".join(str(x) for x in error["loc"])
                    error_msgs.append(f"{loc}: {error['msg']}")
                
                error_message = "; ".join(error_msgs)
                raise TheCouncilValidationError(f"Parameter validation failed: {error_message}")
        
        return params

    def _get_field_type(self, param_type: ParamType) -> Type:
        """Get the Pydantic field type for a parameter type."""
        type_map = {
            ParamType.STRING: str,
            ParamType.INTEGER: int,
            ParamType.FLOAT: float,
            ParamType.BOOLEAN: bool,
            ParamType.OBJECT: Dict[str, Any],
            ParamType.ARRAY: List[Any],
            ParamType.FILE: UploadFile,
        }
        return type_map.get(param_type, str)

    async def _process_request(
        self, 
        automation: Automation, 
        endpoint: Endpoint, 
        params: Dict[str, Any],
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process the request and generate a response.
        
        Args:
            automation: The automation that the endpoint belongs to
            endpoint: The specific endpoint configuration
            params: Validated parameters from the request
            background_tasks: Optional background tasks queue
            
        Returns:
            Response data
        """
        # Determine the entity type based on the automation/endpoint
        # In a real implementation, this would be more sophisticated
        entity_type = Dict[str, Any]
        
        # Create a repository for the automation's database
        repository = self.database_factory.create_repository(
            entity_type=entity_type,
            db_config=automation.db_config
        )
        
        # Execute the appropriate database operation based on the endpoint method
        if endpoint.method == HttpMethod.GET:
            # Handle GET requests
            if endpoint.single_item:
                # Get a single item by ID
                item_id = params.get(endpoint.id_field or 'id')
                if not item_id:
                    raise TheCouncilValidationError(f"Missing required ID field: {endpoint.id_field or 'id'}")
                
                result = await repository.get_by_id(item_id)
                return result or {}
            else:
                # List items with optional filtering
                filters = {}
                for field_name, field_value in params.items():
                    # Add filters from query parameters
                    filters[field_name] = field_value
                
                # Get pagination parameters with safe type conversion
                try:
                    offset = int(params.get('offset', 0) or 0)
                except (TypeError, ValueError):
                    offset = 0
                    
                try:
                    limit = int(params.get('limit', 100) or 100)
                    limit = min(limit, 100)  # Cap at 100
                except (TypeError, ValueError):
                    limit = 100
                
                items = await repository.find(filters, limit, offset)
                total = await repository.count(filters)
                
                return {
                    "items": items,
                    "total": total,
                    "offset": offset,
                    "limit": limit
                }
                
        elif endpoint.method == HttpMethod.POST:
            # Handle POST requests
            result = await repository.create(params)
            return result
            
        elif endpoint.method == HttpMethod.PUT:
            # Handle PUT requests
            item_id = params.get(endpoint.id_field or 'id')
            if not item_id:
                raise TheCouncilValidationError(f"Missing required ID field: {endpoint.id_field or 'id'}")
            
            result = await repository.update(params)
            return result or {}
            
        elif endpoint.method == HttpMethod.DELETE:
            # Handle DELETE requests
            item_id = params.get(endpoint.id_field or 'id')
            if not item_id:
                raise TheCouncilValidationError(f"Missing required ID field: {endpoint.id_field or 'id'}")
            
            success = await repository.delete(item_id)
            return {"success": success, "id": item_id}
            
        elif endpoint.method == HttpMethod.PATCH:
            # Handle PATCH requests
            item_id = params.get(endpoint.id_field or 'id')
            if not item_id:
                raise TheCouncilValidationError(f"Missing required ID field: {endpoint.id_field or 'id'}")
            
            # Get existing item
            existing = await repository.get_by_id(item_id)
            if not existing:
                raise TheCouncilValidationError(f"Item with ID {item_id} not found")
            
            # Update only provided fields
            if isinstance(existing, dict):
                for key, value in params.items():
                    if key != endpoint.id_field and key != 'id':
                        existing[key] = value
            else:
                for key, value in params.items():
                    if key != endpoint.id_field and key != 'id' and hasattr(existing, key):
                        setattr(existing, key, value)
            
            result = await repository.update(existing)
            return result or {}
        
        # If we get here, the method is not supported
        raise NotImplementedError(f"Method {endpoint.method} not implemented")

    def _format_response(self, endpoint: Endpoint, result: Any) -> Dict[str, Any]:
        """
        Format the response according to the endpoint configuration.
        
        Args:
            endpoint: The endpoint configuration
            result: The raw result from processing
            
        Returns:
            Formatted response data
        """
        # In a more complex implementation, we would apply transformations
        # based on the endpoint configuration
        
        # Apply basic wrapping if configured
        if endpoint.wrap_response:
            return {
                "data": result,
                "success": True
            }
        
        # Otherwise return the raw result
        return result

    def _get_success_status_code(self, method: HttpMethod) -> int:
        """Get the appropriate success status code for an HTTP method."""
        if method == HttpMethod.POST:
            return status.HTTP_201_CREATED
        elif method == HttpMethod.DELETE:
            return status.HTTP_204_NO_CONTENT
        else:
            return status.HTTP_200_OK
