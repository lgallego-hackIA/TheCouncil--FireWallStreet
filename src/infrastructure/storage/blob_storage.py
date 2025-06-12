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

        Checks for FORCE_LOCAL_AUTOMATIONS env var first. If true, returns False.
        Otherwise, availability depends on BLOB_READ_WRITE_TOKEN.
        
        Returns:
            bool: True if the adapter is available, False otherwise
        """
        
        # Original check: The Vercel Blob Storage adapter is considered available only if we have a token.
        # This ensures AutomationRegistry falls back to its direct file loading if token is not set or is empty.
        token_present = bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))
        if not token_present:
            logger.info("BLOB_READ_WRITE_TOKEN not found. BlobStorageAdapter reports as unavailable.")
        else:
            logger.info("BLOB_READ_WRITE_TOKEN found. BlobStorageAdapter reports as available (unless FORCE_LOCAL_AUTOMATIONS overrides).")
        return token_present
        
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
            
        Raises:
            RuntimeError: If in mock mode on Vercel, indicating misconfiguration.
            Exception: If any other error occurs during saving.
        """
        # Pre-check for mock mode on Vercel
        if IS_MOCK and VERCEL_ENV: # VERCEL_ENV is set means we are on Vercel
            err_msg = (
                f"BlobStorageAdapter is in mock mode (IS_MOCK=True) while on Vercel (VERCEL_ENV='{VERCEL_ENV}'). "
                f"Cannot save key '{key}' to read-only filesystem. "
                f"Ensure VERCEL_ENV is 'production' and BLOB_READ_WRITE_TOKEN is correctly set at module import time."
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        if not BlobStorageAdapter.is_available():
            logger.warning(
                f"BlobStorageAdapter.is_available() returned False for key '{key}'. "
                f"If on Vercel, this is unexpected. Token set: {bool(BLOB_READ_WRITE_TOKEN)}. "
                f"Proceeding with configured 'put' operation (might be local_blob.put)."
            )

        try:
            # Convert data to JSON string
            json_data = json.dumps(data, default=str, indent=2)
            
            # Create a buffer from the JSON string
            buffer = json_data.encode('utf-8')
            
            # Use the key as the filename with .json extension
            filename = f"{BLOB_PREFIX}/{key}.json"
            
            # Upload to Vercel Blob (this 'put' is vercel_blob.put or local_blob.put based on import)
            result: PutBlobResult = await put(filename, buffer, {"access": "public"})
            
            logger.info(f"Saved blob with key '{key}' to {result.url}")
            return result.url
        except Exception as e:
            logger.error(f"Error saving blob with key '{key}' to Blob Storage: {e}", exc_info=True)
            raise  # Re-raise the exception to be handled by the caller

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
