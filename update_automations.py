#!/usr/bin/env python
"""
Script to update existing automation files with required fields
"""
import os
import json
import glob

def update_automation_files():
    # Find all automation files in the automations directory
    automation_dir = os.path.join("data", "automations")
    automation_files = glob.glob(os.path.join(automation_dir, "*.json"))
    
    # Also update blob storage files
    blob_dir = os.path.join("data", "blobs", "automations")
    blob_files = glob.glob(os.path.join(blob_dir, "*.json"))
    
    print(f"Found {len(automation_files)} automation files in regular storage")
    print(f"Found {len(blob_files)} automation files in blob storage")
    
    for file_path in automation_files + blob_files:
        if "sample.json" in file_path:
            print(f"Skipping sample file: {file_path}")
            continue
            
        print(f"Processing: {file_path}")
        
        try:
            # Read the existing data
            with open(file_path, "r") as f:
                automation = json.load(f)
                
            # Add required fields if they don't exist
            if "version" not in automation:
                automation["version"] = "1.0.0"
                print(f"  Added version field")
                
            if "base_path" not in automation:
                automation["base_path"] = f"/{automation['name']}"
                print(f"  Added base_path field")
            
            # Update endpoints with summary field
            if "endpoints" in automation:
                for i, endpoint in enumerate(automation["endpoints"]):
                    if "summary" not in endpoint:
                        # Use description as summary if available, otherwise generic text
                        summary = endpoint.get("description", f"Endpoint {endpoint['method']} {endpoint['path']}")
                        endpoint["summary"] = summary
                        print(f"  Added summary field to endpoint {i+1}")
            
            # Save the updated data
            with open(file_path, "w") as f:
                json.dump(automation, f, indent=2)
            
            print(f"  Successfully updated: {file_path}")
            
        except Exception as e:
            print(f"  Error updating {file_path}: {e}")
    
    print("Update completed!")

if __name__ == "__main__":
    update_automation_files()
