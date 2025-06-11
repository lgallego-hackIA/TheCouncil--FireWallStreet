import sys
import os
import logging
import asyncio # Added for asyncio.Lock

# Mark environment as serverless
os.environ['VERCEL'] = '1'

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.logging import setup_logging
setup_logging()

from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.application.automation_registry.registry import AutomationRegistry
from src.application.automation_manager import AutomationManager
from src.interfaces.console.router import router as console_router
from src.shared.exceptions import TheCouncilError
from src.shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

automation_registry = AutomationRegistry()
automation_manager = None # Will be initialized by our new mechanism

# Global flag and lock for initialization
is_initialized = False
initialization_lock = asyncio.Lock()

app = FastAPI(
    title="theCouncil API",
    description="Dynamic API system for GPT integration",
    version="0.1.0",
    debug=settings.DEBUG
)
logger.info("--- VERCEL_API: FastAPI app object CREATED (using on-first-request init strategy) ---")

async def initialize_app_components():
    """Handles the actual application component initialization."""
    global automation_manager, app, automation_registry, logger, settings, is_initialized
    
    logger.info("--- VERCEL_API: initialize_app_components STARTED ---")
    
    try:
        project_root = '/var/task' if os.environ.get('VERCEL') == '1' else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"--- Project Directory Listing from root: {project_root} ---")
        for r_path, d_list, f_list_items in os.walk(project_root):
            if '__pycache__' in d_list:
                d_list.remove('__pycache__')
            level = r_path.replace(project_root, '', 1).count(os.sep)
            indent = ' ' * 4 * (level)
            logger.info(f'{indent}{os.path.basename(r_path)}/')
            sub_indent = ' ' * 4 * (level + 1)
            #for f_item_name in f_list_items:
             #   logger.info(f'{sub_indent}{f_item_name}')
        logger.info("--- End Directory Listing ---")
    except Exception as e_dir:
        logger.error(f"Failed to list project directories: {e_dir}")

    logger.info("--- VERCEL_API: PREPARING to instantiate AutomationManager ---")
    try:
        automation_manager = AutomationManager(app, automation_registry)
        logger.info("--- VERCEL_API: SUCCESSFULLY instantiated AutomationManager ---")
    except Exception as e_am_init:
        logger.error(f"--- VERCEL_API: FAILED to instantiate AutomationManager: {e_am_init} ---", exc_info=True)
        is_initialized = False # Ensure we don't proceed as if initialized
        return # Stop further initialization if AutomationManager fails
    
    logger.info("--- VERCEL_API: PREPARING to call AutomationManager.initialize() (from initialize_app_components) ---")
    try:
        await automation_manager.initialize()
        logger.info("--- VERCEL_API: SUCCESSFULLY CALLED AutomationManager.initialize() (from initialize_app_components) ---")
    except Exception as e_init:
        logger.error(f"--- VERCEL_API: FAILED during AutomationManager.initialize(): {e_init} ---", exc_info=True)
        # Optionally re-raise or handle as critical failure
        # raise # Uncomment if this should halt further initialization attempts or signal critical failure

    
    if hasattr(automation_manager, 'router_manager'):
        app.state.router_manager = automation_manager.router_manager
        logger.info("Router manager stored in app state (from initialize_app_components)")
    else:
        logger.error("AutomationManager no router_manager attr after init (from initialize_app_components).")
    
    is_initialized = True # Set flag after successful initialization
    logger.info("--- VERCEL_API: initialize_app_components COMPLETED & is_initialized SET ---")

@app.middleware("http")
async def ensure_initialized_middleware(request: Request, call_next):
    global is_initialized, initialization_lock

    if not is_initialized:
        async with initialization_lock:
            if not is_initialized: 
                logger.info("--- VERCEL_API: ensure_initialized_middleware - NOT INITIALIZED, STARTING INIT ---")
                await initialize_app_components()
                # is_initialized is set within initialize_app_components upon success
                logger.info("--- VERCEL_API: ensure_initialized_middleware - INITIALIZATION CALL COMPLETE ---")
            else:
                logger.info("--- VERCEL_API: ensure_initialized_middleware - ALREADY INITIALIZED (after lock) ---")
    
    # Handle deleted automations logic (ensure app.state.router_manager exists)
    if hasattr(app.state, "router_manager") and \
       request.url.path.startswith("/api/") and \
       app.state.router_manager.is_deleted_automation_path(request.url.path):
        logger.info(f"Caught request to deleted automation path: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={"detail": "This automation endpoint has been deleted."},
        )
            
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(console_router, prefix="/console", tags=["Console"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})

@app.exception_handler(TheCouncilError)
async def thecouncil_exception_handler(request: Request, exc: TheCouncilError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc), "type": exc.error_type})

@app.get("/")
async def get_root():
    return {"name": "theCouncil API", "version": "0.1.0", "description": "Dynamic API system", "docs_url": "/docs"}

@app.get("/health")
async def health_check():
    global automation_registry, is_initialized
    automations_data = []
    num_registered = 0
    if is_initialized and automation_registry and hasattr(automation_registry, 'get_all_automations'):
        try:
            automations_list = await automation_registry.get_all_automations()
            automations_data = [a.id for a in automations_list] if automations_list else []
            num_registered = len(automations_data)
        except Exception as e_health:
            logger.error(f"Error getting automations for health check: {e_health}")
    
    return {
        "status": "healthy", "timestamp": datetime.now().isoformat(), "version": "0.1.0",
        "environment": "serverless" if os.environ.get('VERCEL') == '1' else "local",
        "initialized": is_initialized,
        "registered_automations_count": num_registered,
        "automation_ids": automations_data
    }
