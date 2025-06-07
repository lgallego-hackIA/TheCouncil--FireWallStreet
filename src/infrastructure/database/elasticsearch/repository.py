"""
Elasticsearch repository implementation.
"""
import json
import logging
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from elasticsearch import AsyncElasticsearch, NotFoundError

from src.infrastructure.database.base_repository import BaseRepository

T = TypeVar('T')  # Type of domain entity

logger = logging.getLogger(__name__)


class ElasticsearchRepository(BaseRepository[T], Generic[T]):
    """
    Elasticsearch repository implementation.
    """

    def __init__(
        self,
        client: AsyncElasticsearch,
        entity_type: Type[T],
        index_name: str = None,
        refresh: str = "false"
    ):
        """
        Initialize the Elasticsearch repository.
        
        Args:
            client: Elasticsearch client
            entity_type: Domain entity type
            index_name: Name of the index (defaults to entity_type name in lowercase)
            refresh: Refresh policy for write operations ('true', 'false', or 'wait_for')
        """
        self.client = client
        self.entity_type = entity_type
        self.index_name = index_name or entity_type.__name__.lower()
        self.refresh = refresh
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity in Elasticsearch.
        
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
            
            # Index the document
            response = await self.client.index(
                index=self.index_name,
                id=entity_id,
                document=entity_dict,
                refresh=self.refresh
            )
            
            # Ensure the ID is set correctly
            if hasattr(entity, 'id') and not getattr(entity, 'id', None):
                setattr(entity, 'id', response['_id'])
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity by ID from Elasticsearch.
        
        Args:
            entity_id: ID of the entity to get
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            try:
                response = await self.client.get(
                    index=self.index_name,
                    id=str(entity_id)
                )
                
                # Extract the source document
                entity_dict = response['_source']
                
                # Ensure the ID is included
                if 'id' not in entity_dict:
                    entity_dict['id'] = response['_id']
                
                return self._dict_to_entity(entity_dict)
                
            except NotFoundError:
                return None
                
        except Exception as e:
            if not isinstance(e, NotFoundError):  # Don't log not found as error
                logger.error(f"Error getting entity {self.entity_type.__name__} by ID {entity_id}: {e}")
            return None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination from Elasticsearch.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        try:
            response = await self.client.search(
                index=self.index_name,
                body={
                    "query": {"match_all": {}},
                    "from": offset,
                    "size": limit
                }
            )
            
            hits = response.get('hits', {}).get('hits', [])
            
            entities = []
            for hit in hits:
                entity_dict = hit['_source']
                
                # Ensure the ID is included
                if 'id' not in entity_dict:
                    entity_dict['id'] = hit['_id']
                
                entity = self._dict_to_entity(entity_dict)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error getting all entities {self.entity_type.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an entity in Elasticsearch.
        
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
            exists = await self.exists(entity_id)
            
            if not exists:
                return None
            
            # Update the document
            await self.client.index(
                index=self.index_name,
                id=str(entity_id),
                document=entity_dict,
                refresh=self.refresh
            )
            
            return entity
            
        except Exception as e:
            logger.error(f"Error updating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity from Elasticsearch.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            try:
                response = await self.client.delete(
                    index=self.index_name,
                    id=str(entity_id),
                    refresh=self.refresh
                )
                
                return response.get('result') == 'deleted'
                
            except NotFoundError:
                return False
                
        except Exception as e:
            if not isinstance(e, NotFoundError):  # Don't log not found as error
                logger.error(f"Error deleting entity {self.entity_type.__name__} with ID {entity_id}: {e}")
            return False
    
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if an entity exists in Elasticsearch.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        try:
            return await self.client.exists(
                index=self.index_name,
                id=str(entity_id)
            )
            
        except Exception as e:
            logger.error(f"Error checking if entity {self.entity_type.__name__} exists with ID {entity_id}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters in Elasticsearch.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching the filters
        """
        try:
            query = {"match_all": {}} if not filters else {"term": filters}
            
            response = await self.client.count(
                index=self.index_name,
                body={"query": query}
            )
            
            return response.get('count', 0)
            
        except Exception as e:
            logger.error(f"Error counting entities {self.entity_type.__name__}: {e}")
            raise
    
    async def find(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find entities matching the given filters in Elasticsearch.
        
        Args:
            filters: Filters to apply
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the filters
        """
        try:
            # Build the query
            if not filters:
                query = {"match_all": {}}
            else:
                # Convert simple filters to Elasticsearch term filters
                terms = {}
                for field, value in filters.items():
                    terms[field] = value
                query = {"term": terms}
            
            # Execute the search
            response = await self.client.search(
                index=self.index_name,
                body={
                    "query": query,
                    "from": offset,
                    "size": limit
                }
            )
            
            hits = response.get('hits', {}).get('hits', [])
            
            entities = []
            for hit in hits:
                entity_dict = hit['_source']
                
                # Ensure the ID is included
                if 'id' not in entity_dict:
                    entity_dict['id'] = hit['_id']
                
                entity = self._dict_to_entity(entity_dict)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error finding entities {self.entity_type.__name__}: {e}")
            raise
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary representation for Elasticsearch."""
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
