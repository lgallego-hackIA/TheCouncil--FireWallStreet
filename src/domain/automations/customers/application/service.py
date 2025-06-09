"""
Application services for customers automation.
"""
from typing import List, Optional, Dict, Any
from ..domain.models import CustomersItem
from ..domain.service import CustomersService
from ..infrastructure.repository import CustomersRepository

class CustomersApplicationService:
    """Application service for customers."""
    
    def __init__(self, repository: CustomersRepository = None, domain_service: CustomersService = None):
        """Initialize the application service."""
        self.repository = repository or CustomersRepository()
        self.domain_service = domain_service or CustomersService()
    
    async def create_item(self, data: Dict[str, Any]) -> CustomersItem:
        """
        Create a new item.
        
        Args:
            data: Item data
            
        Returns:
            Created item
        """
        # Create domain entity
        item = CustomersItem(**data)
        
        # Apply domain logic
        item = await self.domain_service.process_item(item)
        
        # Save to repository
        return await self.repository.create(item)
    
    async def get_by_id(self, item_id: str) -> Optional[CustomersItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            Item if found, None otherwise
        """
        return await self.repository.get_by_id(item_id)
    
    async def get_all(self) -> List[CustomersItem]:
        """
        Get all items.
        
        Returns:
            List of items
        """
        return await self.repository.get_all()
