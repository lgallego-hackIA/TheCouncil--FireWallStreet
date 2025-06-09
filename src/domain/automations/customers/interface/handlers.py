"""
Request handlers for customers automation endpoints.
"""
from typing import Dict, Any, List
from fastapi import BackgroundTasks
import time
import platform
import psutil
from datetime import datetime

from ..application.service import CustomersApplicationService
from ..domain.models import CustomersItem
from ..infrastructure.repository import CustomersRepository

# Create application service instance
app_service = CustomersApplicationService()

async def get_all_items(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
    """
    Handler for GET /customers endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Response data
    """
    items = await app_service.get_all()
    return {"items": items, "total": len(items)}

async def create_item(params: Dict[str, Any], *args, **kwargs) -> CustomersItem:
    """
    Handler for POST /customers endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Created item
    """
    return await app_service.create_item(params)

async def get_item_by_id(params: Dict[str, Any], *args, **kwargs) -> CustomersItem:
    """
    Handler for GET /customers/{item_id} endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Item data
    """
    item_id = params.get("item_id")
    return await app_service.get_by_id(item_id)

async def health_check(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
    """
    Handler for GET /customers/health endpoint.
    Provides comprehensive health check for the customers automation.
    
    Args:
        params: Request parameters
        
    Returns:
        Health check data
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Health check called with params: {params}")
    
    try:
        start_time = time.time()
    
        # Repository status defaults (in case we can't connect)
        repository_status = "unknown"
        repository_message = "No repository check performed"
        repository_latency = 0
        
        # We'll skip the repository check for now to avoid errors
        # This will be implemented properly once the DB is set up
    
        # System info
        system_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "memory_usage": {
                "percent": psutil.virtual_memory().percent,
                "available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2)
            },
            "cpu_usage": psutil.cpu_percent()
        }
        
        # Service dependencies
        dependencies = {
            "repository": {
                "status": repository_status,
                "message": repository_message,
                "latency_ms": repository_latency
            }
        }
        
        # Overall health status
        overall_status = "healthy" if repository_status == "ok" else "degraded"
        
        response_time = round((time.time() - start_time) * 1000, 2)  # in ms
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "service": "customers-automation",
            "version": "1.0.0",
            "response_time_ms": response_time,
            "dependencies": dependencies,
            "system_info": system_info
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "service": "customers-automation",
            "version": "1.0.0",
            "error": str(e),
            "message": "Error performing health check"
        }