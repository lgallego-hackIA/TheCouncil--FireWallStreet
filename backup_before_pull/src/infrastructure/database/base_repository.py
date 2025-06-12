"""
Base repository interface for database adapters.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

T = TypeVar('T')  # Type of entity


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository interface for database operations.
    
    All database-specific repositories should implement this interface.
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity to get
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        pass
        
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching the filters
        """
        pass
    
    @abstractmethod
    async def find(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find entities matching the given filters.
        
        Args:
            filters: Filters to apply
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the filters
        """
        pass
