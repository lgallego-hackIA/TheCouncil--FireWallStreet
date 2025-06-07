"""
AutomationManager for handling the lifecycle of automations and their endpoints.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from src.application.automation_registry.registry import AutomationRegistry
from src.domain.automation.models import Automation, AutomationStatus, Endpoint
from src.interfaces.api.router_manager import RouterManager
from src.shared.exceptions import AutomationNotFoundError, EndpointNotFoundError

logger = logging.getLogger(__name__)


class AutomationManager:
    """
    Manager for automation lifecycle and endpoint operations.
    
    This class coordinates between the AutomationRegistry and RouterManager
    to ensure that changes to automations are properly reflected in the API.
    """
    
    def __init__(
        self, 
        app: FastAPI,
        automation_registry: AutomationRegistry,
        router_manager: Optional[RouterManager] = None
    ):
        """
        Initialize the automation manager.
        
        Args:
            app: The FastAPI application instance
            automation_registry: The registry of automations
            router_manager: Optional router manager (created if not provided)
        """
        self.app = app
        self.automation_registry = automation_registry
        self.router_manager = router_manager or RouterManager(app, automation_registry)
    
    async def initialize(self) -> None:
        """
        Initialize the automation manager.
        
        This method is called during application startup to load
        all existing automations and register their API routes.
        """
        # Load automations from storage
        await self.automation_registry.load_automations()
        
        # Register API routes for all active automations
        await self.router_manager.register_all_routers()
        
        logger.info("Automation manager initialized")
    
    async def create_automation(
        self, 
        name: str, 
        description: str,
        version: str = "1.0.0",
        base_path: str = None,
        metadata: Dict[str, Any] = None,
        generate_ddd_structure: bool = False
    ) -> Automation:
        """
        Create a new automation with optional DDD structure generation.
        
        Args:
            name: Name of the automation
            description: Description of the automation
            version: Version of the automation
            base_path: Base path for API endpoints
            metadata: Optional metadata for the automation
            generate_ddd_structure: Whether to generate DDD structure files
            
        Returns:
            The created automation
        """
        # Create the automation in the registry
        automation = await self.automation_registry.create_automation(name, description, base_path=base_path)
        
        # Update additional fields if provided
        if version:
            automation.version = version
        if base_path:
            automation.base_path = base_path
        if metadata:
            automation.metadata = metadata
        
        # Save the updated automation
        await self.automation_registry.update_automation(name, automation)
        
        # Generate DDD structure files if requested
        if generate_ddd_structure:
            await self._generate_ddd_structure(automation)
        
        return automation
    
    async def activate_automation(self, name: str) -> Automation:
        """
        Activate an automation.
        
        Args:
            name: Name of the automation to activate
            
        Returns:
            The activated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
        """
        # Get the automation from the registry
        automation = await self.automation_registry.get_automation(name)
        if not automation:
            raise AutomationNotFoundError(f"Automation '{name}' not found")
        
        # Update the status to active
        automation.status = AutomationStatus.ACTIVE
        
        # Save the updated automation
        await self.automation_registry.update_automation(name, automation)
        
        # Register/update the router for this automation
        await self.router_manager.update_router(name)
        
        logger.info(f"Activated automation: {name}")
        return automation
    
    async def _generate_ddd_structure(self, automation: Automation) -> None:
        """
        Generate DDD structure files for an automation.
        
        Args:
            automation: The automation to generate files for
        """
        import os
        import importlib.resources as pkg_resources
        from pathlib import Path
        
        # Base directory for automations code
        base_dir = Path(f"src/domain/automations/{automation.name}")
        os.makedirs(base_dir, exist_ok=True)
        
        # Create domain layer
        domain_dir = base_dir / "domain"
        os.makedirs(domain_dir, exist_ok=True)
        
        # Create domain model files
        with open(domain_dir / "models.py", "w") as f:
            f.write(f'''"""\nDomain models for {automation.name} automation.\n"""\nfrom pydantic import BaseModel\nfrom typing import List, Optional\nfrom datetime import datetime\n\n# TODO: Define your domain models here\nclass {automation.name.capitalize()}Item(BaseModel):\n    """Example domain model for {automation.name}."""\n    id: Optional[str] = None\n    name: str\n    description: Optional[str] = None\n    created_at: datetime = datetime.now()\n    updated_at: datetime = datetime.now()\n''')
        
        # Create domain service files
        with open(domain_dir / "service.py", "w") as f:
            f.write(f'''"""\nDomain services for {automation.name} automation.\n"""\nfrom typing import List, Optional\nfrom .models import {automation.name.capitalize()}Item\n\nclass {automation.name.capitalize()}Service:\n    """Service for {automation.name} domain logic."""\n    \n    async def process_item(self, item: {automation.name.capitalize()}Item) -> {automation.name.capitalize()}Item:\n        """\n        Process business logic for an item.\n        \n        Args:\n            item: The item to process\n            \n        Returns:\n            Processed item\n        """\n        # TODO: Implement your domain logic here\n        return item\n''')
        
        # Create __init__.py files
        with open(domain_dir / "__init__.py", "w") as f:
            f.write("")
        
        # Create application layer
        app_dir = base_dir / "application"
        os.makedirs(app_dir, exist_ok=True)
        
        # Create application service
        with open(app_dir / "service.py", "w") as f:
            f.write(f'''"""\nApplication services for {automation.name} automation.\n"""\nfrom typing import List, Optional, Dict, Any\nfrom ..domain.models import {automation.name.capitalize()}Item\nfrom ..domain.service import {automation.name.capitalize()}Service\nfrom ..infrastructure.repository import {automation.name.capitalize()}Repository\n\nclass {automation.name.capitalize()}ApplicationService:\n    """Application service for {automation.name}."""\n    \n    def __init__(self, repository: {automation.name.capitalize()}Repository = None, domain_service: {automation.name.capitalize()}Service = None):\n        """Initialize the application service."""\n        self.repository = repository or {automation.name.capitalize()}Repository()\n        self.domain_service = domain_service or {automation.name.capitalize()}Service()\n    \n    async def create_item(self, data: Dict[str, Any]) -> {automation.name.capitalize()}Item:\n        """\n        Create a new item.\n        \n        Args:\n            data: Item data\n            \n        Returns:\n            Created item\n        """\n        # Create domain entity\n        item = {automation.name.capitalize()}Item(**data)\n        \n        # Apply domain logic\n        item = await self.domain_service.process_item(item)\n        \n        # Save to repository\n        return await self.repository.create(item)\n    \n    async def get_by_id(self, item_id: str) -> Optional[{automation.name.capitalize()}Item]:\n        """\n        Get an item by ID.\n        \n        Args:\n            item_id: ID of the item\n            \n        Returns:\n            Item if found, None otherwise\n        """\n        return await self.repository.get_by_id(item_id)\n    \n    async def get_all(self) -> List[{automation.name.capitalize()}Item]:\n        """\n        Get all items.\n        \n        Returns:\n            List of items\n        """\n        return await self.repository.get_all()\n''')
        
        # Create __init__.py files
        with open(app_dir / "__init__.py", "w") as f:
            f.write("")
        
        # Create infrastructure layer
        infra_dir = base_dir / "infrastructure"
        os.makedirs(infra_dir, exist_ok=True)
        
        # Create repository
        with open(infra_dir / "repository.py", "w") as f:
            f.write(f'''"""\nRepository implementation for {automation.name} automation.\n"""\nfrom typing import List, Optional, Dict, Any\nfrom ..domain.models import {automation.name.capitalize()}Item\n\nclass {automation.name.capitalize()}Repository:\n    """Repository for {automation.name} data access."""\n    \n    async def create(self, item: {automation.name.capitalize()}Item) -> {automation.name.capitalize()}Item:\n        """\n        Create a new item.\n        \n        Args:\n            item: Item to create\n            \n        Returns:\n            Created item\n        """\n        # TODO: Implement database access\n        return item\n    \n    async def get_by_id(self, item_id: str) -> Optional[{automation.name.capitalize()}Item]:\n        """\n        Get an item by ID.\n        \n        Args:\n            item_id: ID of the item\n            \n        Returns:\n            Item if found, None otherwise\n        """\n        # TODO: Implement database access\n        return None\n    \n    async def get_all(self) -> List[{automation.name.capitalize()}Item]:\n        """\n        Get all items.\n        \n        Returns:\n            List of items\n        """\n        # TODO: Implement database access\n        return []\n''')
        
        # Create __init__.py files
        with open(infra_dir / "__init__.py", "w") as f:
            f.write("")
        
        # Create interface layer with handlers
        interface_dir = base_dir / "interface"
        os.makedirs(interface_dir, exist_ok=True)
        
        # Create handlers
        with open(interface_dir / "handlers.py", "w") as f:
            f.write(f'''"""\nRequest handlers for {automation.name} automation endpoints.\n"""\nfrom typing import Dict, Any, List\nfrom fastapi import BackgroundTasks\n\nfrom ..application.service import {automation.name.capitalize()}ApplicationService\nfrom ..domain.models import {automation.name.capitalize()}Item\n\n# Create application service instance\napp_service = {automation.name.capitalize()}ApplicationService()\n\nasync def get_all_items(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:\n    """\n    Handler for GET /{automation.name} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Response data\n    """\n    items = await app_service.get_all()\n    return {{"items": items, "total": len(items)}}\n\nasync def create_item(params: Dict[str, Any], *args, **kwargs) -> {automation.name.capitalize()}Item:\n    """\n    Handler for POST /{automation.name} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Created item\n    """\n    return await app_service.create_item(params)\n\nasync def get_item_by_id(params: Dict[str, Any], *args, **kwargs) -> {automation.name.capitalize()}Item:\n    """\n    Handler for GET /{automation.name}/{{item_id}} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Item data\n    """\n    item_id = params.get("item_id")\n    return await app_service.get_by_id(item_id)\n''')
        
        # Create __init__.py files
        with open(interface_dir / "__init__.py", "w") as f:
            f.write("")
        with open(base_dir / "__init__.py", "w") as f:
            f.write("")
        
        # Create README with usage instructions
        with open(base_dir / "README.md", "w") as f:
            f.write(f'''# {automation.name.capitalize()} Automation\n\n## Description\n{automation.description}\n\n## Structure\nThis automation follows Domain-Driven Design principles:\n\n- **Domain Layer**: Core business models and logic\n- **Application Layer**: Orchestration of domain objects and use cases\n- **Infrastructure Layer**: Technical implementations such as repositories\n- **Interface Layer**: Handlers for API endpoints\n\n## Usage\n\n1. Implement your domain models in `domain/models.py`\n2. Add business logic in `domain/service.py`\n3. Configure application services in `application/service.py`\n4. Implement data access in `infrastructure/repository.py`\n5. Update the request handlers in `interface/handlers.py`\n\n## Endpoints\n\n''')
            if automation.endpoints:
                for endpoint in automation.endpoints:
                    f.write(f"- {endpoint.method} {automation.base_path}{endpoint.path}: {endpoint.summary}\n")
            else:
                f.write("No endpoints defined yet. Add endpoints to your automation configuration.\n")
                
            f.write(f'''\n## Configuration\n\nTo use the custom handlers for your endpoints, update your automation configuration:\n\n```python\n# Example for updating an endpoint with custom handler\nendpoint.handler_path = "src.domain.automations.{automation.name}.interface.handlers.create_item"\n```\n''')
        
        logger.info(f"Generated DDD structure for automation: {automation.name}")

    async def deactivate_automation(self, name: str) -> Automation:
        """
        Deactivate an automation.
        
        Args:
            name: Name of the automation to deactivate
            
        Returns:
            The deactivated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
        """
        # Get the automation from the registry
        automation = await self.automation_registry.get_automation(name)
        if not automation:
            raise AutomationNotFoundError(f"Automation '{name}' not found")
        
        # Update the status to inactive
        automation.status = AutomationStatus.INACTIVE
        
        # Save the updated automation
        await self.automation_registry.update_automation(name, automation)
        
        # Remove the router for this automation
        await self.router_manager.remove_router(name)
        
        logger.info(f"Deactivated automation: {name}")
        return automation
    
    async def delete_automation(self, name: str) -> bool:
        """
        Delete an automation.
        
        Args:
            name: Name of the automation to delete
            
        Returns:
            True if the automation was deleted, False otherwise
        """
        # Remove the router first
        await self.router_manager.remove_router(name)
        
        # Delete the automation from the registry
        deleted = await self.automation_registry.delete_automation(name)
        
        if deleted:
            logger.info(f"Deleted automation: {name}")
        
        return deleted
    
    async def add_endpoint(self, automation_name: str, endpoint: Endpoint) -> Automation:
        """
        Add an endpoint to an automation.
        
        Args:
            automation_name: Name of the automation to add the endpoint to
            endpoint: The endpoint to add
            
        Returns:
            The updated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
        """
        # Get the automation from the registry
        automation = await self.automation_registry.get_automation(automation_name)
        if not automation:
            raise AutomationNotFoundError(f"Automation '{automation_name}' not found")
        
        # Add the endpoint
        automation.add_endpoint(endpoint)
        
        # Save the updated automation
        await self.automation_registry.update_automation(automation_name, automation)
        
        # Update the router if the automation is active
        if automation.status == AutomationStatus.ACTIVE:
            await self.router_manager.update_router(automation_name)
        
        logger.info(f"Added endpoint {endpoint.method} {endpoint.path} to automation: {automation_name}")
        return automation
    
    async def update_endpoint(
        self, 
        automation_name: str, 
        path: str, 
        method: str, 
        updated_endpoint: Endpoint
    ) -> Automation:
        """
        Update an endpoint in an automation.
        
        Args:
            automation_name: Name of the automation containing the endpoint
            path: Path of the endpoint to update
            method: HTTP method of the endpoint to update
            updated_endpoint: The updated endpoint configuration
            
        Returns:
            The updated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
            EndpointNotFoundError: If the endpoint is not found
        """
        # Get the automation from the registry
        automation = await self.automation_registry.get_automation(automation_name)
        if not automation:
            raise AutomationNotFoundError(f"Automation '{automation_name}' not found")
        
        # Update the endpoint
        updated = automation.update_endpoint(path, method, updated_endpoint)
        if not updated:
            raise EndpointNotFoundError(
                f"Endpoint {method} {path} not found in automation '{automation_name}'"
            )
        
        # Save the updated automation
        await self.automation_registry.update_automation(automation_name, automation)
        
        # Update the router if the automation is active
        if automation.status == AutomationStatus.ACTIVE:
            await self.router_manager.update_router(automation_name)
        
        logger.info(f"Updated endpoint {method} {path} in automation: {automation_name}")
        return automation
    
    async def remove_endpoint(
        self, 
        automation_name: str, 
        path: str, 
        method: str
    ) -> Automation:
        """
        Remove an endpoint from an automation.
        
        Args:
            automation_name: Name of the automation containing the endpoint
            path: Path of the endpoint to remove
            method: HTTP method of the endpoint to remove
            
        Returns:
            The updated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
            EndpointNotFoundError: If the endpoint is not found
        """
        # Get the automation from the registry
        automation = await self.automation_registry.get_automation(automation_name)
        if not automation:
            raise AutomationNotFoundError(f"Automation '{automation_name}' not found")
        
        # Remove the endpoint
        removed = automation.remove_endpoint(path, method)
        if not removed:
            raise EndpointNotFoundError(
                f"Endpoint {method} {path} not found in automation '{automation_name}'"
            )
        
        # Save the updated automation
        await self.automation_registry.update_automation(automation_name, automation)
        
        # Update the router if the automation is active
        if automation.status == AutomationStatus.ACTIVE:
            await self.router_manager.update_router(automation_name)
        
        logger.info(f"Removed endpoint {method} {path} from automation: {automation_name}")
        return automation
