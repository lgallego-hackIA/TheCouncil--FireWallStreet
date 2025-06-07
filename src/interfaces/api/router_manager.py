"""
Router Manager for managing dynamic FastAPI routers.
"""
import logging
from typing import Dict, List, Optional, Type

from fastapi import APIRouter, FastAPI, Request, BackgroundTasks, Response

from src.application.automation_registry.registry import AutomationRegistry
from src.application.endpoint_handler.handler import EndpointHandler
from src.domain.automation.models import Automation
from src.infrastructure.database_factory import DatabaseFactory

logger = logging.getLogger(__name__)


class RouterManager:
    """
    Manages dynamic creation and registration of FastAPI routers based on registered automations.
    """

    def __init__(self, app: FastAPI, automation_registry: AutomationRegistry):
        """
        Initialize the router manager.
        
        Args:
            app: The FastAPI application instance
            automation_registry: The automation registry containing registered automations
        """
        self.app = app
        self.automation_registry = automation_registry
        self.routers: Dict[str, APIRouter] = {}
        
        # Create endpoint handler for processing requests
        self.endpoint_handler = EndpointHandler(DatabaseFactory())

    async def register_all_routers(self) -> None:
        """
        Register all routers from registered automations.
        This should be called during application startup.
        """
        automations = await self.automation_registry.get_all_automations()
        for automation in automations:
            await self.register_router(automation)
            
    async def register_router(self, automation: Automation) -> None:
        """
        Create and register a router for an automation.
        
        Args:
            automation: The automation to create a router for
        """
        if automation.name in self.routers:
            logger.warning(f"Router for automation '{automation.name}' already registered")
            return

        # Create a new router for the automation
        router = APIRouter(
            prefix=automation.base_path,
            tags=[automation.name],
        )
        
        # Add the automation's endpoints to the router
        await self._add_endpoints_to_router(router, automation)
        
        # Register the router with the FastAPI app
        self.app.include_router(router)
        self.routers[automation.name] = router
        logger.info(f"Registered router for automation: {automation.name}")
        
    async def _add_endpoints_to_router(self, router: APIRouter, automation: Automation) -> None:
        """
        Add endpoints to the router based on automation configuration.
        
        Args:
            router: The router to add endpoints to
            automation: The automation containing endpoint definitions
        """
        for endpoint in automation.endpoints:
            # Skip inactive endpoints
            if not endpoint.active:
                logger.debug(f"Skipping inactive endpoint: {endpoint.method} {automation.name}{endpoint.path}")
                continue
                
            # Determine the appropriate handler for the endpoint
            handler = await self._get_endpoint_handler(endpoint, automation)
            
            # Register the endpoint with the router
            router.add_api_route(
                path=endpoint.path,
                endpoint=handler,
                methods=[endpoint.method.value],  # Use the string value of the enum
                # Don't specify response_model to allow dynamic responses
                summary=endpoint.summary,
                description=endpoint.description,
                # Allow the handler to return a Response object directly
                response_class=Response,
            )
            
            logger.debug(
                f"Added endpoint: {endpoint.method} {automation.name}{endpoint.path}"
            )
    
    async def _get_endpoint_handler(self, endpoint, automation):
        """
        Get or create an appropriate handler function for the endpoint.
        
        Args:
            endpoint: The endpoint configuration
            automation: The parent automation
            
        Returns:
            A handler function suitable for FastAPI
        """
        # Create a closure over the automation and endpoint
        async def dynamic_handler(request: Request, background_tasks: BackgroundTasks = None):
            """Dynamic handler for automation endpoints."""
            # Use the endpoint handler to process the request
            return await self.endpoint_handler.handle_request(
                request=request,
                automation=automation,
                endpoint=endpoint,
                background_tasks=background_tasks
            )
            
        return dynamic_handler
    
    async def update_router(self, automation_name: str) -> None:
        """
        Update a router with changes to its automation.
        
        Args:
            automation_name: The name of the automation to update
        """
        # Remove the existing router if it exists
        if automation_name in self.routers:
            # FastAPI doesn't have a built-in way to remove routers
            # For now, we'll re-create all routers on update (not ideal for production)
            await self.register_all_routers()
            logger.info(f"Updated router for automation: {automation_name}")
        else:
            # If the router doesn't exist, register it
            automation = await self.automation_registry.get_automation(automation_name)
            if automation:
                await self.register_router(automation)
                
    async def remove_router(self, automation_name: str) -> bool:
        """
        Remove a router for an automation.
        
        Args:
            automation_name: The name of the automation whose router should be removed
            
        Returns:
            True if the router was removed, False otherwise
        """
        if automation_name not in self.routers:
            logger.warning(f"Router for automation '{automation_name}' not found")
            return False
            
        # FastAPI doesn't have a built-in way to remove routers
        # We'll need to recreate the app routes without this router
        # This is a simple implementation - in production, you might want
        # a more sophisticated approach
        
        # Remove from our router registry
        del self.routers[automation_name]
        logger.info(f"Removed router for automation: {automation_name}")
        
        # Re-register all routers except the removed one
        # This is not ideal for production as it rebuilds all routes
        await self.register_all_routers()
        
        return True
