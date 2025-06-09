"""
Automation Registry for managing automations.
"""
import logging
import os
import json
from typing import Dict, List, Optional
from uuid import uuid4

from src.domain.automation.models import Automation, AutomationStatus
from src.shared.exceptions import AutomationNotFoundError

logger = logging.getLogger(__name__)


class AutomationRegistry:
    """
    Registry for managing automation configurations.
    
    This class is responsible for loading, storing, and retrieving automations.
    In a production system, this might use a database instead of in-memory storage.
    """

    def __init__(self):
        """Initialize the automation registry."""
        self._automations: Dict[str, Automation] = {}
        self._storage_dir = os.getenv("AUTOMATION_STORAGE_DIR", "data/automations")
    
    async def load_automations(self) -> None:
        """
        Load all automations from storage.
        In a real implementation, this would load from a database.
        """
        # Create the storage directory if it doesn't exist
        os.makedirs(self._storage_dir, exist_ok=True)
        
        # For now, we'll use a simple file-based storage system
        try:
            for filename in os.listdir(self._storage_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self._storage_dir, filename)
                    
                    with open(file_path, "r") as f:
                        automation_data = json.load(f)
                        automation = Automation.parse_obj(automation_data)
                        self._automations[automation.name] = automation
                        logger.info(f"Loaded automation: {automation.name}")
        except Exception as e:
            logger.error(f"Error loading automations: {e}")
    
    async def get_all_automations(self) -> List[Automation]:
        """
        Get all registered automations.
        
        Returns:
            List of all registered automations
        """
        return list(self._automations.values())
    
    async def get_automation(self, name: str) -> Optional[Automation]:
        """
        Get an automation by name.
        
        Args:
            name: Name of the automation to get
            
        Returns:
            The automation if found, None otherwise
        """
        return self._automations.get(name)
        
    async def get_automation_by_id(self, automation_id: str) -> Optional[Automation]:
        """
        Get an automation by its ID.
        
        Args:
            automation_id: ID of the automation to get
            
        Returns:
            The automation if found, None otherwise
        """
        for automation in self._automations.values():
            if automation.id == automation_id:
                return automation
        return None
    
    async def register_automation(self, automation: Automation) -> Automation:
        """
        Register a new automation.
        
        Args:
            automation: The automation to register
            
        Returns:
            The registered automation
            
        Raises:
            ValueError: If an automation with the same name already exists
        """
        if automation.name in self._automations:
            raise ValueError(f"Automation with name '{automation.name}' already exists")
        
        # Generate a unique ID if not provided
        if not automation.id:
            automation.id = str(uuid4())
        
        self._automations[automation.name] = automation
        
        # Save the automation to storage
        await self._save_automation(automation)
        
        logger.info(f"Registered automation: {automation.name}")
        return automation
    
    async def update_automation(self, name: str, updated_automation: Automation) -> Automation:
        """
        Update an existing automation.
        
        Args:
            name: Name of the automation to update
            updated_automation: The updated automation
            
        Returns:
            The updated automation
            
        Raises:
            AutomationNotFoundError: If the automation is not found
        """
        if name not in self._automations:
            raise AutomationNotFoundError(f"Automation '{name}' not found")
        
        # Preserve the original ID
        updated_automation.id = self._automations[name].id
        
        # Update the automation in the registry
        self._automations[name] = updated_automation
        
        # Save the updated automation to storage
        await self._save_automation(updated_automation)
        
        logger.info(f"Updated automation: {name}")
        return updated_automation
    
    async def delete_automation(self, name: str) -> bool:
        """
        Delete an automation.
        
        Args:
            name: Name of the automation to delete
            
        Returns:
            True if the automation was deleted, False if it wasn't found
        """
        if name not in self._automations:
            return False
        
        # Remove the automation from the registry
        automation = self._automations.pop(name)
        
        # Remove the automation from storage
        file_path = os.path.join(self._storage_dir, f"{automation.id}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting automation file: {e}")
        
        logger.info(f"Deleted automation: {name}")
        return True
        
    async def delete_automation_by_id(self, automation_id: str) -> bool:
        """
        Delete an automation by its ID.
        
        Args:
            automation_id: ID of the automation to delete
            
        Returns:
            True if the automation was deleted, False if it wasn't found
        """
        # Find the automation with the given ID
        for name, automation in self._automations.items():
            if automation.id == automation_id:
                # Use the existing delete_automation method
                return self.delete_automation(name)
        
        logger.warning(f"Automation with ID {automation_id} not found for deletion")
        return False
    
    async def _save_automation(self, automation: Automation) -> None:
        """
        Save an automation to storage.
        
        Args:
            automation: The automation to save
        """
        os.makedirs(self._storage_dir, exist_ok=True)
        
        file_path = os.path.join(self._storage_dir, f"{automation.id}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(automation.dict(), f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error saving automation: {e}")
    
    async def create_automation(self, name: str, description: str, base_path: str = None) -> Automation:
        """
        Create a new automation with basic details.
        
        Args:
            name: Name of the automation
            description: Description of the automation
            base_path: Base path for API endpoints (e.g., /api/v1/resource)
            
        Returns:
            The created automation
            
        Raises:
            ValueError: If an automation with the same name already exists
        """
        if name in self._automations:
            raise ValueError(f"Automation with name '{name}' already exists")
        
        # Create a new automation
        automation = Automation(
            id=str(uuid4()),
            name=name,
            description=description,
            version="1.0.0",
            status=AutomationStatus.DRAFT,
            base_path=base_path or f"/api/{name}",  # Use provided base_path or create default
        )
        
        # Register the automation
        await self.register_automation(automation)
        
        return automation
