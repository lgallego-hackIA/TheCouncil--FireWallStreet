"""
AutomationManager for handling the lifecycle of automations and their endpoints.
"""
import logging
from typing import Any, Dict, List, Optional
from string import Template

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
        import shutil
        
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
        
        # Create a base __init__.py in the automation directory
        with open(base_dir / "__init__.py", "w") as f:
            f.write("")
            
        # Ensure tests directory exists
        tests_root = Path("tests")
        os.makedirs(tests_root, exist_ok=True)
        if not (tests_root / "__init__.py").exists():
            with open(tests_root / "__init__.py", "w") as f:
                f.write("")
                
        # Ensure tests/automations directory exists
        tests_automations = tests_root / "automations"
        os.makedirs(tests_automations, exist_ok=True)
        if not (tests_automations / "__init__.py").exists():
            with open(tests_automations / "__init__.py", "w") as f:
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
            # Construct the handlers file content
            handlers_content = '"""\nRequest handlers for {0} automation endpoints.\n"""\nfrom typing import Dict, Any, List\nfrom fastapi import BackgroundTasks\nimport time\nimport platform\nimport psutil\nfrom datetime import datetime\n\nfrom ..application.service import {1}ApplicationService\nfrom ..domain.models import {1}Item\nfrom ..infrastructure.repository import {1}Repository\n\n# Create application service instance\napp_service = {1}ApplicationService()\n\nasync def get_all_items(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:\n    """\n    Handler for GET /{0} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Response data\n    """\n    items = await app_service.get_all()\n    return {"items": items, "total": len(items)}\n\nasync def create_item(params: Dict[str, Any], *args, **kwargs) -> {1}Item:\n    """\n    Handler for POST /{0} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Created item\n    """\n    return await app_service.create_item(params)\n\nasync def get_item_by_id(params: Dict[str, Any], *args, **kwargs) -> {1}Item:\n    """\n    Handler for GET /{0}/{{item_id}} endpoint.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Item data\n    """\n    item_id = params.get("item_id")\n    return await app_service.get_by_id(item_id)\n\nasync def health_check(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:\n    """\n    Handler for GET /{0}/health endpoint.\n    Provides comprehensive health check for the {0} automation.\n    \n    Args:\n        params: Request parameters\n        \n    Returns:\n        Health check data\n    """\n    start_time = time.time()\n    \n    # Check repository connection\n    repo = {1}Repository()\n    repository_status = "ok"\n    repository_message = "Repository connection successful"\n    repository_latency = 0\n    \n    try:\n        repo_start = time.time()\n        await repo.get_all()  # Simple repository operation to verify connectivity\n        repository_latency = round((time.time() - repo_start) * 1000, 2)  # in ms\n    except Exception as e:\n        repository_status = "error"\n        repository_message = "Repository error: {}".format(str(e))\n    \n    # System info\n    system_info = {{\n        "platform": platform.platform(),\n        "processor": platform.processor(),\n        "python_version": platform.python_version(),\n        "memory_usage": {{\n            "percent": psutil.virtual_memory().percent,\n            "available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2)\n        }},\n        "cpu_usage": psutil.cpu_percent()\n    }}\n    \n    # Service dependencies\n    dependencies = {{\n        "repository": {{\n            "status": repository_status,\n            "message": repository_message,\n            "latency_ms": repository_latency\n        }}\n    }}\n    \n    # Overall health status\n    overall_status = "healthy" if repository_status == "ok" else "degraded"\n    \n    response_time = round((time.time() - start_time) * 1000, 2)  # in ms\n    \n    return {{\n        "status": overall_status,\n        "timestamp": datetime.now().isoformat(),\n        "service": f"{0}-automation",\n        "version": "1.0.0",\n        "response_time_ms": response_time,\n        "dependencies": dependencies,\n        "system_info": system_info\n    }}\n'.format(automation.name, automation.name.capitalize())
            
            f.write(handlers_content)
        
        # Create __init__.py files
        with open(interface_dir / "__init__.py", "w") as f:
            f.write("")
            
        # Create tests directory and test files
        tests_dir = Path(f"tests/automations/{automation.name}")
        os.makedirs(tests_dir, exist_ok=True)
        
        # Create __init__.py for tests directory
        with open(tests_dir / "__init__.py", "w") as f:
            f.write("")
        
        # Create test_models.py
        with open(tests_dir / "test_models.py", "w") as f:
            test_models_template = Template('''
"""
Tests for $name domain models.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from src.domain.automations.$name_lower.domain.models import $name_capitalized


def test_${name_lower}_item_creation():
    """Test that a $name_capitalizedItem can be created with valid data."""
    item = $name_capitalizedItem(
        name="Test $name",
        description="Test description"
    )
    
    assert item.name == "Test $name"
    assert item.description == "Test description"
    assert item.id is None
    assert isinstance(item.created_at, datetime)
    assert isinstance(item.updated_at, datetime)


def test_$name_lower_item_invalid_creation():
    """Test that $name_capitalizedItem validation works correctly."""
    with pytest.raises(ValidationError):
        # Name is required
        $name_capitalizedItem(
            description="Test without name"
        )
''')
            f.write(test_models_template.substitute(
                name=automation.name,
                name_lower=automation.name.lower(),
                name_capitalized=automation.name.capitalize()
            ))
        
        # Create test_service.py
        with open(tests_dir / "test_service.py", "w") as f:
            test_service_template = Template('''
"""
Tests for $name application service.
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.domain.automations.$name_lower.domain.models import $name_capitalizedItem
from src.domain.automations.$name_lower.application.service import $name_capitalizedApplicationService


@pytest.fixture
def mock_$name_lower_repository():
    """Create a mock repository."""
    repository = AsyncMock()
    repository.create.return_value = $name_capitalizedItem(
        id="test-id",
        name="Test $name",
        description="Test description"
    )
    repository.get_by_id.return_value = $name_capitalizedItem(
        id="test-id",
        name="Test $name",
        description="Test description"
    )
    repository.get_all.return_value = [
        $name_capitalizedItem(
            id="test-id-1",
            name="Test $name 1",
            description="Test description 1"
        ),
        $name_capitalizedItem(
            id="test-id-2",
            name="Test $name 2",
            description="Test description 2"
        )
    ]
    return repository


@pytest.mark.asyncio
async def test_create_item(mock_$name_lower_repository):
    """Test creating an item."""
    service = $name_capitalizedApplicationService(repository=mock_$name_lower_repository)
    
    data = {
        "name": "Test $name",
        "description": "Test description"
    }
    
    result = await service.create_item(data)
    
    assert result.id == "test-id"
    assert result.name == "Test $name"
    mock_$name_lower_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id(mock_$name_lower_repository):
    """Test getting an item by ID."""
    service = $name_capitalizedApplicationService(repository=mock_$name_lower_repository)
    
    result = await service.get_by_id("test-id")
    
    assert result.id == "test-id"
    assert result.name == "Test $name"
    mock_$name_lower_repository.get_by_id.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_get_all(mock_$name_lower_repository):
    """Test getting all items."""
    service = $name_capitalizedApplicationService(repository=mock_$name_lower_repository)
    
    result = await service.get_all()
    
    assert len(result) == 2
    assert result[0].id == "test-id-1"
    assert result[1].id == "test-id-2"
    mock_$name_lower_repository.get_all.assert_called_once()
''')
            f.write(test_service_template.substitute(
                name=automation.name,
                name_lower=automation.name.lower(),
                name_capitalized=automation.name.capitalize()
            ))
        
        # Create test_handlers.py
        with open(tests_dir / "test_handlers.py", "w") as f:
            test_handlers_template = Template('''
"""
Tests for $name request handlers.
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.domain.automations.$name_lower.domain.models import $name_capitalizedItem
from src.domain.automations.$name_lower.interface.handlers import get_all_items, create_item, get_item_by_id, health_check


@pytest.mark.asyncio
async def test_get_all_items():
    """Test the get_all_items handler."""
    with patch("src.domain.automations.$name_lower.interface.handlers.app_service") as mock_service:
        mock_service.get_all.return_value = [
            $name_capitalizedItem(
                id="test-id-1",
                name="Test $name 1",
                description="Test description 1"
            ),
            $name_capitalizedItem(
                id="test-id-2",
                name="Test $name 2",
                description="Test description 2"
            )
        ]
        
        result = await get_all_items({})
        
        assert result["total"] == 2
        assert len(result["items"]) == 2
        mock_service.get_all.assert_called_once()


@pytest.mark.asyncio
async def test_create_item():
    """Test the create_item handler."""
    with patch("src.domain.automations.$name_lower.interface.handlers.app_service") as mock_service:
        mock_item = $name_capitalizedItem(
            id="test-id",
            name="Test $name",
            description="Test description"
        )
        mock_service.create_item.return_value = mock_item
        
        params = {
            "name": "Test $name",
            "description": "Test description"
        }
        
        result = await create_item(params)
        
        assert result.id == "test-id"
        assert result.name == "Test $name"
        mock_service.create_item.assert_called_once_with(params)


@pytest.mark.asyncio
async def test_get_item_by_id():
    """Test the get_item_by_id handler."""
    with patch("src.domain.automations.$name_lower.interface.handlers.app_service") as mock_service:
        mock_item = $name_capitalizedItem(
            id="test-id",
            name="Test $name",
            description="Test description"
        )
        mock_service.get_by_id.return_value = mock_item
        
        params = {
            "item_id": "test-id"
        }
        
        result = await get_item_by_id(params)
        
        assert result.id == "test-id"
        assert result.name == "Test $name"
        mock_service.get_by_id.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_health_check():
    """Test the health_check handler."""
    result = await health_check({})
    
    assert "status" in result
    assert "timestamp" in result
    assert "service" in result
    assert result["service"] == "$name-automation"
    assert "dependencies" in result
    assert "system_info" in result
''')
            f.write(test_handlers_template.substitute(
                name=automation.name,
                name_lower=automation.name.lower(),
                name_capitalized=automation.name.capitalize()
            ))
        
        # Create README.md with automation documentation
        with open(base_dir / "README.md", "w") as f:
            f.write(f'# {automation.name.capitalize()} Automation\n\n## Description\n{automation.description}\n\n## Structure\nThis automation follows Domain-Driven Design principles:\n\n- **Domain Layer**: Core business models and logic\n- **Application Layer**: Orchestration of domain objects and use cases\n- **Infrastructure Layer**: Technical implementations such as repositories\n- **Interface Layer**: Handlers for API endpoints\n\n## Usage\n\n1. Implement your domain models in `domain/models.py`\n2. Add business logic in `domain/service.py`\n3. Configure application services in `application/service.py`\n4. Implement data access in `infrastructure/repository.py`\n5. Update the request handlers in `interface/handlers.py`\n\n## Endpoints\n\n')
            if automation.endpoints:
                for endpoint in automation.endpoints:
                    f.write(f'- {endpoint.method} {automation.base_path}{endpoint.path}: {endpoint.summary}\n')
            else:
                f.write('No endpoints defined yet. Add endpoints to your automation configuration.\n')
                
            # Additional documentation sections
            readme_content = """
## Configuration

To use the custom handlers for your endpoints, update your automation configuration:

```python
# Example for updating an endpoint with custom handler
endpoint.handler_path = "src.domain.automations.{0}.interface.handlers.create_item"
```

## Health Check

A comprehensive health check endpoint is automatically created for this automation.
Use the following handler path to add it to your endpoints:

```python
"src.domain.automations.{0}.interface.handlers.health_check"
```

## Testing

Unit tests are automatically generated for this automation. Run them with:

```bash
pytest tests/automations/{0}/
```
"""
            f.write(readme_content.format(automation.name))
        
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
            # Also clean up the generated code files in src/domain/automations/{name}/
            import os
            import shutil
            from pathlib import Path
            
            code_dir = Path(f"src/domain/automations/{name}")
            if code_dir.exists() and code_dir.is_dir():
                try:
                    shutil.rmtree(code_dir)
                    logger.info(f"Removed generated code for automation: {name}")
                except Exception as e:
                    logger.error(f"Error removing generated code for automation {name}: {e}")
            
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
