"""
Local mock implementation of Vercel Blob storage for development.
This module provides local file-based storage with the same API as Vercel Blob.
"""
import os
import json
import logging
import shutil
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
import aiofiles
import aiofiles.os
import asyncio

logger = logging.getLogger(__name__)

# Local storage directory
LOCAL_BLOB_DIR = os.getenv("LOCAL_BLOB_DIR", "data/blobs")


class MockBlobResponse:
    """Mock implementation of Vercel Blob response."""
    
    def __init__(self, filepath: str, content: bytes):
        self.filepath = filepath
        self.content = content
    
    async def text(self) -> str:
        """Return content as string."""
        return self.content.decode('utf-8')
    
    async def arrayBuffer(self) -> bytes:
        """Return content as bytes."""
        return self.content


class BlobMetadata:
    """Metadata for a blob."""
    
    def __init__(self, pathname: str, size: int, uploadedAt: datetime):
        self.pathname = pathname
        self.size = size
        self.uploadedAt = uploadedAt
        self.url = f"http://localhost:8000/blobs/{pathname}"


class ListingResponse:
    """Response for list_blobs."""
    
    def __init__(self, blobs: List[BlobMetadata], cursor: Optional[str] = None):
        self.blobs = blobs
        self.cursor = cursor


class PutBlobResult:
    """Result of put operation."""
    
    def __init__(self, pathname: str, size: int, uploadedAt: datetime):
        self.pathname = pathname
        self.size = size
        self.uploadedAt = uploadedAt
        self.url = f"http://localhost:8000/blobs/{pathname}"


class BlobNotFoundError(Exception):
    """Exception raised when a blob is not found."""
    pass


async def put(pathname: str, body: bytes, options: Dict[str, Any] = None) -> PutBlobResult:
    """
    Store data in the local blob storage.
    
    Args:
        pathname: Path/key for the blob
        body: Content to store
        options: Optional settings
        
    Returns:
        PutBlobResult: Result of the operation
    """
    # Ensure directory exists
    os.makedirs(LOCAL_BLOB_DIR, exist_ok=True)
    
    # Get full filepath
    filepath = os.path.join(LOCAL_BLOB_DIR, pathname)
    
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Write the blob
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(body)
    
    # Get file size
    size = len(body)
    
    # Create result
    result = PutBlobResult(
        pathname=pathname,
        size=size,
        uploadedAt=datetime.now()
    )
    
    logger.info(f"Stored blob at {filepath}")
    return result


async def get(pathname: str) -> Optional[MockBlobResponse]:
    """
    Get data from the local blob storage.
    
    Args:
        pathname: Path/key for the blob
        
    Returns:
        MockBlobResponse: The blob response with data
        
    Raises:
        BlobNotFoundError: If the blob is not found
    """
    # Get full filepath
    filepath = os.path.join(LOCAL_BLOB_DIR, pathname)
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise BlobNotFoundError(f"Blob not found: {pathname}")
    
    # Read the blob
    async with aiofiles.open(filepath, 'rb') as f:
        content = await f.read()
    
    return MockBlobResponse(filepath, content)


async def del_blob(pathname: str) -> bool:
    """
    Delete a blob from local storage.
    
    Args:
        pathname: Path/key for the blob
        
    Returns:
        bool: True if deleted, False otherwise
    """
    # Get full filepath
    filepath = os.path.join(LOCAL_BLOB_DIR, pathname)
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise BlobNotFoundError(f"Blob not found: {pathname}")
    
    # Delete the blob
    await aiofiles.os.remove(filepath)
    
    # Remove empty directories
    dirpath = os.path.dirname(filepath)
    try:
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
    except OSError:
        pass
    
    logger.info(f"Deleted blob at {filepath}")
    return True


async def list_blobs(options: Dict[str, Any] = None) -> ListingResponse:
    """
    List blobs in local storage.
    
    Args:
        options: Optional settings including prefix and cursor
        
    Returns:
        ListingResponse: Result containing blob metadata
    """
    options = options or {}
    prefix = options.get('prefix', '')
    limit = options.get('limit', 100)
    cursor = options.get('cursor', None)
    
    # Ensure directory exists
    os.makedirs(LOCAL_BLOB_DIR, exist_ok=True)
    
    # List all blobs with prefix
    blob_list = []
    start_idx = int(cursor) if cursor else 0
    count = 0
    
    for root, _, files in os.walk(os.path.join(LOCAL_BLOB_DIR)):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, LOCAL_BLOB_DIR)
            
            # Check if it matches the prefix
            if prefix and not relative_path.startswith(prefix):
                continue
            
            # Apply cursor pagination
            if count < start_idx:
                count += 1
                continue
            
            # Check limit
            if len(blob_list) >= limit:
                break
            
            # Get file stat
            stat = os.stat(full_path)
            
            # Create metadata
            metadata = BlobMetadata(
                pathname=relative_path,
                size=stat.st_size,
                uploadedAt=datetime.fromtimestamp(stat.st_mtime)
            )
            
            blob_list.append(metadata)
    
    # Create response with cursor for next page
    next_cursor = str(start_idx + len(blob_list)) if len(blob_list) == limit else None
    
    return ListingResponse(blobs=blob_list, cursor=next_cursor)


async def clear_local_blobs() -> None:
    """
    Clear all local blobs. Useful for testing.
    """
    if os.path.exists(LOCAL_BLOB_DIR):
        shutil.rmtree(LOCAL_BLOB_DIR)
        os.makedirs(LOCAL_BLOB_DIR, exist_ok=True)
        logger.info(f"Cleared all local blobs in {LOCAL_BLOB_DIR}")
    else:
        os.makedirs(LOCAL_BLOB_DIR, exist_ok=True)
        logger.info(f"Created local blob directory: {LOCAL_BLOB_DIR}")
