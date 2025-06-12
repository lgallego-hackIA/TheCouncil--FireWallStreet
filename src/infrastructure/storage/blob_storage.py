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
import sys
import os

VERCEL_BLOB_AVAILABLE = False
# Initialize all names that would be imported from vercel_blob
put, get, list_blobs, del_blob, head, copy = (None,) * 6
BlobCommandOptions, BlobListOptions, BlobListResponse, BlobListResult, BlobPutOptions = (None,) * 5
DelBlobResult, HeadBlobResult, ListBlobResult, PutBlobResult = (None,) * 4
BlobNotFoundError, ListingResponse = (None,) * 2

try:
    logger.info(f"Attempting to import vercel_blob. Python version: {sys.version}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    logger.info(f"sys.path: {sys.path}")
    from vercel_blob import put, get, list_blobs, del_blob, PutBlobResult, BlobNotFoundError, ListingResponse
    logger.info("Successfully imported vercel_blob SDK.")
    VERCEL_BLOB_AVAILABLE = True
    logger.info("vercel_blob SDK imported successfully and all components assigned.")
except ImportError as e_import:
    logger.error(f"vercel_blob SDK import failed. Error: {e_import}", exc_info=True)
    VERCEL_BLOB_AVAILABLE = False

    async def _dummy_blob_op_import_error(*args, **kwargs):
        logger.error("vercel_blob SDK is not installed or failed to import (ImportError). Blob operation cannot proceed.")
        raise NotImplementedError(f"vercel_blob SDK not installed or failed to import: {e_import}")

    put = _dummy_blob_op_import_error
    get = _dummy_blob_op_import_error
    list_blobs = _dummy_blob_op_import_error
    del_blob = _dummy_blob_op_import_error
    head = _dummy_blob_op_import_error
    copy = _dummy_blob_op_import_error

    class _DummyBlobTypeImportError:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(f"vercel_blob SDK not installed or failed to import: {e_import}")
    
    BlobCommandOptions = _DummyBlobTypeImportError
    BlobListOptions = _DummyBlobTypeImportError
    BlobListResponse = _DummyBlobTypeImportError
    BlobListResult = _DummyBlobTypeImportError
    BlobPutOptions = _DummyBlobTypeImportError
    DelBlobResult = _DummyBlobTypeImportError
    HeadBlobResult = _DummyBlobTypeImportError
    ListBlobResult = _DummyBlobTypeImportError
    PutBlobResult = _DummyBlobTypeImportError
    BlobNotFoundError = _DummyBlobTypeImportError
    ListingResponse = _DummyBlobTypeImportError

except Exception as e_general:
    logger.error(f"An unexpected error occurred during vercel_blob SDK import or setup: {e_general}", exc_info=True)
    VERCEL_BLOB_AVAILABLE = False

    async def _dummy_blob_op_general_error(*args, **kwargs):
        logger.error(f"Unexpected error during vercel_blob setup ({type(e_general).__name__}). Blob operation cannot proceed.")
        raise NotImplementedError(f"Unexpected error during vercel_blob setup: {e_general}")

    put = _dummy_blob_op_general_error
    get = _dummy_blob_op_general_error
    list_blobs = _dummy_blob_op_general_error
    del_blob = _dummy_blob_op_general_error
    head = _dummy_blob_op_general_error
    copy = _dummy_blob_op_general_error

    class _DummyBlobTypeGeneralError:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(f"Unexpected error during vercel_blob setup: {e_general}")

    BlobCommandOptions = _DummyBlobTypeGeneralError
    BlobListOptions = _DummyBlobTypeGeneralError
    BlobListResponse = _DummyBlobTypeGeneralError
    BlobListResult = _DummyBlobTypeGeneralError
    BlobPutOptions = _DummyBlobTypeGeneralError
    DelBlobResult = _DummyBlobTypeGeneralError
    HeadBlobResult = _DummyBlobTypeGeneralError
    ListBlobResult = _DummyBlobTypeGeneralError
    PutBlobResult = _DummyBlobTypeGeneralError
    BlobNotFoundError = _DummyBlobTypeGeneralError
    ListingResponse = _DummyBlobTypeGeneralError

# Re-initialize logger as the previous one might have been shadowed if local_blob was imported
logger = logging.getLogger(__name__)

# Environment variables for Vercel Blob
BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
BLOB_PREFIX = "automations"

class BlobStorageAdapter:
    """Adapter for Vercel Blob Storage API for JSON data."""

    @staticmethod
    def is_available() -> bool:
        """Check if the Vercel Blob Storage adapter is considered available.

        Availability depends solely on the presence of the BLOB_READ_WRITE_TOKEN.
        
        Returns:
            bool: True if the token is present, False otherwise.
        """
        if BLOB_READ_WRITE_TOKEN:
            logger.debug("BLOB_READ_WRITE_TOKEN is present. BlobStorageAdapter reports as available.")
            return True
        else:
            logger.info("BLOB_READ_WRITE_TOKEN is not set. BlobStorageAdapter reports as unavailable.")
            return False
        
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
