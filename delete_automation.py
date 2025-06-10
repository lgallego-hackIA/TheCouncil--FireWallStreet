#!/usr/bin/env python
"""
Script to safely remove an automation from theCouncil
"""
import os
import json
import sys
import shutil
import glob
from colorama import init, Fore, Style

# Initialize colorama
init()

def print_header(text):
    """Print a formatted header."""
    print(f"\n=== {text} ===")

def print_success(text):
    """Print a success message."""
    print(f"{Fore.GREEN}✓{Style.RESET_ALL} {text}")

def print_error(text):
    """Print an error message."""
    print(f"{Fore.RED}✗{Style.RESET_ALL} {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Fore.YELLOW}!{Style.RESET_ALL} {text}")

def get_input(prompt, default=None, validator=None):
    """Get user input with validation."""
    prompt_text = f"{prompt}"
    if default:
        prompt_text += f" [{default}]"
    prompt_text += ": "
    
    while True:
        value = input(prompt_text) or default
        if value is None:
            print_error("Input is required")
            continue
        
        if validator and not validator(value):
            print_error("Invalid input. Please try again.")
            continue
            
        return value

def find_automation_by_name(name):
    """Find automation files by name."""
    # Look through the automations directory
    automation_dir = os.path.join("data", "automations")
    
    if not os.path.exists(automation_dir):
        return None
    
    # Find the automation json file
    for file_name in os.listdir(automation_dir):
        if file_name.endswith(".json") and file_name != "sample.json":
            file_path = os.path.join(automation_dir, file_name)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if data.get("name") == name:
                        return data, file_path
            except:
                pass
    
    return None, None

def delete_automation():
    """Delete an automation from the system."""
    print_header("theCouncil Automation Removal Tool")
    print("This tool will remove an automation and all associated files.\n")
    
    # Get the automation name
    name = get_input("Automation name to remove")
    
    # Find the automation
    automation, file_path = find_automation_by_name(name)
    
    if not automation:
        print_error(f"Automation '{name}' not found!")
        return
    
    display_name = automation.get("display_name", name)
    
    print(f"\nFound automation: {display_name}")
    print(f"Description: {automation.get('description', 'No description')}")
    print(f"ID: {automation.get('id', 'Unknown')}")
    
    if not get_input("Are you sure you want to remove this automation? (y/n)", "n").lower() in ["y", "yes"]:
        print_warning("Removal cancelled.")
        return
    
    files_removed = []
    dirs_removed = []

    # 1. Remove the automation JSON file
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        files_removed.append(file_path)
        print_success(f"Removed automation file: {file_path}")
    
    # 2. Remove from blob storage
    blob_path = os.path.join("data", "blobs", "automations", f"{name}.json")
    if os.path.exists(blob_path):
        os.remove(blob_path)
        files_removed.append(blob_path)
        print_success(f"Removed blob storage file: {blob_path}")
    
    # 3. Remove OpenAPI schema
    openapi_path = os.path.join("data", "openapi", f"{name}.json")
    if os.path.exists(openapi_path):
        os.remove(openapi_path)
        files_removed.append(openapi_path)
        print_success(f"Removed OpenAPI schema: {openapi_path}")
    
    # 3b. Remove OpenAPI schema from blob storage
    blob_openapi_path = os.path.join("data", "blobs", "openapi", f"{name}.json")
    if os.path.exists(blob_openapi_path):
        os.remove(blob_openapi_path)
        files_removed.append(blob_openapi_path)
        print_success(f"Removed blob OpenAPI schema: {blob_openapi_path}")
    
    # 4. Remove router directory
    router_dir = os.path.join("src", "interfaces", "api", "routers", name)
    if os.path.exists(router_dir) and os.path.isdir(router_dir):
        shutil.rmtree(router_dir)
        dirs_removed.append(router_dir)
        print_success(f"Removed router directory: {router_dir}")
    
    # 5. Remove test directory
    test_dir = os.path.join("tests", "interfaces", "api", "routers", name)
    if os.path.exists(test_dir) and os.path.isdir(test_dir):
        shutil.rmtree(test_dir)
        dirs_removed.append(test_dir)
        print_success(f"Removed test directory: {test_dir}")
    
    print_header("Summary")
    print(f"Successfully removed automation '{display_name}'!")
    print(f"\nFiles removed: {len(files_removed)}")
    for file in files_removed:
        print(f"  - {file}")
        
    print(f"\nDirectories removed: {len(dirs_removed)}")
    for directory in dirs_removed:
        print(f"  - {directory}")
    
    print("\nReminder: You'll need to restart your API server for changes to take effect.")

if __name__ == "__main__":
    delete_automation()
