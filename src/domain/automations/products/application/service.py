"""
Application services for products automation.
"""
from typing import List, Optional, Dict, Any
from ..domain.models import ProductsItem
from ..domain.service import ProductsService
from ..infrastructure.repository import ProductsRepository

class ProductsApplicationService:
    """Application service for products."""
    
    def __init__(self, repository: ProductsRepository = None, domain_service: ProductsService = None):
        """Initialize the application service."""
        self.repository = repository or ProductsRepository()
        self.domain_service = domain_service or ProductsService()
    
    async def create_item(self, data: Dict[str, Any]) -> ProductsItem:
        """
        Create a new item.
        
        Args:
            data: Item data
            
        Returns:
            Created item
        """
        # Create domain entity
        item = ProductsItem(**data)
        
        # Apply domain logic
        item = await self.domain_service.process_item(item)
        
        # Save to repository
        return await self.repository.create(item)
    
    async def get_by_id(self, item_id: str) -> Optional[ProductsItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            Item if found, None otherwise
        """
        return await self.repository.get_by_id(item_id)
    
    async def get_all(self) -> List[ProductsItem]:
        """
        Get all items.
        
        Returns:
            List of items
        """
        return await self.repository.get_all()
