#!/usr/bin/env python3
"""
Script to set up local development environment for theCouncil.
This creates a .env file based on .env.example with appropriate local settings.
"""
import os
import shutil
import sys

def setup_local_env():
    """Create a local .env file based on .env.example."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to env files
    env_example_path = os.path.join(project_root, '.env.example')
    env_path = os.path.join(project_root, '.env')
    
    # Check if .env.example exists
    if not os.path.exists(env_example_path):
        print("Error: .env.example file not found.")
        sys.exit(1)
    
    # Check if .env already exists
    if os.path.exists(env_path):
        overwrite = input(".env file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Read the .env.example content
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    # Make modifications for local development
    env_content = env_content.replace('BLOB_READ_WRITE_TOKEN=your_vercel_blob_token_here', 
                                      '# BLOB_READ_WRITE_TOKEN not needed for local development')
    env_content = env_content.replace('# VERCEL=0', 'VERCEL=0')
    
    # Write the .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f".env file created at {env_path}")
    print("Local development environment set up successfully!")
    print()
    print("For Vercel deployment:")
    print("1. Get a BLOB_READ_WRITE_TOKEN from the Vercel dashboard")
    print("2. Add it to your Vercel environment variables")
    print("3. Deploy your application to Vercel")

if __name__ == "__main__":
    setup_local_env()
