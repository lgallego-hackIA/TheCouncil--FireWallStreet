"""
Request handlers for products automation endpoints.
"""
from typing import Dict, Any, List
from fastapi import BackgroundTasks

from ..application.service import ProductsApplicationService
from ..domain.models import ProductsItem

# Create application service instance
app_service = ProductsApplicationService()

async def get_all_items(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
    """
    Handler for GET /products endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Response data
    """
    items = await app_service.get_all()
    return {"items": items, "total": len(items)}

async def create_item(params: Dict[str, Any], *args, **kwargs) -> ProductsItem:
    """
    Handler for POST /products endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Created item
    """
    return await app_service.create_item(params)

async def get_item_by_id(params: Dict[str, Any], *args, **kwargs) -> ProductsItem:
    """
    Handler for GET /products/{item_id} endpoint.
    
    Args:
        params: Request parameters
        
    Returns:
        Item data
    """
    item_id = params.get("item_id")
    return await app_service.get_by_id(item_id)
