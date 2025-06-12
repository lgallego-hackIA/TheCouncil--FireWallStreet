#!/usr/bin/env python3
"""
Wizard for creating new automations in theCouncil, supporting both interactive and non-interactive modes.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
import uuid
import re
import textwrap
import argparse

# --- Constants and Setup ---
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

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

# --- Helper Functions ---
def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")

def get_input(prompt, default=None, validator=None):
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
    return bool(re.match(r'^[a-zA-Z0-9-]+$', name))

def validate_path(path):
    return path.startswith('/') and re.match(r'^[a-zA-Z0-9/_{}-]+$', path)

def validate_method(method):
    return method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

def sanitize_for_python_identifier(text: str) -> str:
    s = re.sub(r'[^0-9a-zA-Z_]', '_', text).strip('_')
    s = re.sub(r'_+', '_', s)
    if s and s[0].isdigit():
        s = '_' + s
    return f"handle_{s.lower()}" if s else "handle_generic_endpoint"

def validate_yes_no(value):
    return value.lower() in ['y', 'n', 'yes', 'no']

def get_yes_no(prompt, default="y"):
    value = get_input(prompt, default, validate_yes_no)
    return value.lower() in ['y', 'yes']

def validate_not_empty(value):
    return bool(value.strip())

# --- Core Logic ---
def process_and_generate_files(name, display_name, description, endpoints):
    print_header("Processing Automation Details")
    automation_id = str(uuid.uuid4())
    name_safe = name.replace("-", "_")
    automation = {
        "id": automation_id,
        "name": name,
        "display_name": display_name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "version": "1.0.0",
        "base_path": f"/{name}",
        "endpoints": [],
        "db_config": {
            "type": "mongodb",
            "config": {
                "connection_string": os.getenv("DATABASE_URL", "mongodb://localhost:27017/council_db"),
                "database": "council_db",
                "collection": f"{name_safe}_collection"
            }
        },
    }

    endpoint_details_for_handlers = []
    for endpoint_info in endpoints:
        endpoint_data = endpoint_info.copy()
        endpoint_data["id"] = str(uuid.uuid4())
        endpoint_data["summary"] = endpoint_info.get("description", f"{endpoint_info['method']} {endpoint_info['path']}")
        endpoint_data["active"] = True

        raw_name = f"{endpoint_data['method']}_{endpoint_data['path']}"
        handler_function_name = sanitize_for_python_identifier(raw_name)
        endpoint_data["handler_path"] = f"src.interfaces.api.routers.{name_safe}.handlers.{handler_function_name}"
        endpoint_info['function_name'] = handler_function_name
        endpoint_details_for_handlers.append(endpoint_info)

        automation["endpoints"].append(endpoint_data)

    print_header("Creating File Structure")
    router_dir = os.path.join("src", "interfaces", "api", "routers", name_safe)
    os.makedirs(router_dir, exist_ok=True)
    print_success(f"Created directory: {router_dir}")

    # Generate router.py, __init__.py, handlers.py, and test files
    generate_router_files(router_dir, name, name_safe, display_name)
    generate_handlers_file(router_dir, endpoint_details_for_handlers)
    generate_test_files(name, name_safe, automation["endpoints"])

    print_header("Saving Automation")
    save_automation_json(automation)
    print_success(f"Automation '{name}' created successfully.")
    print_warning("Remember to restart the server to apply changes.")

def generate_router_files(router_dir, name, name_safe, display_name):
    # Create __init__.py
    with open(os.path.join(router_dir, "__init__.py"), "w") as f:
        f.write(f'"""Router for {display_name} automation."""\n')
    print_success(f"Created {os.path.join(router_dir, '__init__.py')}")

    # Create router.py from template
    try:
        with open(os.path.join(TEMPLATE_DIR, "router_template.py"), "r") as f:
            router_template = f.read()
        router_code = router_template.replace("$name$", name).replace("$name_safe$", name_safe)
        with open(os.path.join(router_dir, "router.py"), "w") as f:
            f.write(router_code)
        print_success(f"Created {os.path.join(router_dir, 'router.py')}")
    except FileNotFoundError:
        print_error(f"Template file not found: {os.path.join(TEMPLATE_DIR, 'router_template.py')}")

def generate_handlers_file(router_dir, details):
    if not details:
        print_warning("No user-defined endpoints provided; skipping handlers.py generation.")
        # Still create an empty handlers.py file
        with open(os.path.join(router_dir, "handlers.py"), "w") as f:
            f.write("# No handlers defined for this automation yet.\n")
        print_success(f"Created empty {os.path.join(router_dir, 'handlers.py')}")
        return

    try:
        with open(os.path.join(TEMPLATE_DIR, "handler_function_template.py"), "r") as f:
            handler_template = f.read()
    except FileNotFoundError:
        print_error(f"Template file not found: {os.path.join(TEMPLATE_DIR, 'handler_function_template.py')}")
        return

    all_handlers_code = []
    common_imports = [
        "from typing import Dict, Any, Optional",
        "from datetime import datetime",
        "from fastapi import BackgroundTasks",
        "# from src.domain.automation.models import Automation, Endpoint # Uncomment if needed",
        "\n"
    ]

    path_param_regex = re.compile(r"{([^}]+)}")

    for detail in details:
        path_params = path_param_regex.findall(detail['path'])
        path_params_signature_str = "".join([f"{param_name}: str, " for param_name in path_params])

        temp_code = handler_template.replace("$function_name$", detail['function_name'])
        temp_code = temp_code.replace("$path_params_signature$", path_params_signature_str)
        temp_code = temp_code.replace("$http_method$", detail['method'])
        temp_code = temp_code.replace("$endpoint_path$", detail['path'])
        temp_code = temp_code.replace("$body_handling_code$", "    pass  # Add body handling logic here")
        temp_code = temp_code.replace("$path_param_handling_code$", "    pass  # Add path param logic here")
        temp_code = temp_code.replace("$body_in_response$", "")
        all_handlers_code.append(temp_code)

    final_content = "\n".join(common_imports) + "\n\n" + "\n\n".join(all_handlers_code)
    with open(os.path.join(router_dir, "handlers.py"), "w") as f:
        f.write(final_content)
    print_success(f"Created {os.path.join(router_dir, 'handlers.py')}")

def generate_test_files(name, name_safe, endpoints):
    test_dir = os.path.join("tests", "interfaces", "api", "routers", name_safe)
    os.makedirs(test_dir, exist_ok=True)
    print_success(f"Created test directory: {test_dir}")

    with open(os.path.join(test_dir, "__init__.py"), "w") as f:
        f.write("")

    try:
        with open(os.path.join(TEMPLATE_DIR, "test_function_template.py"), "r") as f:
            test_template = f.read()
    except FileNotFoundError:
        print_error("Test template not found.")
        return

    all_tests_code = ["import pytest", "from fastapi.testclient import TestClient", "from src.main import app", "\n"]
    for endpoint in endpoints:
        # Sanitize path for test function name, which will be appended to 'test_'
        sanitized_path = endpoint['path'].replace('/', '_').replace('{', '').replace('}', '').strip('_')
        func_name_suffix = f"{endpoint['method'].lower()}_{sanitized_path}"
        
        # Use a placeholder for path parameters in the URL
        url_for_test = re.sub(r'{([^}]+)}', r'test_\g<1>_value', endpoint['path'])
        full_url = f"/{name}{url_for_test}"
        
        test_code = (test_template
                     .replace("$function_name$", func_name_suffix)
                     .replace("$full_url$", full_url)
                     .replace("$http_method_lower$", endpoint['method'].lower())
                     .replace("$http_method$", endpoint['method'].upper())
                     .replace("$endpoint_path$", endpoint['path']))
        all_tests_code.append(test_code)

    # Manually add health check test since it's auto-generated by RouterManager
    health_check_endpoint = {"path": "/health", "method": "GET"}
    sanitized_path = health_check_endpoint['path'].replace('/', '_').strip('_')
    func_name_suffix = f"{health_check_endpoint['method'].lower()}_{sanitized_path}"
    full_url = f"/{name}{health_check_endpoint['path']}"
    
    health_test_code = (test_template
                 .replace("$function_name$", func_name_suffix)
                 .replace("$full_url$", full_url)
                 .replace("$http_method_lower$", health_check_endpoint['method'].lower())
                 .replace("$http_method$", health_check_endpoint['method'].upper())
                 .replace("$endpoint_path$", health_check_endpoint['path']))
    all_tests_code.append(health_test_code)

    with open(os.path.join(test_dir, f"test_{name_safe}_router.py"), "w") as f:
        f.write("\n\n".join(all_tests_code))
    print_success(f"Created test file: {os.path.join(test_dir, f'test_{name_safe}_router.py')}")

def save_automation_json(automation):
    storage_dir = os.path.join("data", "automations")
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, f"{automation['id']}.json")
    with open(file_path, "w") as f:
        json.dump(automation, f, indent=2)
    print_success(f"Saved automation config to {file_path}")
    
    blob_dir = os.path.join("data", "blobs", "automations")
    os.makedirs(blob_dir, exist_ok=True)
    blob_file_path = os.path.join(blob_dir, f"{automation['name']}.json")
    with open(blob_file_path, "w") as f:
        json.dump(automation, f, indent=2)
    print_success(f"Saved blob mock at {blob_file_path}")

async def run_interactive_wizard():
    print_header("theCouncil Automation Creation Wizard")
    name = get_input("Automation name (alphanumeric and dashes)", validator=validate_name)
    display_name = get_input("Display name", default=name.title())
    description = get_input("Description", validator=validate_not_empty)
    
    endpoints = []
    print_header("Endpoints")
    while True:
        path = get_input("Path", validator=validate_path)
        method = get_input("HTTP Method", default="GET", validator=validate_method).upper()
        endpoint_description = get_input("Endpoint description")
        endpoints.append({"path": path, "method": method, "description": endpoint_description})
        if not get_yes_no("Add another endpoint?", default="n"):
            break
    process_and_generate_files(name, display_name, description, endpoints)

def run_non_interactive(args):
    print_header("Creating Automation (Non-Interactive)")
    try:
        endpoints = json.loads(args.endpoints)
    except json.JSONDecodeError:
        print_error("Invalid JSON format for --endpoints argument.")
        sys.exit(1)
    process_and_generate_files(args.name, args.display_name or args.name.title(), args.description, endpoints)

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Create a new theCouncil automation.")
    parser.add_argument('--interactive', action='store_true', help='Run in interactive wizard mode.')
    parser.add_argument('--config-file', type=str, help='Path to a JSON file defining the automation.')
    parser.add_argument('--name', type=str, help='Name of the automation (e.g., "logistics"). Used if --config-file is not provided.')
    parser.add_argument('--display-name', type=str, help='Display name (e.g., "Logistics"). Used if --config-file is not provided or if not in config.')
    parser.add_argument('--description', type=str, help='A description for the automation. Used if --config-file is not provided.')
    parser.add_argument('--endpoints', type=str, help='JSON string of endpoints. Ex: \'[{"path": "/items", "method": "GET"}]\'. Used if --config-file is not provided.')

    args = parser.parse_args()

    if args.config_file:
        print_header("Creating Automation (from Config File)")
        try:
            with open(args.config_file, 'r') as f:
                config_data = json.load(f)
            
            name = config_data.get('name')
            display_name = config_data.get('display_name', name.title() if name else "Untitled Automation")
            description = config_data.get('description')
            endpoints = config_data.get('endpoints')

            if not all([name, description, endpoints is not None]): # endpoints can be an empty list
                print_error("Config file must contain 'name', 'description', and 'endpoints' (can be empty list).")
                sys.exit(1)
            
            process_and_generate_files(name, display_name, description, endpoints)

        except FileNotFoundError:
            print_error(f"Config file not found: {args.config_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print_error(f"Invalid JSON format in config file: {args.config_file}")
            sys.exit(1)
        except Exception as e:
            print_error(f"An unexpected error occurred while processing the config file: {e}")
            sys.exit(1)
    elif args.interactive or len(sys.argv) == 1:
        asyncio.run(run_interactive_wizard())
    else:
        # This is for non-interactive mode using direct CLI arguments
        if not all([args.name, args.description, args.endpoints]):
            print_error("For non-interactive mode (without --config-file or --interactive), --name, --description, and --endpoints are required.")
            parser.print_help()
            sys.exit(1)
        run_non_interactive(args) # This function parses args.endpoints and calls process_and_generate_files

if __name__ == "__main__":
    main()
