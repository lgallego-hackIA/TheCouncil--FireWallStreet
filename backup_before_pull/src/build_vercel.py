"""
Script to build and test Vercel deployment locally.
This is useful for testing the Vercel configuration before pushing to GitHub.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_vercel_cli():
    """Check if Vercel CLI is installed."""
    try:
        subprocess.run(["vercel", "--version"], 
                       check=True, 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def install_vercel_cli():
    """Install Vercel CLI using npm."""
    print("Installing Vercel CLI...")
    try:
        subprocess.run(["npm", "install", "-g", "vercel"], 
                      check=True)
        print("Vercel CLI installed successfully!")
        return True
    except subprocess.SubprocessError:
        print("Failed to install Vercel CLI. Please install it manually with: npm install -g vercel")
        return False

def login_to_vercel():
    """Log in to Vercel."""
    print("Please log in to Vercel:")
    try:
        subprocess.run(["vercel", "login"], check=True)
        return True
    except subprocess.SubprocessError:
        print("Failed to log in to Vercel.")
        return False

def deploy_to_vercel(production=False):
    """Deploy to Vercel."""
    cmd = ["vercel"]
    if production:
        cmd.append("--prod")
    
    print(f"{'Production' if production else 'Development'} deployment to Vercel...")
    try:
        subprocess.run(cmd, check=True)
        print("Deployment successful!")
        return True
    except subprocess.SubprocessError:
        print("Deployment failed.")
        return False

def main():
    """Main entry point."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()
    os.chdir(project_root)
    
    # Check if Vercel CLI is installed
    if not check_vercel_cli():
        if not install_vercel_cli():
            sys.exit(1)
    
    # Check if user is logged in to Vercel
    if not login_to_vercel():
        sys.exit(1)
    
    # Deploy to Vercel
    production = len(sys.argv) > 1 and sys.argv[1] == "--prod"
    if not deploy_to_vercel(production):
        sys.exit(1)

if __name__ == "__main__":
    main()
