import logging
from fastapi import FastAPI, APIRouter, Request, BackgroundTasks
from typing import Dict, Any
from src.application.automation_registry.registry import AutomationRegistry
from src.domain.automation.models import Automation, Endpoint, AutomationStatus, HttpMethod
import importlib
import inspect

logger = logging.getLogger(__name__)

class RouterManager:
    def __init__(self, app: FastAPI, automation_registry: AutomationRegistry):
        self.app = app
        self.routers: Dict[str, APIRouter] = {} # To store automation-specific routers
        self.automation_registry = automation_registry
        logger.info("RouterManager initialized with automation registry.")

    def add_router(self, prefix: str, router: APIRouter, tags: list[str] = None):
        """
        Includes a router in the FastAPI application.
        """
        if tags is None:
            tags = []
        self.app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"Router with prefix '{prefix}' added.")

    def add_router_for_automation(self, automation_id: str, router: APIRouter, prefix: str = None, automation_name: str = None):
        """
        Adds and stores a router specifically for an automation.
        The actual prefix under which it's served will depend on the automation's configuration.
        """
        effective_prefix = prefix or f"/{automation_id}" # Placeholder logic
        effective_automation_name = automation_name or automation_id
        
        # Use the provided prefix and automation_name directly
        self.app.include_router(router, prefix=prefix, tags=[f"Automation: {automation_name}"])
        self.routers[automation_id] = router
        logger.info(f"Router for automation '{automation_id}' (name: '{automation_name}') added with prefix '{prefix}'.")
        
        # Add health check endpoint for this automation
        self.add_health_check_for_automation(automation_name, automation_id)

    def remove_router_for_automation(self, automation_id: str):
        """
        Removes a router for an automation.
        Note: FastAPI doesn't directly support removing routers after they've been included.
        This method would typically prevent new requests from reaching it or rely on a server restart.
        Based on memory 3ec1b4f3-8ec4-4995-981b-f47ca14473eb, a restart is needed for changes to take effect.
        """
        if automation_id in self.routers:
            logger.info(
                f"Router for automation '{automation_id}' marked for removal from RouterManager's tracking. "
                f"A server restart is required for the routes to be fully removed."
            )
            del self.routers[automation_id]
        else:
            logger.warning(f"Router for automation '{automation_id}' not found for removal.")

    def add_health_check_for_automation(self, automation_name: str, automation_id: str):
        """
        Adds a dedicated health check endpoint for a specific automation.
        Based on memory 3ec1b4f3-8ec4-4995-981b-f47ca14473eb.
        The health check path is /[automation_name]/health.
        """
        health_router = APIRouter()
        # The health path is relative to the automation's base path if routers are nested,
        # or absolute if health checks are registered at the top level prefixed by automation name.
        # Memory suggests /automation-name/health, implying it's a top-level path segment.
        health_path = "/health" # This will be prefixed by the automation_name router itself.

        # Create a new router for the health check, to be mounted under /automation_name
        automation_base_router = APIRouter()

        @automation_base_router.get(health_path, tags=[f"Health Checks", f"Automation: {automation_name}"])
        async def automation_health():
            return {
                "service": automation_name,
                "status": "healthy",
                "message": f"{automation_name} automation is operating normally"
            }
        
        # Mount this health router under the automation_name prefix
        self.app.include_router(automation_base_router, prefix=f"/{automation_name}")
        logger.info(f"Health check endpoint added for automation '{automation_name}' at '/{automation_name}{health_path}'.")

    def get_all_routers(self) -> Dict[str, APIRouter]:
        return self.routers

    async def register_all_routers(self) -> None:
        """
        Registers API routes for all active automations found in the registry.
        This method is typically called at application startup.
        """
        logger.info("Registering all automation routers...")
        automations = await self.automation_registry.get_all_automations()
        if not automations:
            logger.info("No automations found in the registry to register.")
            return

        for automation in automations:
            if automation.status != AutomationStatus.ACTIVE:
                logger.info(f"Skipping registration for inactive automation: {automation.name}")
                continue

            logger.info(f"Registering routes for active automation: {automation.name} (ID: {automation.id})")
            automation_router = APIRouter()

            if not automation.endpoints:
                logger.warning(f"Automation '{automation.name}' has no endpoints defined.")
            
            for endpoint_config in automation.endpoints:
                if not endpoint_config.active:
                    logger.info(f"Skipping inactive endpoint: {endpoint_config.method.value} {endpoint_config.path} for automation {automation.name}")
                    continue
                
                if not endpoint_config.handler_path:
                    logger.error(f"Endpoint {endpoint_config.path} for {automation.name} is missing handler_path. Skipping.")
                    continue

                try:
                    module_str, func_name = endpoint_config.handler_path.rsplit('.', 1)
                    module = importlib.import_module(module_str)
                    handler_func = getattr(module, func_name)
                    
                    # Determine if response_model needs to be dynamically imported
                    # For now, assume handlers are typed or FastAPI infers it.
                    # response_model = None
                    # if endpoint_config.response_model_name:
                    #     try:
                    #         response_model_module_str, response_model_class_name = endpoint_config.response_model_name.rsplit('.', 1)
                    #         response_model_module = importlib.import_module(response_model_module_str)
                    #         response_model = getattr(response_model_module, response_model_class_name)
                    #     except Exception as e:
                    #         logger.error(f"Could not load response model {endpoint_config.response_model_name} for {automation.name} - {endpoint_config.path}: {e}")

                    async def handler_func_wrapper(
                        request: Request,
                        background_tasks: BackgroundTasks,
                        # Capture loop variables as default arguments to solve late-binding issue
                        h_func=handler_func,
                        e_config=endpoint_config,
                        current_automation=automation  # Capture the current automation object
                    ) -> Dict[str, Any]:
                        # Convert query_params from starlette's MultiDict to a simple dict
                        query_params_dict = {k: v for k, v in request.query_params.items()}
                        
                        # Merge path and query parameters
                        # Path parameters take precedence if names collide
                        merged_params = {**query_params_dict, **request.path_params}

                        # Call the actual handler using the captured variables
                        return await h_func(
                            params=merged_params,
                            repository=None, # Placeholder
                            automation=current_automation, # Use the captured automation object
                            endpoint=e_config,
                            background_tasks=background_tasks
                        )
                    
                    automation_router.add_api_route(
                        path=endpoint_config.path,
                        endpoint=handler_func_wrapper,
                        methods=[endpoint_config.method.value.upper()],
                        tags=[automation.name],
                        response_model=Dict # Explicitly set response model to Dict
                        # Consider adding other parameters if needed
                    )
                    logger.info(f"Successfully registered endpoint: {endpoint_config.method.value} {automation.base_path}{endpoint_config.path} for {automation.name}")
                except ImportError as e:
                    logger.error(f"Failed to import module for handler {endpoint_config.handler_path} for automation {automation.name}: {e}")
                except AttributeError as e:
                    logger.error(f"Failed to find handler function {func_name} in module {module_str} for automation {automation.name}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error registering endpoint {endpoint_config.path} for {automation.name}: {e}")
            
            # Add the configured router for this automation
            # The add_router_for_automation method will also add the health check
            self.add_router_for_automation(
                automation_id=automation.id,
                router=automation_router,
                prefix=automation.base_path, # Use the automation's base_path as the prefix
                automation_name=automation.name
            )
        logger.info("Finished registering automation routers.")

# Example usage (for testing or if RouterManager is used independently)
if __name__ == '__main__':
    app_instance = FastAPI()
    # For example usage, we'd need a mock or real AutomationRegistry
    # from src.application.automation_registry.registry import AutomationRegistry # Already imported above
    # class MockAutomationRegistry:
    #     def get_automation_by_id(self, automation_id):
    #         return None # Or a mock automation object
    # mock_registry = MockAutomationRegistry()
    # router_manager = RouterManager(app_instance, mock_registry)
    # The example below won't run directly without a registry, commenting out for now
    # router_manager = RouterManager(app_instance, None) # This would fail, needs a registry

    sample_router = APIRouter()
    @sample_router.get("/test")
    async def test_endpoint():
        return {"message": "Test"}
    router_manager.add_router("/sample", sample_router, tags=["Sample"])

    automation_specific_router = APIRouter()
    @automation_specific_router.get("/data")
    async def get_automation_data():
        return {"data": "some automation data"}
    
    # When add_router_for_automation is called, it will also set up /my_automation_123/health
    router_manager.add_router_for_automation(
        automation_id="auto123", 
        router=automation_specific_router, 
        prefix="/automations/my_automation_123", 
        automation_name="my_automation_123"
    )

    # To run and see: uvicorn <filename>:app_instance --reload (replace <filename>)
    # Access: /sample/test
    # Access: /automations/my_automation_123/data
    # Access: /my_automation_123/health
