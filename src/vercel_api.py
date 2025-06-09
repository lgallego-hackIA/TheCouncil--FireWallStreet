"""
Vercel API entrypoint for theCouncil project.
This module adapts the FastAPI application to run on Vercel's serverless environment.
"""
import sys
import os

# Add project root to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastAPI app from main.py
from src.main import app

# This is necessary for Vercel serverless function to work
# Vercel expects a variable named 'app' as the entrypoint
app = app
