"""
OpenAPI Schema Storage module for theCouncil.
Handles storing and retrieving OpenAPI schemas using Vercel Blob Storage.
"""
import json
import logging
import os
from typing import Dict, Any, Optional

from src.infrastructure.storage.blob_storage import BlobStorageAdapter, BLOB_STORAGE_AVAILABLE

logger = logging.getLogger(__name__)

# Constants for OpenAPI storage
OPENAPI_BLOB_PREFIX = "openapi"
OPENAPI_LOCAL_DIR = "data/openapi"

class OpenAPIStorage:
    """
    Storage adapter for OpenAPI schemas.
    Uses Vercel Blob Storage when available, falls back to file storage.
    """

    @staticmethod
    def is_blob_available() -> bool:
        """
        Check if Blob Storage is available.
        
        Returns:
            bool: True if Blob Storage is available
        """
        return BLOB_STORAGE_AVAILABLE and BlobStorageAdapter.is_available()
    
    @staticmethod
    async def save_schema(automation_id: str, schema_data: Dict[str, Any]) -> str:
        """
        Save OpenAPI schema for an automation.
        
        Args:
            automation_id: ID of the automation
            schema_data: OpenAPI schema data
            
        Returns:
            str: URL or path where the schema was saved
        """
        if OpenAPIStorage.is_blob_available():
            # Use Vercel Blob Storage
            try:
                blob_key = f"{OPENAPI_BLOB_PREFIX}/{automation_id}"
                url = await BlobStorageAdapter.save_json(blob_key, schema_data)
                logger.info(f"Saved OpenAPI schema for {automation_id} to blob: {url}")
                return url
            except Exception as e:
                logger.error(f"Error saving OpenAPI schema to blob storage: {e}")
                # Fall back to file storage
                return await OpenAPIStorage._save_schema_to_file(automation_id, schema_data)
        else:
            # Use local file storage
            return await OpenAPIStorage._save_schema_to_file(automation_id, schema_data)
    
    @staticmethod
    async def _save_schema_to_file(automation_id: str, schema_data: Dict[str, Any]) -> str:
        """
        Save OpenAPI schema to local file storage.
        
        Args:
            automation_id: ID of the automation
            schema_data: OpenAPI schema data
            
        Returns:
            str: Path to the saved schema file
        """
        os.makedirs(OPENAPI_LOCAL_DIR, exist_ok=True)
        filepath = os.path.join(OPENAPI_LOCAL_DIR, f"{automation_id}.json")
        
        try:
            with open(filepath, "w") as f:
                json.dump(schema_data, f, default=str, indent=2)
            
            logger.info(f"Saved OpenAPI schema for {automation_id} to file: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving OpenAPI schema to file: {e}")
            raise
    
    @staticmethod
    async def load_schema(automation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load OpenAPI schema for an automation.
        
        Args:
            automation_id: ID of the automation
            
        Returns:
            Optional[Dict[str, Any]]: OpenAPI schema data if found, None otherwise
        """
        if OpenAPIStorage.is_blob_available():
            # Try Vercel Blob Storage first
            try:
                blob_key = f"{OPENAPI_BLOB_PREFIX}/{automation_id}"
                schema_data = await BlobStorageAdapter.load_json(blob_key)
                logger.info(f"Loaded OpenAPI schema for {automation_id} from blob")
                return schema_data
            except FileNotFoundError:
                logger.warning(f"OpenAPI schema for {automation_id} not found in blob storage")
                # Fall back to file storage
                return await OpenAPIStorage._load_schema_from_file(automation_id)
            except Exception as e:
                logger.error(f"Error loading OpenAPI schema from blob storage: {e}")
                # Fall back to file storage
                return await OpenAPIStorage._load_schema_from_file(automation_id)
        else:
            # Use local file storage
            return await OpenAPIStorage._load_schema_from_file(automation_id)
    
    @staticmethod
    async def _load_schema_from_file(automation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load OpenAPI schema from local file storage.
        
        Args:
            automation_id: ID of the automation
            
        Returns:
            Optional[Dict[str, Any]]: OpenAPI schema data if found, None otherwise
        """
        filepath = os.path.join(OPENAPI_LOCAL_DIR, f"{automation_id}.json")
        
        if not os.path.exists(filepath):
            logger.warning(f"OpenAPI schema file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r") as f:
                schema_data = json.load(f)
            
            logger.info(f"Loaded OpenAPI schema for {automation_id} from file: {filepath}")
            return schema_data
        except Exception as e:
            logger.error(f"Error loading OpenAPI schema from file: {e}")
            return None
    
    @staticmethod
    async def delete_schema(automation_id: str) -> bool:
        """
        Delete OpenAPI schema for an automation.
        
        Args:
            automation_id: ID of the automation
            
        Returns:
            bool: True if deleted successfully
        """
        success = False
        
        if OpenAPIStorage.is_blob_available():
            # Try to delete from Vercel Blob Storage
            try:
                blob_key = f"{OPENAPI_BLOB_PREFIX}/{automation_id}"
                blob_success = await BlobStorageAdapter.delete_json(blob_key)
                if blob_success:
                    logger.info(f"Deleted OpenAPI schema for {automation_id} from blob storage")
                    success = True
            except Exception as e:
                logger.error(f"Error deleting OpenAPI schema from blob storage: {e}")
        
        # Also try to delete from file storage
        filepath = os.path.join(OPENAPI_LOCAL_DIR, f"{automation_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"Deleted OpenAPI schema for {automation_id} from file: {filepath}")
                success = True
            except Exception as e:
                logger.error(f"Error deleting OpenAPI schema file: {e}")
        
        return success
