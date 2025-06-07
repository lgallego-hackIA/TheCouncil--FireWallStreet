"""
Application services for orders automation.
"""
from typing import List, Optional, Dict, Any
from ..domain.models import OrdersItem
from ..domain.service import OrdersService
from ..infrastructure.repository import OrdersRepository

class OrdersApplicationService:
    """Application service for orders."""
    
    def __init__(self, repository: OrdersRepository = None, domain_service: OrdersService = None):
        """Initialize the application service."""
        self.repository = repository or OrdersRepository()
        self.domain_service = domain_service or OrdersService()
    
    async def create_item(self, data: Dict[str, Any]) -> OrdersItem:
        """
        Create a new item.
        
        Args:
            data: Item data
            
        Returns:
            Created item
        """
        # Create domain entity
        item = OrdersItem(**data)
        
        # Apply domain logic
        item = await self.domain_service.process_item(item)
        
        # Save to repository
        return await self.repository.create(item)
    
    async def get_by_id(self, item_id: str) -> Optional[OrdersItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            Item if found, None otherwise
        """
        return await self.repository.get_by_id(item_id)
    
    async def get_all(self) -> List[OrdersItem]:
        """
        Get all items.
        
        Returns:
            List of items
        """
        return await self.repository.get_all()
