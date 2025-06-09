"""
Application services for inventory automation.
"""
from typing import List, Optional, Dict, Any
from ..domain.models import InventoryItem
from ..domain.service import InventoryService
from ..infrastructure.repository import InventoryRepository

class InventoryApplicationService:
    """Application service for inventory."""
    
    def __init__(self, repository: InventoryRepository = None, domain_service: InventoryService = None):
        """Initialize the application service."""
        self.repository = repository or InventoryRepository()
        self.domain_service = domain_service or InventoryService()
    
    async def create_item(self, data: Dict[str, Any]) -> InventoryItem:
        """
        Create a new item.
        
        Args:
            data: Item data
            
        Returns:
            Created item
        """
        # Create domain entity
        item = InventoryItem(**data)
        
        # Apply domain logic
        item = await self.domain_service.process_item(item)
        
        # Save to repository
        return await self.repository.create(item)
    
    async def get_by_id(self, item_id: str) -> Optional[InventoryItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            Item if found, None otherwise
        """
        return await self.repository.get_by_id(item_id)
    
    async def get_all(self) -> List[InventoryItem]:
        """
        Get all items.
        
        Returns:
            List of items
        """
        return await self.repository.get_all()
