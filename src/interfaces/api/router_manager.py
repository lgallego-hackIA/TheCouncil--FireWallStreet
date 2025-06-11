import logging
from fastapi import FastAPI, APIRouter, Request, BackgroundTasks
from typing import Dict, Any, Optional
from src.application.automation_registry.registry import AutomationRegistry
from src.domain.automation.models import Automation, Endpoint, AutomationStatus, HttpMethod
import importlib
import json
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
        self.app.include_router(router, prefix=prefix, tags=[f"Automation: {automation_name}"])
        self.routers[automation_id] = router
        logger.info(f"Router for automation '{automation_id}' (name: '{automation_name}') added with prefix '{prefix}'.")

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
                        # Prepare params for the handler (query and body)
                        query_params_dict = {k: v for k, v in request.query_params.items()}
                        params_for_handler = {"query_params": query_params_dict}

                        # Handle request body for relevant methods
                        if request.method in ["POST", "PUT", "PATCH"]:
                            body_bytes = await request.body()
                            if body_bytes:
                                try:
                                    params_for_handler["body"] = json.loads(body_bytes)
                                except json.JSONDecodeError:
                                    logger.warning(f"Request body for {request.method} {request.url.path} is not valid JSON.")
                                    params_for_handler["body"] = None
                            else:
                                params_for_handler["body"] = None
                        else:
                            params_for_handler["body"] = None # Ensure 'body' key exists
                        
                        logger.debug(f"Calling h_func: {h_func.__name__}")
                        logger.debug(f"Path params from request.path_params: {request.path_params}")
                        logger.debug(f"Params for handler (query/body): {params_for_handler}")

                        # Call the actual handler using the captured variables
                        return await h_func(
                            **request.path_params,  # Spread path parameters from request.path_params
                            params=params_for_handler,   # Pass the clean dict for query/body
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
            
            # Add a dedicated health check endpoint to the automation's router
            # This uses a default argument to capture the current automation's name and avoid late-binding issues
            @automation_router.get("/health", tags=[f"Health Checks", f"Automation: {automation.name}"])
            async def automation_health(name=automation.name):
                return {
                    "service": name,
                    "status": "healthy",
                    "message": f"{name} automation is operating normally"
                }
            logger.info(f"Health check endpoint added for '{automation.name}' at '{automation.base_path}/health'.")

            # Add the configured router for this automation
            self.add_router_for_automation(
                automation_id=automation.id,
                router=automation_router,
                prefix=automation.base_path, # Use the automation's base_path as the prefix
                automation_name=automation.name
            )
        logger.info("Finished registering automation routers.")


