"""
Vercel Blob Storage adapter for theCouncil.
This module provides functionality for storing and retrieving data from Vercel Blob Storage.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
import base64
from datetime import timedelta

# Set up logger
logger = logging.getLogger(__name__)

# Check if in Vercel environment
IN_VERCEL = os.environ.get('VERCEL') == '1'

# Check if Blob Storage token is available
HAS_BLOB_TOKEN = os.environ.get('BLOB_READ_WRITE_TOKEN') is not None

# Define if Blob Storage is available (either real or mock)
BLOB_STORAGE_AVAILABLE = IN_VERCEL and HAS_BLOB_TOKEN or not IN_VERCEL

# Import appropriate Blob implementation based on environment
if IN_VERCEL and HAS_BLOB_TOKEN:
    # Use actual Vercel Blob when in Vercel environment and token is available
    try:
        from vercel_blob import put, get, list_blobs, del_blob, PutBlobResult
        from vercel_blob.types import BlobNotFoundError, ListingResponse
        IS_MOCK = False
    except ImportError:
        logger.warning("Failed to import vercel_blob, falling back to local implementation")
        from src.infrastructure.storage.local_blob import put, get, list_blobs, del_blob, PutBlobResult
        from src.infrastructure.storage.local_blob import BlobNotFoundError, ListingResponse
        IS_MOCK = True
else:
    # Use local mock implementation when in development
    from src.infrastructure.storage.local_blob import put, get, list_blobs, del_blob, PutBlobResult
    from src.infrastructure.storage.local_blob import BlobNotFoundError, ListingResponse
    IS_MOCK = True

logger = logging.getLogger(__name__)

# Environment variables for Vercel Blob
BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
BLOB_PREFIX = "automations"

class BlobStorageAdapter:
    """Adapter for Vercel Blob Storage API for JSON data."""

    @staticmethod
    def is_available() -> bool:
        """Check if the blob storage adapter is available.
        
        Returns:
            bool: True if the adapter is available, False otherwise
        """
        # The Vercel Blob Storage adapter is considered available only if we have a token.
        # This ensures AutomationRegistry falls back to its direct file loading if token is not set or is empty.
        return bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))
        
    @staticmethod
    async def list_blobs(prefix: str = "") -> List[str]:
        """List all blobs with the given prefix.
        
        Args:
            prefix: Prefix to filter blobs by
            
        Returns:
            List[str]: List of blob paths
        """
        try:
            # Default prefix is automations/
            if not prefix.startswith("automations/") and not prefix.startswith("openapi/"):
                full_prefix = f"automations/{prefix}"
            else:
                full_prefix = prefix
                
            # List blobs with the prefix
            result = await list_blobs({"prefix": full_prefix})
            
            # Extract paths
            paths = [blob.pathname for blob in result.blobs]
            
            logger.info(f"Listed {len(paths)} blobs with prefix '{full_prefix}'")
            return paths
        except Exception as e:
            logger.error(f"Error listing blobs with prefix '{prefix}': {e}")
            return []

    @staticmethod
    async def save_json(key: str, data: Dict[str, Any]) -> str:
        """
        Save JSON data to Vercel Blob Storage.
        
        Args:
            key: The key for the blob (used in the filename)
            data: The data to save
            
        Returns:
            str: The URL of the saved blob
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data, default=str, indent=2)
            
            # Create a buffer from the JSON string
            buffer = json_data.encode('utf-8')
            
            # Use the key as the filename with .json extension
            filename = f"{BLOB_PREFIX}/{key}.json"
            
            # Upload to Vercel Blob
            result: PutBlobResult = await put(filename, buffer, {"access": "public"})
            
            logger.info(f"Saved blob with key '{key}' to {result.url}")
            return result.url
        except Exception as e:
            logger.error(f"Error saving to Blob Storage: {e}")
            raise

    @staticmethod
    async def load_json(key: str) -> Dict[str, Any]:
        """
        Load JSON data from Vercel Blob Storage.
        
        Args:
            key: The key for the blob (used in the filename)
            
        Returns:
            Dict[str, Any]: The loaded JSON data
            
        Raises:
            FileNotFoundError: If the blob is not found
        """
        try:
            # Use the key as the filename with .json extension
            filename = f"{BLOB_PREFIX}/{key}.json"
            
            # Download from Vercel Blob
            blob = await get(filename)
            
            if not blob:
                raise FileNotFoundError(f"Blob with key '{key}' not found")
            
            # Parse JSON from blob
            json_data = await blob.text()
            return json.loads(json_data)
        except BlobNotFoundError:
            logger.error(f"Blob with key '{key}' not found")
            raise FileNotFoundError(f"Blob with key '{key}' not found")
        except Exception as e:
            logger.error(f"Error loading from Blob Storage: {e}")
            raise

    @staticmethod
    async def delete_json(key: str) -> bool:
        """
        Delete JSON data from Vercel Blob Storage.
        
        Args:
            key: The key for the blob (used in the filename)
            
        Returns:
            bool: True if the blob was deleted, False otherwise
        """
        try:
            # Use the key as the filename with .json extension
            filename = f"{BLOB_PREFIX}/{key}.json"
            
            # Delete from Vercel Blob
            await del_blob(filename)
            
            logger.info(f"Deleted blob with key '{key}'")
            return True
        except BlobNotFoundError:
            logger.warning(f"Blob with key '{key}' not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Error deleting from Blob Storage: {e}")
            return False

    @staticmethod
    async def list_json_keys(local_automations_path: Optional[str] = None) -> List[str]:
        """
        List all JSON keys (typically automation IDs).
        If Vercel Blob Storage is available, lists from blob storage under 'automations/'.
        Otherwise, if local_automations_path is provided, lists from the local file system.
        Keys returned are the base names without .json extension (e.g., automation IDs).
        """
        keys: List[str] = []
        if BlobStorageAdapter.is_available():
            logger.info("Listing JSON keys from Vercel Blob Storage.")
            try:
                # BLOB_PREFIX is typically "automations"
                blob_list_response = await vercel_blob.list(prefix=BLOB_PREFIX + "/", options={'limit': 1000})
                for blob in blob_list_response.get('blobs', []):
                    if blob.pathname.startswith(BLOB_PREFIX + "/") and blob.pathname.endswith(".json"):
                        # Extract key: remove prefix "automations/" and suffix ".json"
                        key = blob.pathname.replace(f"{BLOB_PREFIX}/", "", 1).replace(".json", "")
                        if key: # Ensure key is not empty after stripping
                            keys.append(key)
                logger.info(f"Found {len(keys)} keys in Vercel Blob Storage.")
            except Exception as e:
                logger.error(f"Error listing JSON keys from Vercel Blob Storage: {e}")
        elif local_automations_path:
            logger.info(f"Vercel Blob Storage not available or token not set. Listing JSON keys from local path: {local_automations_path}")
            try:
                if os.path.isdir(local_automations_path):
                    for filename in os.listdir(local_automations_path):
                        if filename.endswith(".json"):
                            key = filename.replace(".json", "")
                            keys.append(key)
                    logger.info(f"Found {len(keys)} keys in local directory: {local_automations_path}.")
                else:
                    logger.warning(f"Local automation path is not a directory: {local_automations_path}")
            except Exception as e:
                logger.error(f"Error listing JSON keys from local path {local_automations_path}: {e}")
        else:
            logger.warning("Vercel Blob Storage not available and no local_automations_path provided to list_json_keys.")
            
        return keys
