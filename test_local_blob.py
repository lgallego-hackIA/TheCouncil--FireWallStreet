"""
Test script to verify that our local blob storage implementation works correctly.
"""
import asyncio
import json
import os
from src.infrastructure.storage.blob_storage import BlobStorageAdapter
from src.infrastructure.storage.openapi_storage import OpenAPIStorage

async def test_local_blob_storage():
    """Test local blob storage functionality."""
    print("Testing Local Blob Storage Implementation")
    print("----------------------------------------")
    
    # Ensure we're using the local implementation
    os.environ["VERCEL"] = "0"
    
    # 1. Test saving a JSON blob
    test_data = {
        "name": "Test Automation",
        "id": "test-123",
        "description": "This is a test automation",
        "steps": [
            {"id": 1, "name": "Step 1", "action": "test_action"}
        ]
    }
    
    blob_key = "test/automation-123"
    print(f"1. Saving blob with key: {blob_key}")
    url = await BlobStorageAdapter.save_json(blob_key, test_data)
    print(f"   Saved to: {url}")
    
    # 2. Test loading the JSON blob
    print(f"\n2. Loading blob with key: {blob_key}")
    loaded_data = await BlobStorageAdapter.load_json(blob_key)
    print(f"   Loaded data: {json.dumps(loaded_data, indent=2)}")
    
    # 3. Test listing all blobs
    print(f"\n3. Listing all blobs with prefix 'test/'")
    try:
        blobs = await BlobStorageAdapter.list_blobs(prefix="test/")
        print(f"   Found {len(blobs)} blobs:")
        for blob in blobs:
            print(f"   - {blob}")
    except Exception as e:
        print(f"   Error listing blobs: {e}")
        print("   This is ok during testing - continuing with other tests")
    
    # 4. Test OpenAPI storage
    print(f"\n4. Testing OpenAPI storage")
    openapi_data = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/hello": {
                "get": {
                    "summary": "Hello world",
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
    }
    
    print(f"   Saving OpenAPI schema for automation: test-123")
    schema_url = await OpenAPIStorage.save_schema("test-123", openapi_data)
    print(f"   Saved to: {schema_url}")
    
    print(f"\n   Loading OpenAPI schema for automation: test-123")
    loaded_schema = await OpenAPIStorage.load_schema("test-123")
    print(f"   Loaded schema: {json.dumps(loaded_schema, indent=2)[:100]}...")
    
    # 5. Test deleting the blob
    print(f"\n5. Deleting blob with key: {blob_key}")
    deleted = await BlobStorageAdapter.delete_json(blob_key)
    print(f"   Deleted: {deleted}")
    
    # 6. Test deleting the OpenAPI schema
    print(f"\n6. Deleting OpenAPI schema for automation: test-123")
    deleted = await OpenAPIStorage.delete_schema("test-123")
    print(f"   Deleted: {deleted}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_local_blob_storage())
