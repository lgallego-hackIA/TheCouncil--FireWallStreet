"""
Automation Registry for managing automations.
"""
import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from src.domain.automation.models import Automation, AutomationStatus
from src.shared.exceptions import AutomationNotFoundError
try:
    from src.infrastructure.storage.blob_storage import BlobStorageAdapter
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Vercel Blob Storage not available. Falling back to file storage.")
    BLOB_STORAGE_AVAILABLE = False

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
        
        # Define the project root based on the current file's location
        # This makes pathing reliable across different environments (local, Vercel)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        default_storage_path = project_root / "data" / "automations"
        
        self._storage_dir = os.getenv("AUTOMATION_STORAGE_DIR", str(default_storage_path))
        logger.info(f"Automation storage directory set to: {self._storage_dir}")
    
    async def load_automations(self) -> None:
        """
        Load all automations from storage.
        Uses Vercel Blob Storage when available, falls back to file storage.
        """
        # Temporarily disable Vercel Blob Storage to debug file path issues
        use_blob_storage = False
        logger.info("Vercel Blob Storage is temporarily disabled for debugging.")
        
        if use_blob_storage:
            # Load from Vercel Blob Storage
            logger.info("Loading automations from Vercel Blob Storage")
            try:
                # List all automation keys in blob storage
                keys = await BlobStorageAdapter.list_json_keys()
                
                for key in keys:
                    try:
                        # Load automation data from blob storage
                        automation_data = await BlobStorageAdapter.load_json(key)
                        automation = Automation.parse_obj(automation_data)
                        self._automations[automation.name] = automation
                        logger.info(f"Loaded automation {automation.name} (ID: {key}) from blob storage")
                    except FileNotFoundError:
                        logger.warning(f"Automation file for key {key} not found in blob storage. Skipping.")
                    except Exception as e:
                        logger.error(f"Error parsing or loading automation {key} from blob storage: {e}")
            except Exception as e:
                logger.error(f"Error listing automation keys from blob storage: {e}")
        else:
            # Fall back to file storage for local development
            logger.info("Loading automations from local file storage at: " + self._storage_dir)
            # Create the storage directory if it doesn't exist
            os.makedirs(self._storage_dir, exist_ok=True)
            
            try:
                if not os.path.isdir(self._storage_dir):
                    logger.warning(f"Automation storage path is not a directory: {self._storage_dir}")
                    return
                
                files_in_dir = os.listdir(self._storage_dir)
                logger.info(f"Files found in automation directory: {files_in_dir}")

                for filename in files_in_dir:
                    if filename.endswith(".json"):
                        file_path = os.path.join(self._storage_dir, filename)
                        try:
                            with open(file_path, "r") as f:
                                automation_data = json.load(f)
                                automation = Automation.parse_obj(automation_data)
                                self._automations[automation.name] = automation
                                logger.info(f"Loaded automation from file: {automation.name} (File: {filename})")
                        except Exception as e:
                            logger.error(f"Error loading or parsing automation from file {filename}: {e}")
            except Exception as e:
                logger.error(f"Error listing files in automation directory {self._storage_dir}: {e}")
    
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
        Uses Vercel Blob Storage when available, falls back to file storage.
        
        Args:
            name: Name of the automation to delete
            
        Returns:
            True if the automation was deleted, False if it wasn't found
        """
        if name not in self._automations:
            return False
        
        # Get the automation before removing it from the registry
        automation = self._automations.pop(name)
        
        # Check if Vercel Blob Storage is available and configured
        use_blob_storage = BLOB_STORAGE_AVAILABLE and BlobStorageAdapter.is_available()
        
        if use_blob_storage:
            # Delete from Vercel Blob Storage
            try:
                await BlobStorageAdapter.delete_json(automation.id)
                logger.info(f"Deleted automation {name} from blob storage")
            except Exception as e:
                logger.error(f"Error deleting automation from blob storage: {e}")
        
        # Also try to delete from file storage for completeness
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
        Uses Vercel Blob Storage when available, falls back to file storage.
        
        Args:
            automation: The automation to save
        """
        # Check if Vercel Blob Storage is available and configured
        use_blob_storage = BLOB_STORAGE_AVAILABLE and BlobStorageAdapter.is_available()
        
        # Convert automation to dict for storage
        automation_data = automation.dict()
        
        if use_blob_storage:
            # Save to Vercel Blob Storage
            try:
                url = await BlobStorageAdapter.save_json(automation.id, automation_data)
                logger.info(f"Saved automation {automation.name} to blob storage: {url}")
            except Exception as e:
                logger.error(f"Error saving automation to blob storage: {e}")
                # Fall back to file storage if blob storage fails
                await self._save_automation_to_file(automation.id, automation_data)
        else:
            # Fall back to file storage for local development
            await self._save_automation_to_file(automation.id, automation_data)
    
    async def _save_automation_to_file(self, automation_id: str, automation_data: Dict[str, Any]) -> None:
        """
        Save an automation to file storage.
        
        Args:
            automation_id: ID of the automation to save
            automation_data: The automation data to save
        """
        os.makedirs(self._storage_dir, exist_ok=True)
        
        file_path = os.path.join(self._storage_dir, f"{automation_id}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(automation_data, f, default=str, indent=2)
            logger.info(f"Saved automation {automation_id} to file storage")
        except Exception as e:
            logger.error(f"Error saving automation to file: {e}")
    
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
