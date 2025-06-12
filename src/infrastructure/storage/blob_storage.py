"""
Vercel Blob Storage adapter for theCouncil.
This module provides functionality for storing and retrieving data from Vercel Blob Storage.
"""
import sys
import traceback
# CRITICAL DEBUG PRINT 1
print("BLOB_STORAGE.PY: TOP LEVEL EXECUTION STARTED", file=sys.stderr)
sys.stderr.flush()
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

_CACHED_IMPORT_ERROR_DETAILS = "No ImportError occurred or details not captured."

# CRITICAL DEBUG PRINT 2
print("BLOB_STORAGE.PY: ATTEMPTING VERCEL_BLOB IMPORT BLOCK", file=sys.stderr)
sys.stderr.flush()
try:
    logger.info(f"Attempting to import vercel_blob. Python version: {sys.version}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    logger.info(f"sys.path: {sys.path}")
    from vercel_blob import (
        put, get, list_blobs, del_blob, head, copy,
        BlobCommandOptions, BlobListOptions, BlobListResponse, BlobListResult, BlobPutOptions,
        DelBlobResult, HeadBlobResult, ListBlobResult, PutBlobResult,
        BlobNotFoundError, ListingResponse
    )
    logger.info("Successfully attempted to import all expected components from vercel_blob SDK.")
    VERCEL_BLOB_AVAILABLE = True
    logger.info("vercel_blob SDK imported successfully and all components assigned.")
except ImportError as e_import:
    _CACHED_IMPORT_ERROR_DETAILS = traceback.format_exc()
    # Now print, after details are captured
    print(f"BLOB_STORAGE.PY: CAUGHT IMPORT_ERROR: {str(e_import)}. Details captured:\n{_CACHED_IMPORT_ERROR_DETAILS}", file=sys.stderr)
    sys.stderr.flush()
    VERCEL_BLOB_AVAILABLE = False # Ensure this is set
    # DO NOT re-raise e_import here. Allow module to load with dummies.
    # The dummy assignments for ImportError case will follow.

    async def _dummy_blob_op_import_error(*args, **kwargs):
        logger.error("vercel_blob SDK is not installed or failed to import (ImportError). Blob operation cannot proceed.")
        raise NotImplementedError("vercel_blob SDK not installed or failed to import. Check logs for original ImportError details.")

    put = _dummy_blob_op_import_error
    get = _dummy_blob_op_import_error
    list_blobs = _dummy_blob_op_import_error
    del_blob = _dummy_blob_op_import_error
    head = _dummy_blob_op_import_error
    copy = _dummy_blob_op_import_error

    class _DummyBlobTypeImportError:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("vercel_blob SDK not installed or failed to import. Check logs for original ImportError details.")
    
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
    print(f"BLOB_STORAGE.PY: CAUGHT GENERAL_EXCEPTION: {str(e_general)}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    VERCEL_BLOB_AVAILABLE = False

    async def _dummy_blob_op_general_error(*args, **kwargs):
        logger.error(f"Unexpected error during vercel_blob setup. Blob operation cannot proceed.") # Removed type(e_general) for safety, full details in exc_info log
        raise NotImplementedError("Unexpected error during vercel_blob setup. Check logs for original Exception details.")

    put = _dummy_blob_op_general_error
    get = _dummy_blob_op_general_error
    list_blobs = _dummy_blob_op_general_error
    del_blob = _dummy_blob_op_general_error
    head = _dummy_blob_op_general_error
    copy = _dummy_blob_op_general_error

    class _DummyBlobTypeGeneralError:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Unexpected error during vercel_blob setup. Check logs for original Exception details.")

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

# CRITICAL DEBUG PRINT 5
if VERCEL_BLOB_AVAILABLE:
    print("BLOB_STORAGE.PY: VERCEL_BLOB_AVAILABLE is TRUE after import block", file=sys.stderr)
else:
    print("BLOB_STORAGE.PY: VERCEL_BLOB_AVAILABLE is FALSE after import block", file=sys.stderr)
sys.stderr.flush()

# Re-initialize logger as the previous one might have been shadowed if local_blob was imported
logger = logging.getLogger(__name__)

# Environment variables for Vercel Blob
BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
BLOB_PREFIX = "automations"

class BlobStorageAdapter:
    """Adapter for Vercel Blob Storage API for JSON data."""

    @staticmethod
    def is_available() -> bool:
        print("BLOB_STORAGE.PY: BlobStorageAdapter.is_available() CALLED", file=sys.stderr)
        sys.stderr.flush()

        if not VERCEL_BLOB_AVAILABLE:
            error_message = (
                "Vercel Blob Storage SDK (vercel_blob) failed to import or initialize correctly. "
                f"Cached ImportError details:\n{_CACHED_IMPORT_ERROR_DETAILS}"
            )
            logger.error(error_message)
            print(f"BLOB_STORAGE.PY: is_available() - VERCEL_BLOB_AVAILABLE is False. {error_message}", file=sys.stderr)
            sys.stderr.flush()
            return False

        if not BLOB_READ_WRITE_TOKEN:
            logger.info("BLOB_READ_WRITE_TOKEN is not set. BlobStorageAdapter reports as unavailable.")
            print("BLOB_STORAGE.PY: is_available() - BLOB_READ_WRITE_TOKEN is not set.", file=sys.stderr)
            sys.stderr.flush()
            return False
        
        # Check if essential components are assigned and not dummies
        # Assuming _dummy_blob_op_import_error is the one assigned on ImportError
        # and _dummy_blob_op_general_error for other errors.
        # We need to check against the actual function objects if possible, or by name if they are unique.
        # For simplicity, checking for None which is the initial state before any assignment.
        # And also checking against the known dummy function if VERCEL_BLOB_AVAILABLE was true but then components were bad.
        
        # A more robust check would be to see if they are the dummy functions.
        # This requires the dummy functions to be defined in a scope accessible here or passed.
        # For now, let's assume if VERCEL_BLOB_AVAILABLE is True, the components should be the real ones.
        # The primary failure mode we're debugging is VERCEL_BLOB_AVAILABLE becoming False due to ImportError.

        # Let's refine the check for actual components being usable
        # This part of the check is more relevant if VERCEL_BLOB_AVAILABLE was true, but something else went wrong.
        # However, the main goal now is to see the ImportError details if VERCEL_BLOB_AVAILABLE is false.
        
        # We can add a check for key components not being None if VERCEL_BLOB_AVAILABLE is True
        # This is a secondary check after the VERCEL_BLOB_AVAILABLE and TOKEN checks.
        essential_components = {
            "put": put,
            "get": get,
            "list_blobs": list_blobs,
            "del_blob": del_blob,
            "head": head,
            "copy": copy,
            "PutBlobResult": PutBlobResult,
            "BlobNotFoundError": BlobNotFoundError
        }
        missing_sdk_parts = [name for name, comp in essential_components.items() if comp is None or comp.__name__.startswith('_dummy_blob_op')]

        if missing_sdk_parts:
            logger.error(f"BlobStorageAdapter: VERCEL_BLOB_AVAILABLE is True and Token is set, but essential SDK components are missing or dummies: {missing_sdk_parts}")
            print(f"BLOB_STORAGE.PY: is_available() - Essential SDK components missing/dummies: {missing_sdk_parts}", file=sys.stderr)
            sys.stderr.flush()
            return False

        logger.debug("VERCEL_BLOB_AVAILABLE is True, Token is set, and essential components seem okay. BlobStorageAdapter reports as available.")
        return True
        
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
