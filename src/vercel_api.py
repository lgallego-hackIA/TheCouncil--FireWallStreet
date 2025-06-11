"""
Vercel API entrypoint for theCouncil project.
This module adapts the FastAPI application to run on Vercel's serverless environment.
"""
import sys
import os
import logging

# Mark environment as serverless
os.environ['VERCEL'] = '1'

# Add project root to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# It's crucial to set up logging BEFORE importing any other application modules
# to ensure that loggers are configured correctly from the start.
from src.shared.logging import setup_logging
setup_logging()

# Now, import the rest of the components
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.application.automation_registry.registry import AutomationRegistry
from src.application.automation_manager import AutomationManager
from src.interfaces.console.router import router as console_router
from src.shared.exceptions import TheCouncilError
from src.shared.config import get_settings


logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Create global instances
automation_registry = AutomationRegistry()
automation_manager = None

# Create FastAPI application
app = FastAPI(
    title="theCouncil API",
    description="Dynamic API system for GPT integration",
    version="0.1.0",
    debug=settings.DEBUG
)
logger.error("--- VERCEL_API: FastAPI app object CREATED (using on_event strategy) ---")

@app.on_event("startup")
async def startup_event():
    logger.error("--- VERCEL_API: ON_EVENT STARTUP FUNCTION STARTED ---")
    # Initialize components on startup
    logger.info("Starting theCouncil API (Vercel serverless mode) via on_event")
    
    # Log the directory structure for debugging purposes on Vercel
    try:
        project_root = '/var/task' if os.environ.get('VERCEL') == '1' else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"--- Project Directory Listing from root: {project_root} ---")
        for root, dirs, files in os.walk(project_root):
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            level = root.replace(project_root, '', 1).count(os.sep)
            indent = ' ' * 4 * (level)
            logger.info(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                logger.info(f'{sub_indent}{f}')
        logger.info("--- End Directory Listing ---")
    except Exception as e:
        logger.error(f"Failed to list project directories: {e}")

    global automation_manager
    
    # Create automation manager
    automation_manager = AutomationManager(app, automation_registry)
    
    # Initialize the automation manager
    logger.error("--- VERCEL_API: ATTEMPTING AutomationManager.initialize() (from on_event) ---")
    await automation_manager.initialize()
    
    # Store router_manager in app.state for middleware to access
    if hasattr(automation_manager, 'router_manager'):
        app.state.router_manager = automation_manager.router_manager
        logger.info("Router manager stored in app state for middleware access (from on_event)")
    else:
        logger.error("AutomationManager does not have router_manager attribute after initialization (from on_event).")
    logger.error("--- VERCEL_API: ON_EVENT STARTUP FUNCTION COMPLETED ---")

# --- DIRECT INITIALIZATION TEST BLOCK START ---
# This block is for diagnostic purposes to see if code can run here when on_event isn't firing.
logger.error("--- VERCEL_API: EXECUTING DIRECT INITIALIZATION TEST BLOCK ---")
try:
    # Simplified, synchronous version of startup logic for testing
    logger.info("Direct Init: Starting theCouncil API (Vercel serverless mode)")
    
    # Log the directory structure for debugging purposes on Vercel
    try:
        direct_project_root = '/var/task' if os.environ.get('VERCEL') == '1' else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"Direct Init: --- Project Directory Listing from root: {direct_project_root} ---")
        for r, d, f_list in os.walk(direct_project_root):
            if '__pycache__' in d:
                d.remove('__pycache__')
            lvl = r.replace(direct_project_root, '', 1).count(os.sep)
            ind = ' ' * 4 * (lvl)
            logger.info(f'Direct Init: {ind}{os.path.basename(r)}/')
            sub_ind = ' ' * 4 * (lvl + 1)
            for item_f in f_list:
                logger.info(f'Direct Init: {sub_ind}{item_f}')
        logger.info("Direct Init: --- End Directory Listing ---")
    except Exception as e_dir:
        logger.error(f"Direct Init: Failed to list project directories: {e_dir}")

    # Attempt to create and initialize AutomationManager directly (synchronous parts if possible)
    # Note: AutomationManager.initialize is async, so this is a partial test.
    # We are primarily checking if this code block *executes*.
    if 'app' in locals() and 'automation_registry' in locals():
        logger.info("Direct Init: 'app' and 'automation_registry' are in locals.")
        temp_automation_manager = AutomationManager(app, automation_registry) # app is FastAPI instance
        logger.info("Direct Init: temp_AutomationManager INSTANTIATED.")
        # Cannot easily call await temp_automation_manager.initialize() here directly in sync code.
        # The main goal is to see if this block runs.
        # For a fuller test, one might try asyncio.run(temp_automation_manager.initialize()),
        # but that can conflict with Uvicorn's event loop.
        # We will rely on the @app.on_event("startup") to call the async initialize.
    else:
        logger.error("Direct Init: 'app' or 'automation_registry' not found in locals(). This is unexpected.")

    logger.error("--- VERCEL_API: DIRECT INITIALIZATION TEST BLOCK COMPLETED ---")
except Exception as e_direct_init:
    logger.error(f"--- VERCEL_API: ERROR IN DIRECT INITIALIZATION TEST BLOCK: {e_direct_init} ---", exc_info=True)
# --- DIRECT INITIALIZATION TEST BLOCK END ---

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the console router for automation management
app.include_router(console_router, prefix="/console", tags=["Console"])

# Middleware to handle deleted automations
@app.middleware("http")
async def handle_deleted_automations(request: Request, call_next):
    """Middleware to handle requests to deleted automation endpoints."""
    # Only check API requests, not console or other routes
    if request.url.path.startswith("/api/"):
        # This is a safe way to access router_manager via app.state
        if hasattr(app.state, "router_manager") and \
           app.state.router_manager.is_deleted_automation_path(request.url.path):
            logger.info(f"Caught request to deleted automation path: {request.url.path}")
            return JSONResponse(
                status_code=404,
                content={"detail": "This automation endpoint has been deleted."},
            )
    return await call_next(request)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )

@app.exception_handler(TheCouncilError)
async def thecouncil_exception_handler(request: Request, exc: TheCouncilError):
    """Handle TheCouncilError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "type": exc.error_type},
    )

@app.get("/")
async def get_root():
    """API root endpoint."""
    return {
        "name": "theCouncil API",
        "version": "0.1.0",
        "description": "Dynamic API system for GPT integration",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Central health check endpoint for the entire API.
    
    Returns status information about the API and its components.
    """
    # Get all registered automations from the registry
    automations = []
    if automation_registry and hasattr(automation_registry, 'get_all_automations'):
        try:
            automations = await automation_registry.get_all_automations()
        except Exception as e:
            logger.error(f"Error getting automations: {e}")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "environment": "serverless" if os.environ.get('VERCEL') == '1' else "local",
        "registered_automations": len(automations) if automations else 0,
        "automations": [a.id for a in automations] if automations else []
    }
