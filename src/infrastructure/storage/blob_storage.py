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
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
import base64
from datetime import timedelta

# Set up logger
logger = logging.getLogger(__name__)
import sys
import os

VERCEL_BLOB_AVAILABLE = False
# Initialize all names that would be imported from vercel_blob
put, head, copy = (None,) * 3 # SDK functions imported directly
# del and list will be imported directly and then aliased
delete_blob_sdk, list_blobs_sdk = None, None # Aliases to be assigned after import
# Actual SDK functions will be imported as 'list' and 'del', then aliased or used directly.
# For clarity in our module, we'll use list_blobs_sdk and delete_blob_sdk internally for the SDK functions.
# Initial state for SDK components
local_sdk_put = None
local_sdk_head = None
local_sdk_delete = None
local_sdk_list = None
local_sdk_copy = None
local_sdk_download_file = None # From the local blob_store.py

# Custom error types from the local SDK (to be imported)
LocalBlobConfigError = None
LocalBlobRequestError = None
LocalBlobFileError = None

_CACHED_IMPORT_ERROR_DETAILS = "No ImportError occurred or details not captured."
VERCEL_BLOB_AVAILABLE = False

# CRITICAL DEBUG PRINT 2
print("BLOB_STORAGE.PY: ATTEMPTING LOCAL VERCEL_BLOB SDK IMPORT BLOCK", file=sys.stderr)
sys.stderr.flush()

try:
    from src.infrastructure.database.vercel_blob import blob_store
    from src.infrastructure.database.vercel_blob.errors import (
        BlobConfigError as LocalBlobConfigError,
        BlobRequestError as LocalBlobRequestError,
        BlobFileError as LocalBlobFileError
    )

    local_sdk_put = blob_store.put
    local_sdk_head = blob_store.head
    local_sdk_delete = blob_store.delete
    local_sdk_list = blob_store.list
    local_sdk_copy = blob_store.copy
    local_sdk_download_file = blob_store.download_file

    if not all(callable(f) for f in [local_sdk_put, local_sdk_head, local_sdk_delete, local_sdk_list, local_sdk_copy, local_sdk_download_file]):
        raise ImportError("One or more essential functions from local blob_store are not callable.")

    logger.info("Successfully imported local Vercel Blob SDK (src.infrastructure.database.vercel_blob).")
    VERCEL_BLOB_AVAILABLE = True

except ImportError as e_import:
    _CACHED_IMPORT_ERROR_DETAILS = traceback.format_exc()
    print(f"BLOB_STORAGE.PY: CAUGHT IMPORT_ERROR importing local SDK: {str(e_import)}. Details captured:\n{_CACHED_IMPORT_ERROR_DETAILS}", file=sys.stderr)
    sys.stderr.flush()
    VERCEL_BLOB_AVAILABLE = False
    LocalBlobConfigError = Exception
    LocalBlobRequestError = Exception
    LocalBlobFileError = Exception

except Exception as e_general:
    _CACHED_IMPORT_ERROR_DETAILS = traceback.format_exc()
    print(f"BLOB_STORAGE.PY: CAUGHT GENERAL_EXCEPTION during local SDK import: {str(e_general)}. Details:\n{_CACHED_IMPORT_ERROR_DETAILS}", file=sys.stderr)
    sys.stderr.flush()
    VERCEL_BLOB_AVAILABLE = False
    LocalBlobConfigError = Exception
    LocalBlobRequestError = Exception
    LocalBlobFileError = Exception

if not VERCEL_BLOB_AVAILABLE:
    # Define a synchronous dummy for consistency with the local SDK's nature
    def _dummy_local_sdk_op_sync(*args, **kwargs):
        logger.error(f"Local Vercel Blob SDK is not available. Operation cannot proceed. Import error details: {_CACHED_IMPORT_ERROR_DETAILS}")
        raise NotImplementedError(f"Local Vercel Blob SDK not available. Check logs. Details: {_CACHED_IMPORT_ERROR_DETAILS}")

    local_sdk_put = _dummy_local_sdk_op_sync
    local_sdk_head = _dummy_local_sdk_op_sync
    local_sdk_delete = _dummy_local_sdk_op_sync
    local_sdk_list = _dummy_local_sdk_op_sync
    local_sdk_copy = _dummy_local_sdk_op_sync
    local_sdk_download_file = _dummy_local_sdk_op_sync

    if LocalBlobConfigError is None: LocalBlobConfigError = Exception
    if LocalBlobRequestError is None: LocalBlobRequestError = Exception
    if LocalBlobFileError is None: LocalBlobFileError = Exception

class LocalSDKError(Exception):
    """Base class for errors originating from the local Vercel Blob SDK wrapper."""
    pass

if LocalBlobRequestError and not issubclass(LocalBlobRequestError, LocalSDKError) and LocalBlobRequestError is not Exception:
    class WrappedLocalBlobRequestError(LocalSDKError, LocalBlobRequestError): pass
    LocalBlobRequestError = WrappedLocalBlobRequestError
elif LocalBlobRequestError is Exception:
    class GenericLocalBlobRequestError(LocalSDKError): pass
    LocalBlobRequestError = GenericLocalBlobRequestError

# Base URL for constructing direct blob URLs for local SDK head/delete operations
VERCEL_BLOB_API_BASE_URL = "https://blob.vercel-storage.com"

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
        """Check if the Vercel Blob Storage (local SDK version) is available and configured."""
        if not VERCEL_BLOB_AVAILABLE:
            logger.warning(
                "BlobStorageAdapter: VERCEL_BLOB_AVAILABLE is False. Local SDK import likely failed. "
                f"Cached import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            print(
                "BLOB_STORAGE.PY: is_available() - VERCEL_BLOB_AVAILABLE is False. Local SDK import failed.",
                file=sys.stderr
            )
            sys.stderr.flush()
            return False

        if not BLOB_READ_WRITE_TOKEN:
            logger.info("BlobStorageAdapter: BLOB_READ_WRITE_TOKEN is not set. Reports as unavailable.")
            print("BLOB_STORAGE.PY: is_available() - BLOB_READ_WRITE_TOKEN is not set.", file=sys.stderr)
            sys.stderr.flush()
            return False
        
        essential_sdk_functions = {
            "put": local_sdk_put,
            "head": local_sdk_head,
            "delete": local_sdk_delete,
            "list": local_sdk_list,
            "copy": local_sdk_copy,
            "download_file": local_sdk_download_file,
        }
        
        non_functional_components = [
            name for name, func in essential_sdk_functions.items() 
            if func is None or (hasattr(func, '__name__') and func.__name__ == '_dummy_local_sdk_op_sync')
        ]

        if non_functional_components:
            logger.error(
                f"BlobStorageAdapter: Local SDK is marked VERCEL_BLOB_AVAILABLE and Token is set, "
                f"but essential functions are missing or dummies: {non_functional_components}. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            print(
                f"BLOB_STORAGE.PY: is_available() - Essential local SDK functions missing/dummies: {non_functional_components}",
                file=sys.stderr
            )
            sys.stderr.flush()
            return False

        logger.debug("BlobStorageAdapter: Local SDK (VERCEL_BLOB_AVAILABLE=True), Token set, and essential functions seem okay. Reports as available.")
        return True
        
    @staticmethod
    async def list_blobs(prefix: str = "", limit: Optional[int] = None, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List blobs from Vercel Blob Storage using the local SDK.
        
        Args:
            prefix: Prefix to filter blobs by.
            limit: Maximum number of blobs to return.
            cursor: Cursor for pagination.
            
        Returns:
            Dict[str, Any]: A dictionary containing 'blobs' (list of dicts, each with blob details),
                            'cursor' (str, for pagination), and 'hasMore' (bool).
                            Returns an empty dict with empty blobs list on error.
        
        Raises:
            RuntimeError: If blob storage is unavailable or misconfigured.
            LocalBlobRequestError: For API errors during the list operation.
        """
        if not BlobStorageAdapter.is_available():
            logger.error(
                f"BlobStorageAdapter.is_available() returned False. Cannot list blobs for prefix '{prefix}'. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            raise RuntimeError(
                "Blob storage is unavailable or misconfigured. Check logs for details, "
                f"especially VERCEL_BLOB_AVAILABLE status and import errors: {_CACHED_IMPORT_ERROR_DETAILS}"
            )

        # The local SDK's list function handles its own default prefixing (e.g., within "automations/")
        # if the provided prefix is empty or doesn't conform to its expected structure.
        # We pass the user-provided prefix directly; if it's empty, the SDK uses its default.
        logger.info(f"Attempting to list blobs with prefix: '{prefix}' (limit: {limit}, cursor: {cursor}) using local SDK.")

        try:
            loop = asyncio.get_running_loop()
            response_dict = await loop.run_in_executor(
                None,
                local_sdk_list,
                prefix if prefix else None, # Pass None if prefix is empty, SDK handles default
                limit,
                'all', # mode ('all' or 'folded')
                cursor,
                BLOB_READ_WRITE_TOKEN
            )

            if not isinstance(response_dict, dict) or 'blobs' not in response_dict:
                logger.error(f"Unexpected response format from local_sdk_list for prefix '{prefix}': {response_dict}")
                return {'blobs': [], 'cursor': None, 'hasMore': False}
            
            blobs_list = response_dict.get('blobs', [])
            if not isinstance(blobs_list, list):
                logger.warning(f"local_sdk_list returned 'blobs' not as a list for prefix '{prefix}'. Got: {type(blobs_list)}. Correcting to empty list.")
                blobs_list = []

            logger.info(f"Successfully listed {len(blobs_list)} blobs for prefix '{prefix}'. Has more: {response_dict.get('hasMore')}")
            return {
                'blobs': blobs_list, 
                'cursor': response_dict.get('cursor'),
                'hasMore': response_dict.get('hasMore', False)
            }

        except LocalBlobRequestError as e:
            logger.error(f"Local SDK API request error listing blobs with prefix '{prefix}': {e}", exc_info=True)
            raise
        except LocalBlobConfigError as e:
            logger.error(f"Local SDK configuration error listing blobs with prefix '{prefix}': {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing blobs with prefix '{prefix}': {e}", exc_info=True)
            if isinstance(e, (LocalBlobRequestError, LocalBlobConfigError, LocalSDKError)):
                 raise
            raise LocalSDKError(f"Unexpected error listing blobs with prefix '{prefix}': {e}")

    @staticmethod
    async def save_json(key: str, data: Dict[str, Any], add_random_suffix: bool = False, folder: str = "") -> str:
        """
        Save JSON data to Vercel Blob Storage using the local SDK.
        
        Args:
            key: The key for the blob (used in the filename, without .json extension).
            data: The data to save.
            add_random_suffix: Whether to add a random suffix to the blob name (defaults to False).
            
        Returns:
            str: The URL of the saved blob.
            
        Raises:
            RuntimeError: If blob storage is unavailable or misconfigured.
            LocalBlobRequestError: For API errors during the put operation.
            LocalBlobConfigError: For configuration errors with the local SDK.
            LocalBlobFileError: For file-related errors (less likely for put).
            Exception: For any other unexpected errors.
        """
        if not BlobStorageAdapter.is_available():
            logger.error(
                f"BlobStorageAdapter.is_available() returned False. Cannot save JSON for key '{key}'. "
                f"Token set: {bool(BLOB_READ_WRITE_TOKEN)}. "
                f"VERCEL_BLOB_AVAILABLE: {VERCEL_BLOB_AVAILABLE}. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            raise RuntimeError(
                "Blob storage is unavailable or misconfigured. Check logs for details, "
                f"especially VERCEL_BLOB_AVAILABLE status and import errors: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
        if folder:
            pathname = f"{BLOB_PREFIX}/{folder}/{key}.json"
        else:
            pathname = f"{BLOB_PREFIX}/{key}.json"
        json_body_bytes = json.dumps(data).encode('utf-8')

        logger.info(f"Attempting to save JSON to blob: {pathname} (add_random_suffix: {add_random_suffix})")

        try:
            loop = asyncio.get_running_loop()
            options = {
                "token": BLOB_READ_WRITE_TOKEN,
                "addRandomSuffix": "true" if add_random_suffix else "false",
                # Content-Type is typically inferred by the local SDK's put via guess_mime_type(pathname)
                # If 'application/json' needs to be forced and guess_mime_type is insufficient,
                # the local SDK's put function might need a way to override x-content-type via options.
            }
            response_dict = await loop.run_in_executor(
                None,
                local_sdk_put,
                pathname,        # path
                json_body_bytes, # data
                options,         # options dictionary
                10,              # timeout (default for local_sdk_put)
                False,           # verbose (default for local_sdk_put)
                False            # multipart (explicitly False for these JSON saves)
            )
            
            if not isinstance(response_dict, dict) or 'url' not in response_dict:
                logger.error(f"Unexpected response format from local_sdk_put for {pathname}: {response_dict}")
                raise LocalSDKError(f"Unexpected response format from local_sdk_put for {pathname}. Expected dict with 'url'.")

            blob_url = response_dict['url']
            logger.info(f"Successfully saved JSON to blob: {pathname}, URL: {blob_url}")
            return blob_url

        except LocalBlobRequestError as e:
            logger.error(f"Local SDK API request error saving JSON to {pathname}: {e}", exc_info=True)
            raise
        except LocalBlobConfigError as e:
            logger.error(f"Local SDK configuration error saving JSON to {pathname}: {e}", exc_info=True)
            raise
        except LocalBlobFileError as e:
            logger.error(f"Local SDK file error saving JSON to {pathname}: {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding response from local_sdk_put for {pathname}: {e}", exc_info=True)
            raise LocalSDKError(f"Error decoding response from local_sdk_put for {pathname}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving JSON to {pathname}: {e}", exc_info=True)
            if isinstance(e, (LocalBlobRequestError, LocalBlobConfigError, LocalBlobFileError, LocalSDKError)):
                 raise
            raise LocalSDKError(f"Unexpected error saving JSON to {pathname}: {e}")

    @staticmethod
    async def load_json(key: str) -> Dict[str, Any]:
        """
        Load JSON data from Vercel Blob Storage using the local SDK.
        
        Args:
            key: The key for the blob (filename without .json extension, relative to BLOB_PREFIX).
            
        Returns:
            Dict[str, Any]: The loaded JSON data
            
        Raises:
            FileNotFoundError: If the blob is not found.
            RuntimeError: If there's an issue fetching or parsing the blob.
            LocalBlobRequestError: For API errors.
        """
        if not BlobStorageAdapter.is_available():
            logger.error(
                f"BlobStorageAdapter.is_available() returned False. Cannot load JSON for key '{key}'. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            raise RuntimeError(f"Blob storage is unavailable, cannot load key '{key}'. Check logs. Details: {_CACHED_IMPORT_ERROR_DETAILS}")

        pathname = f"{BLOB_PREFIX}/{key}.json"
        full_api_url = f"{VERCEL_BLOB_API_BASE_URL}/{pathname}"
        download_url = None

        logger.debug(f"Attempting to get metadata for blob via local SDK head: {full_api_url}")

        try:
            loop = asyncio.get_running_loop()
            head_response_headers = await loop.run_in_executor(
                None,
                local_sdk_head,
                full_api_url,
                BLOB_READ_WRITE_TOKEN
            )

            if not isinstance(head_response_headers, dict):
                logger.warning(f"Blob metadata (headers) not found or not a dict for key '{key}' (URL: {full_api_url}). Head response: {head_response_headers}")
                raise FileNotFoundError(f"Blob with key '{key}' not found (invalid head response). URL: {full_api_url}")

            download_url = head_response_headers.get('x-download-url')
            if not download_url:
                logger.warning(f"No 'x-download-url' in head response headers for {full_api_url}. Headers: {head_response_headers}")
                raise FileNotFoundError(f"Blob with key '{key}' not found or no download URL available via head. URL: {full_api_url}")

            logger.debug(f"Successfully fetched metadata for {pathname}. Download URL from 'x-download-url': {download_url}")

            async with httpx.AsyncClient() as client:
                logger.debug(f"Attempting to download blob content from: {download_url}")
                response = await client.get(download_url)
                response.raise_for_status()
                loaded_data = response.json()
                logger.info(f"Successfully loaded and parsed JSON blob with key '{key}' from {download_url}")
                return loaded_data

        except LocalBlobRequestError as e:
            error_str = str(e).lower()
            if "404" in error_str or "not_found" in error_str or "no such file" in error_str:
                logger.warning(f"Blob not found via local_sdk_head for key '{key}' (URL: {full_api_url}): {e}")
                raise FileNotFoundError(f"Blob with key '{key}' not found. URL: {full_api_url}") from e
            logger.error(f"Local SDK API request error loading JSON for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when downloading blob for key '{key}' from {download_url}: {e.response.status_code} - {e.response.text}", exc_info=True)
            if e.response.status_code == 404:
                 raise FileNotFoundError(f"Blob content not found at download URL for key '{key}'. URL: {download_url}") from e
            raise RuntimeError(f"Failed to download blob for key '{key}' due to HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error when downloading blob for key '{key}' from {download_url}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to download blob for key '{key}' due to network error.") from e
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from blob for key '{key}'. Download URL: {download_url}. Error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to parse JSON from blob for key '{key}'.") from e
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading JSON for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            if isinstance(e, (LocalBlobRequestError, LocalBlobConfigError, LocalBlobFileError, LocalSDKError, RuntimeError)):
                 raise
            raise LocalSDKError(f"Unexpected error loading JSON for key '{key}': {e}") from e

    @staticmethod
    async def delete_json(key: str) -> bool:
        """
        Delete JSON data from Vercel Blob Storage using the local SDK.
        
        Args:
            key: The key for the blob (filename without .json extension, relative to BLOB_PREFIX).
            
        Returns:
            bool: True if the blob was deleted or not found, False on error.
        """
        if not BlobStorageAdapter.is_available():
            logger.error(
                f"BlobStorageAdapter.is_available() returned False. Cannot delete JSON for key '{key}'. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            return False 

        pathname = f"{BLOB_PREFIX}/{key}.json"
        full_api_url = f"{VERCEL_BLOB_API_BASE_URL}/{pathname}"
        
        logger.debug(f"Attempting to delete blob via local SDK: {full_api_url}")

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                local_sdk_delete,
                [full_api_url],
                BLOB_READ_WRITE_TOKEN
            )
            logger.info(f"Successfully initiated deletion for blob with key '{key}' (URL: {full_api_url})")
            return True
        except LocalBlobRequestError as e:
            error_str = str(e).lower()
            if "404" in error_str or "not_found" in error_str or "no such file" in error_str:
                logger.warning(f"Blob not found during deletion attempt for key '{key}' (URL: {full_api_url}), considering as success: {e}")
                return True
            logger.error(f"Local SDK API request error deleting JSON for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting JSON for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            return False

    @staticmethod
    async def download_blob(key: str) -> bytes:
        """
        Download raw blob data from Vercel Blob Storage using the local SDK.
        
        Args:
            key: The key for the blob (filename relative to BLOB_PREFIX, can include extension).
            
        Returns:
            bytes: The raw blob data.
            
        Raises:
            FileNotFoundError: If the blob is not found.
            RuntimeError: If there's an issue fetching the blob.
            LocalBlobRequestError: For API errors.
        """
        if not BlobStorageAdapter.is_available():
            logger.error(
                f"BlobStorageAdapter.is_available() returned False. Cannot download blob for key '{key}'. "
                f"Import error details: {_CACHED_IMPORT_ERROR_DETAILS}"
            )
            raise RuntimeError(f"Blob storage is unavailable, cannot download key '{key}'. Check logs. Details: {_CACHED_IMPORT_ERROR_DETAILS}")

        pathname = f"{BLOB_PREFIX}/{key}"
        full_api_url = f"{VERCEL_BLOB_API_BASE_URL}/{pathname}"
        download_url = None

        logger.debug(f"Attempting to get metadata for raw blob download via local SDK head: {full_api_url}")
        
        try:
            loop = asyncio.get_running_loop()
            head_response_headers = await loop.run_in_executor(
                None,
                local_sdk_head,
                full_api_url,
                BLOB_READ_WRITE_TOKEN
            )

            if not isinstance(head_response_headers, dict):
                logger.warning(f"Blob metadata (headers) not found or not a dict for key '{key}' (URL: {full_api_url}). Head response: {head_response_headers}")
                raise FileNotFoundError(f"Blob with key '{key}' not found (invalid head response). URL: {full_api_url}")

            download_url = head_response_headers.get('x-download-url')
            if not download_url:
                logger.warning(f"No 'x-download-url' in head response headers for {full_api_url}. Headers: {head_response_headers}")
                raise FileNotFoundError(f"Blob with key '{key}' not found or no download URL available via head. URL: {full_api_url}")

            logger.debug(f"Successfully fetched metadata for raw blob {pathname}. Download URL: {download_url}")

            async with httpx.AsyncClient() as client:
                logger.debug(f"Attempting to download raw blob content from: {download_url}")
                response = await client.get(download_url)
                response.raise_for_status()
                blob_content = response.content
                logger.info(f"Successfully downloaded raw blob with key '{key}' from {download_url}")
                return blob_content

        except LocalBlobRequestError as e:
            error_str = str(e).lower()
            if "404" in error_str or "not_found" in error_str or "no such file" in error_str:
                logger.warning(f"Raw blob not found via local_sdk_head for key '{key}' (URL: {full_api_url}): {e}")
                raise FileNotFoundError(f"Raw blob with key '{key}' not found. URL: {full_api_url}") from e
            logger.error(f"Local SDK API request error downloading raw blob for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when downloading raw blob for key '{key}' from {download_url}: {e.response.status_code} - {e.response.text}", exc_info=True)
            if e.response.status_code == 404:
                 raise FileNotFoundError(f"Raw blob content not found at download URL for key '{key}'. URL: {download_url}") from e
            raise RuntimeError(f"Failed to download raw blob for key '{key}' due to HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error when downloading raw blob for key '{key}' from {download_url}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to download raw blob for key '{key}' due to network error.") from e
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading raw blob for key '{key}' (URL: {full_api_url}): {e}", exc_info=True)
            if isinstance(e, (LocalBlobRequestError, LocalBlobConfigError, LocalBlobFileError, LocalSDKError, RuntimeError)):
                 raise
            raise LocalSDKError(f"Unexpected error downloading raw blob for key '{key}': {e}") from e
