"""
Redis repository implementation.
"""
import json
import logging
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import redis.asyncio as redis

from src.infrastructure.database.base_repository import BaseRepository

T = TypeVar('T')  # Type of domain entity

logger = logging.getLogger(__name__)


class RedisRepository(BaseRepository[T], Generic[T]):
    """
    Redis repository implementation.
    """

    def __init__(self, redis_client: redis.Redis, entity_type: Type[T], namespace: str = None):
        """
        Initialize the Redis repository.
        
        Args:
            redis_client: Redis client
            entity_type: Domain entity type
            namespace: Namespace for Redis keys (defaults to entity_type name in lowercase)
        """
        self.redis = redis_client
        self.entity_type = entity_type
        self.namespace = namespace or entity_type.__name__.lower()
    
    def _get_key(self, entity_id: str) -> str:
        """Get the full Redis key for an entity."""
        return f"{self.namespace}:{entity_id}"
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity in Redis.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID
        """
        try:
            # Convert entity to dictionary
            entity_dict = self._entity_to_dict(entity)
            
            # Generate ID if not present
            entity_id = entity_dict.get('id')
            if not entity_id:
                entity_id = str(uuid.uuid4())
                entity_dict['id'] = entity_id
                if hasattr(entity, 'id'):
                    setattr(entity, 'id', entity_id)
            
            # Store in Redis
            key = self._get_key(entity_id)
            entity_json = json.dumps(entity_dict)
            await self.redis.set(key, entity_json)
            
            # Add to index set
            await self.redis.sadd(f"{self.namespace}:all", entity_id)
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity by ID from Redis.
        
        Args:
            entity_id: ID of the entity to get
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            key = self._get_key(str(entity_id))
            entity_json = await self.redis.get(key)
            
            if entity_json is None:
                return None
            
            # Decode and convert to entity
            entity_dict = json.loads(entity_json)
            return self._dict_to_entity(entity_dict)
            
        except Exception as e:
            logger.error(f"Error getting entity {self.entity_type.__name__} by ID {entity_id}: {e}")
            raise
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination from Redis.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        try:
            # Get all entity IDs from the index set
            all_ids = await self.redis.smembers(f"{self.namespace}:all")
            
            # Apply pagination (Redis doesn't have built-in pagination for sets)
            paginated_ids = list(all_ids)[offset:offset + limit]
            
            entities = []
            for entity_id in paginated_ids:
                entity = await self.get_by_id(entity_id)
                if entity:
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error getting all entities {self.entity_type.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an entity in Redis.
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity if successful, None otherwise
        """
        try:
            # Convert entity to dictionary
            entity_dict = self._entity_to_dict(entity)
            
            # Get ID
            entity_id = entity_dict.get('id')
            if not entity_id:
                logger.error(f"Cannot update entity {self.entity_type.__name__} without ID")
                return None
            
            # Check if the entity exists
            key = self._get_key(entity_id)
            exists = await self.redis.exists(key)
            
            if not exists:
                return None
            
            # Update in Redis
            entity_json = json.dumps(entity_dict)
            await self.redis.set(key, entity_json)
            
            return entity
            
        except Exception as e:
            logger.error(f"Error updating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity from Redis.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            entity_id_str = str(entity_id)
            key = self._get_key(entity_id_str)
            
            # Check if the entity exists
            exists = await self.redis.exists(key)
            if not exists:
                return False
            
            # Delete the entity
            await self.redis.delete(key)
            
            # Remove from index set
            await self.redis.srem(f"{self.namespace}:all", entity_id_str)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entity {self.entity_type.__name__} with ID {entity_id}: {e}")
            raise
    
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if an entity exists in Redis.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        try:
            key = self._get_key(str(entity_id))
            return await self.redis.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Error checking if entity {self.entity_type.__name__} exists with ID {entity_id}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters in Redis.
        
        Note: Redis doesn't support complex filtering, so for filtered counts,
        we need to retrieve all entities and filter them in memory.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching the filters
        """
        try:
            if not filters:
                # If no filters, just return the count of all entities
                return await self.redis.scard(f"{self.namespace}:all")
            
            # For filtered count, need to retrieve and filter in memory
            all_entities = await self.get_all(limit=10000)  # Limit to avoid memory issues
            
            # Apply filters
            filtered_entities = all_entities
            for field, value in filters.items():
                filtered_entities = [
                    e for e in filtered_entities
                    if hasattr(e, field) and getattr(e, field) == value
                ]
            
            return len(filtered_entities)
            
        except Exception as e:
            logger.error(f"Error counting entities {self.entity_type.__name__}: {e}")
            raise
    
    async def find(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find entities matching the given filters in Redis.
        
        Note: Redis doesn't support complex filtering, so we need to retrieve
        all entities and filter them in memory.
        
        Args:
            filters: Filters to apply
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the filters
        """
        try:
            # Retrieve all entities (Redis doesn't have built-in filtering)
            all_entities = await self.get_all(limit=10000)  # Limit to avoid memory issues
            
            # Apply filters
            filtered_entities = all_entities
            for field, value in filters.items():
                filtered_entities = [
                    e for e in filtered_entities
                    if hasattr(e, field) and getattr(e, field) == value
                ]
            
            # Apply pagination
            return filtered_entities[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error finding entities {self.entity_type.__name__}: {e}")
            raise
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary representation for Redis."""
        if hasattr(entity, 'dict'):
            # For Pydantic models
            return entity.dict()
        elif hasattr(entity, '__dict__'):
            # For standard classes
            # Filter out private attributes
            return {k: v for k, v in entity.__dict__.items() if not k.startswith('_')}
        else:
            # For dictionaries or other mappings
            return dict(entity)
    
    def _dict_to_entity(self, entity_dict: Dict[str, Any]) -> T:
        """Convert dictionary to entity."""
        # Use Pydantic model if the entity type is one
        if hasattr(self.entity_type, 'parse_obj'):
            return self.entity_type.parse_obj(entity_dict)
        elif hasattr(self.entity_type, 'from_dict'):
            return self.entity_type.from_dict(entity_dict)
        else:
            # For standard classes, use constructor
            return self.entity_type(**entity_dict)
