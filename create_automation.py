#!/usr/bin/env python3
"""
Interactive wizard for creating new automations in theCouncil.
This script guides developers through the process of creating a new automation,
setting up the necessary files, and configuring the automation.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
import uuid
import re
import shutil
import colorama
from colorama import Fore, Style

# Initialize colorama for colored terminal output
colorama.init(autoreset=True)

# Helper functions for UI
def print_header(text):
    """Print a colored header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 50}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(50)}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 50}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {text}")

def print_error(text):
    """Print an error message."""
    print(f"{Fore.RED}✗ {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Fore.YELLOW}⚠ {text}")

def get_input(prompt, default=None, validator=None):
    """Get user input with optional default and validation."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if validator:
            is_valid, error = validator(user_input)
            if not is_valid:
                print_error(error)
                continue
        
        return user_input

def get_yes_no(prompt, default=None):
    """Get a yes/no answer from the user."""
    default_str = None
    if default:
        default = default.lower()
        if default.startswith('y'):
            default_str = 'y/N'
            default = True
        elif default.startswith('n'):
            default_str = 'Y/n'
            default = False
    
    while True:
        if default_str:
            user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
        else:
            user_input = input(f"{prompt} [y/n]: ").strip().lower()
        
        if not user_input and default is not None:
            return default
        
        if user_input.startswith('y'):
            return True
        elif user_input.startswith('n'):
            return False
        
        print_error("Please answer 'y' or 'n'.")

# Validators
def validate_name(name):
    """Validate automation name (alphanumeric and dashes)."""
    if not name:
        return False, "Name cannot be empty."
    
    if not re.match(r'^[a-zA-Z0-9-]+$', name):
        return False, "Name can only contain alphanumeric characters and dashes."
    
    return True, ""

def validate_not_empty(value):
    """Validate that a value is not empty."""
    if not value:
        return False, "Value cannot be empty."
    
    return True, ""

def validate_path(path):
    """Validate API path."""
    if not path:
        return False, "Path cannot be empty."
    
    if not path.startswith('/'):
        return False, "Path must start with a slash (/)."
    
    return True, ""

def validate_method(method):
    """Validate HTTP method."""
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
    
    if not method:
        return False, "Method cannot be empty."
    
    if method.upper() not in valid_methods:
        return False, f"Method must be one of: {', '.join(valid_methods)}."
    
    return True, ""

# Constant for template files
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")


def get_input(prompt, default=None, validator=None):
    """
    Get input from the user with validation.
    
    Args:
        prompt: The prompt to show the user
        default: Default value if user enters nothing
        validator: Function to validate the input
        
    Returns:
        The validated input
    """
    display_default = f" [{default}]" if default else ""
    while True:
        value = input(f"{Colors.CYAN}{prompt}{display_default}: {Colors.ENDC}")
        if not value and default:
            value = default
            
        if validator and not validator(value):
            print_error("Invalid input. Please try again.")
            continue
            
        return value


def validate_name(name):
    """Validate automation name (alphanumeric and dashes)."""
    return bool(re.match(r'^[a-zA-Z0-9-]+$', name))


def validate_path(path):
    """Validate API path (starts with / and valid URL path)."""
    return path.startswith('/') and re.match(r'^[a-zA-Z0-9/_\-{}]+$', path)


def validate_method(method):
    """Validate HTTP method."""
    return method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

def sanitize_for_python_identifier(text: str) -> str:
    """Converts a string into a valid Python function name prefix."""
    # Replace non-alphanumeric characters (except underscores) with underscores
    s = re.sub(r'[^0-9a-zA-Z_]', '_', text)
    # Remove leading/trailing underscores that might result from replacements like /items -> _items_
    s = s.strip('_')
    # Replace multiple consecutive underscores with a single one
    s = re.sub(r'_+', '_', s)
    # Ensure it doesn't start with a digit
    if s and s[0].isdigit():
        s = '_' + s
    # Ensure it's not empty after sanitization
    if not s:
        return "handle_generic_endpoint" # Default if everything is stripped
    return f"handle_{s.lower()}"


def validate_yes_no(value):
    """Validate yes/no answer."""
    return value.lower() in ['y', 'n', 'yes', 'no']


def get_yes_no(prompt, default="y"):
    """Get a yes/no answer from the user."""
    value = get_input(prompt, default, validate_yes_no)
    return value.lower() in ['y', 'yes']


def validate_not_empty(value):
    """Validate that a value is not empty."""
    return bool(value.strip())


async def create_automation():
    """Run the automation creation wizard."""
    print_header("theCouncil Automation Creation Wizard")
    print("This wizard will help you create a new automation for theCouncil.")
    print("Follow the prompts to set up your automation structure and files.")
    
    # Step 1: Get basic automation info
    print_header("Basic Information")
    name = get_input("Automation name (alphanumeric and dashes)", validator=validate_name)
    display_name = get_input("Display name", default=name.title())
    description = get_input("Description", validator=validate_not_empty)
    
    # Create automation ID
    automation_id = str(uuid.uuid4())
    
    # Step 2: Define endpoints
    print_header("Endpoints")
    print("Now let's define the endpoints for your automation.")
    print("You can add multiple endpoints. For each endpoint, you'll need to specify:")
    print("- Path (e.g., /users/{user_id})")
    print("- HTTP method (GET, POST, PUT, DELETE, PATCH)")
    print("- Description")
    
    endpoints = []
    while True:
        path = get_input("Path", validator=validate_path)
        method = get_input("HTTP Method", default="GET", validator=validate_method).upper()
        endpoint_description = get_input("Endpoint description")
        
        endpoint_id = str(uuid.uuid4())
        endpoints.append({
            "id": endpoint_id,
            "path": path,
            "method": method,
            "description": endpoint_description
        })
        
        if not get_yes_no("Add another endpoint?", default="n"):
            break
    
    # Create the automation object as a dictionary
    automation = {
        "id": automation_id,
        "name": name,
        "display_name": display_name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "version": "1.0.0",  # Required by automation registry
        "base_path": f"/{name}",  # Required by automation registry
        "endpoints": [],
        "db_config": {
            "type": "mongodb",
            "config": {
                "connection_string": os.getenv("DATABASE_URL", "mongodb://localhost:27017/council_db"),
                "database": "council_db",
                "collection": f"{name.replace('-', '_')}_collection"
            }
        },
    }
    
    # Initialize list to store details for handlers.py generation
    # This will be accessed later to generate the handlers.py file
    if not hasattr(create_automation, "endpoint_details_for_handlers"):
        create_automation.endpoint_details_for_handlers = []
    else:
        # Clear if re-running in same session (e.g. for tests or if wizard is looped)
        create_automation.endpoint_details_for_handlers.clear()

    # Process user-defined endpoints
    for endpoint_info in endpoints: # 'endpoints' is the list from user input
        endpoint_data = endpoint_info.copy()
        # Use description for summary, or generate one if description is empty
        endpoint_data["summary"] = endpoint_info["description"] if endpoint_info["description"] else f"{endpoint_info['method']} {endpoint_info['path']}"
        endpoint_data["active"] = True
        
        # Generate specific handler for this endpoint 
        # (User should not define /health here, as it's added automatically later)
        if not endpoint_data["path"].lower().endswith('/health'):
            raw_name_for_function = f"{endpoint_data['method']}_{endpoint_data['path']}"
            handler_function_name = sanitize_for_python_identifier(raw_name_for_function)
            
            # Define the handler path for the automation configuration
            # All handlers will now be in a single 'handlers.py' file
            handler_path = f"src.interfaces.api.routers.{name}.handlers.{handler_function_name}"
            endpoint_data["handler_path"] = handler_path
            
            # Store details for generating this function in handlers.py
            create_automation.endpoint_details_for_handlers.append({
                "method": endpoint_data['method'],
                "path": endpoint_data['path'],
                "function_name": handler_function_name,
                "description": endpoint_info['description'] # Original description for the handler docstring
            })
        
        automation["endpoints"].append(endpoint_data)
        
    # Add health check endpoint for this automation
    health_endpoint = {
        "id": str(uuid.uuid4()),
        "path": "/health",
        "method": "GET",
        "description": f"Health check endpoint for {name} automation",
        "summary": "Health Status",
        "active": True
    }
    automation["endpoints"].append(health_endpoint)
    
    # Step 3: Create the file structure
    print_header("Creating File Structure")
    
    # Create directories for the automation
    router_dir = os.path.join("src", "interfaces", "api", "routers", name)
    if not os.path.exists(router_dir):
        os.makedirs(router_dir, exist_ok=True)
        print_success(f"Created router directory: {router_dir}")
    
    # Create __init__.py in the router directory
    with open(os.path.join(router_dir, "__init__.py"), "w") as f:
        content = '"""\nRouter for ' + display_name + ' automation.\n"""\n\nfrom .router import router\n'
        f.write(content)
    print_success(f"Created {router_dir}/__init__.py")
    
    # Create router.py using template
    with open(os.path.join(TEMPLATE_DIR, "router_template.py"), "r") as template_file:
        router_template = template_file.read()
    
    # Create a safe version of the name for Python identifiers (replace dashes with underscores)
    name_safe = name.replace("-", "_")
    
    # Get the path from the first endpoint or use a default based on name
    if endpoints and endpoints[0]["path"]:
        # Use the custom path from the first endpoint but remove the leading slash if present
        custom_path = endpoints[0]["path"]
        if custom_path.startswith('/'):
            custom_path = custom_path[1:]
    else:
        # Create a proper URL path (plural form without double pluralization)
        # Check if name already ends with 's' to avoid double pluralization (e.g. "market-shares" -> "market-shares" not "market-sharess")
        if name.endswith('s'):
            custom_path = name
        else:
            custom_path = f"{name}s"
    
    # Replace template variables
    router_code = router_template.replace("$name$", name)
    router_code = router_code.replace("$name_safe$", name_safe)
    router_code = router_code.replace("$id$", "item_id")
    router_code = router_code.replace("$custom_path$", custom_path)
    
    # Write router code
    with open(os.path.join(router_dir, "router.py"), "w") as f:
        content = '"""\nRouter implementation for ' + display_name + ' automation.\n"""\n\n' + router_code
        f.write(content)
    print_success(f"Created {router_dir}/router.py")

    # --- Generate handlers.py ---
    all_handler_functions_code = []
    common_imports_for_handlers = [
        "from datetime import datetime",
        "from typing import Dict, Any, Optional",
        "from fastapi import BackgroundTasks",
        "# Ensure these are correctly typed if you have them defined",
        "# from src.domain.models.automation_config import Automation, Endpoint",
        "\n"  # Extra newline after imports
    ]

    handler_function_template_path = os.path.join(TEMPLATE_DIR, "handler_function_template.py")
    single_function_template_body = "" # Initialize
    try:
        with open(handler_function_template_path, "r") as f_template:
            full_template_content = f_template.read()
            func_def_marker = "async def $function_name$"
            func_def_start_index = full_template_content.find(func_def_marker)
            if func_def_start_index != -1:
                single_function_template_body = full_template_content[func_def_start_index:]
            else:
                print_error(f"Critical error: '{func_def_marker}' not found in {handler_function_template_path}.")
    except FileNotFoundError:
        print_error(f"Template file not found: {handler_function_template_path}. Cannot generate handlers.")

    if single_function_template_body and hasattr(create_automation, "endpoint_details_for_handlers") and create_automation.endpoint_details_for_handlers:
        for detail in create_automation.endpoint_details_for_handlers:
            function_code = single_function_template_body
            function_code = function_code.replace("$function_name$", detail["function_name"])
            function_code = function_code.replace("$http_method$", detail["method"])
            function_code = function_code.replace("$endpoint_path$", detail["path"])
            all_handler_functions_code.append(function_code)

        if all_handler_functions_code:
            handlers_file_path = os.path.join(router_dir, "handlers.py")
            final_handlers_py_content = "\n".join(common_imports_for_handlers) + "\n\n" + "\n\n".join(all_handler_functions_code)
            with open(handlers_file_path, "w") as f_handlers:
                f_handlers.write(final_handlers_py_content)
            print_success(f"Created {handlers_file_path} with {len(all_handler_functions_code)} handlers.")
    else:
        if not single_function_template_body:
            print_warning("Handler function template was empty or not processed correctly. No handlers generated.")
        elif not hasattr(create_automation, "endpoint_details_for_handlers") or not create_automation.endpoint_details_for_handlers:
            print("No user-defined endpoints to generate handlers for. Skipping handlers.py creation.") # Using standard print
    # --- End Generate handlers.py ---
    
    # Step 4: Save the automation to storage
    print_header("Saving Automation")
    
    # Create storage directory if it doesn't exist
    storage_dir = os.path.join("data", "automations")
    os.makedirs(storage_dir, exist_ok=True)
    
    # Save automation as JSON file
    automation_file = os.path.join(storage_dir, f"{automation_id}.json")
    with open(automation_file, "w") as f:
        json.dump(automation, f, indent=2)
    
    print_success(f"Saved automation '{name}' to {automation_file}")
    
    # Create blob storage version (for both local and Vercel environments)
    blob_dir = os.path.join("data", "blobs", "automations")
    try:
        # Ensure the blob directory exists
        os.makedirs(blob_dir, exist_ok=True)
        
        # Save to local blob storage
        blob_file = os.path.join(blob_dir, f"{name}.json")
        with open(blob_file, "w") as f:
            json.dump(automation, f, indent=2)
            
        print_success(f"Saved automation to blob storage: {blob_file}")
        
        # If BLOB_READ_WRITE_TOKEN is set, inform user that the file will be available in Vercel Blob Storage
        # when deployed to Vercel
        if os.environ.get('BLOB_READ_WRITE_TOKEN'):
            print_success("Vercel Blob Storage token detected - will use Vercel Blob Storage when deployed")
    except Exception as e:
        print_warning(f"Could not save to blob storage: {e}")
    
    # Save OpenAPI schema
    try:
        # Create basic OpenAPI schema for the automation
        openapi_dir = os.path.join("data", "openapi")
        os.makedirs(openapi_dir, exist_ok=True)
        
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{display_name} API",
                "description": description,
                "version": "1.0.0"
            },
            "paths": {}
        }
        
        # Add paths for each endpoint
        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in openapi_schema["paths"]:
                openapi_schema["paths"][path] = {}
                
            openapi_schema["paths"][path][method] = {
                "summary": endpoint["description"],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {}
                        }
                    }
                }
            }
        
        # Save OpenAPI schema
        openapi_file = os.path.join(openapi_dir, f"{name}.json")
        with open(openapi_file, "w") as f:
            json.dump(openapi_schema, f, indent=2)
            
        # Also save to blob storage (for both local and Vercel environments)
        blob_openapi_dir = os.path.join("data", "blobs", "openapi")
        os.makedirs(blob_openapi_dir, exist_ok=True)
        blob_openapi_file = os.path.join(blob_openapi_dir, f"{name}.json")
        with open(blob_openapi_file, "w") as f:
            json.dump(openapi_schema, f, indent=2)
            
        print_success(f"Created OpenAPI schema: {openapi_file}")
    except Exception as e:
        print_warning(f"Could not create OpenAPI schema: {e}")
    
    # Step 5: Create test files
    print_success(f"Created {router_dir}/router.py")
    
    # Now create handler files if any were defined
    if hasattr(create_automation, "handlers_to_create") and create_automation.handlers_to_create:
        for handler_info in create_automation.handlers_to_create:
            try:
                handler_name = handler_info["name"]
                path_part = handler_info["path_part"]
                handler_filename = handler_info["handler_filename"]
                handler_function_name = handler_info["handler_function_name"]
                
                # Create the handler file
                with open(os.path.join(TEMPLATE_DIR, "handler_template.py"), "r") as template_file:
                    handler_template = template_file.read()
                
                # Replace template variables
                handler_code = handler_template.replace("$endpoint_name$", path_part)
                handler_code = handler_code.replace("$handler_function_name$", handler_function_name)
                handler_code = handler_code.replace("$automation_name$", name)
                
                # Write the handler file
                handler_path = os.path.join(router_dir, handler_filename)
                with open(handler_path, "w") as f:
                    f.write(handler_code)
                print_success(f"Created {handler_path}")
            except Exception as e:
                print_error(f"Error creating handler file: {str(e)}")
    
    # Step 5: Create test files
    print_header("Creating Test Files")
    
    # Create test directory if it doesn't exist
    test_dir = os.path.join("tests", "interfaces", "api", "routers", name)
    os.makedirs(test_dir, exist_ok=True)
    
    # Create __init__.py in test directory
    with open(os.path.join(test_dir, "__init__.py"), "w") as f:
        f.write('"""\nTests for ' + display_name + ' automation.\n"""\n')
    print_success(f"Created {test_dir}/__init__.py")
    
    # Create test file using template
    with open(os.path.join(TEMPLATE_DIR, "test_template.py"), "r") as template_file:
        test_template = template_file.read()
    
    # Replace template variables
    test_code = test_template.replace("$name$", name)
    test_code = test_code.replace("$name_safe$", name_safe)
    test_code = test_code.replace("$custom_path$", custom_path)
    
    # Write test file
    test_file = os.path.join(test_dir, f"test_{name}_router.py")
    with open(test_file, "w") as f:
        f.write(test_code)
    print_success(f"Created {test_file}")
    
    # Step 6: Final summary
    print_header("Summary")
    print(f"Successfully created automation '{display_name}'!")
    print(f"\nRoutes:")
    for endpoint in endpoints:
        print(f"  {endpoint['method']} {endpoint['path']} - {endpoint['description']}")
    
    print(f"\nFiles created:")
    print(f"  {router_dir}/__init__.py")
    print(f"  {router_dir}/router.py")
    print(f"  {test_file}")
    print(f"  {automation_file}")
    
    print(f"\nNext steps:")
    print(f"  1. Update the router implementation in {router_dir}/router.py")
    print(f"  2. Restart your FastAPI server to apply changes")
    print(f"  3. Test your endpoints at http://localhost:8000/docs")
    print(f"  4. Check the API health status at http://localhost:8000/health")
    
    return automation

# Main execution
if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs(os.path.join("src", "interfaces", "api", "routers"), exist_ok=True)
    os.makedirs(os.path.join("data", "automations"), exist_ok=True)
    os.makedirs(os.path.join("data", "blobs", "automations"), exist_ok=True)
    os.makedirs(os.path.join("data", "openapi"), exist_ok=True)
    
    # Run the automation creation wizard
    try:
        asyncio.run(create_automation())
        print("\nAutomation creation completed successfully!")
    except KeyboardInterrupt:
        print("\n\nAutomation creation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error creating automation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Create the template directory if it doesn't exist
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
