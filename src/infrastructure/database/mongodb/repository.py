"""
MongoDB repository implementation.
"""
import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infrastructure.database.base_repository import BaseRepository

T = TypeVar('T')  # Type of domain entity

logger = logging.getLogger(__name__)


class MongoDBRepository(BaseRepository[T], Generic[T]):
    """
    MongoDB repository implementation using Motor.
    """

    def __init__(self, database: AsyncIOMotorDatabase, entity_type: Type[T], collection_name: str = None):
        """
        Initialize the MongoDB repository.
        
        Args:
            database: MongoDB database instance
            entity_type: Domain entity type
            collection_name: Name of the collection (defaults to entity_type name in lowercase)
        """
        self.db = database
        self.entity_type = entity_type
        self.collection_name = collection_name or entity_type.__name__.lower()
        self.collection = self.db[self.collection_name]
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the database.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID
        """
        try:
            # Convert entity to dictionary
            entity_dict = self._entity_to_dict(entity)
            
            # Remove _id if it's None
            if '_id' in entity_dict and entity_dict['_id'] is None:
                del entity_dict['_id']
            
            # Insert the document
            result = await self.collection.insert_one(entity_dict)
            
            # Update the entity with the generated ID if needed
            if hasattr(entity, 'id') and not getattr(entity, 'id', None):
                setattr(entity, 'id', str(result.inserted_id))
            elif hasattr(entity, '_id') and not getattr(entity, '_id', None):
                setattr(entity, '_id', str(result.inserted_id))
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity to get
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(entity_id, str) and ObjectId.is_valid(entity_id):
                entity_id = ObjectId(entity_id)
            
            # Query the document
            document = await self.collection.find_one({'_id': entity_id})
            
            if document is None:
                return None
            
            # Convert document to entity
            return self._dict_to_entity(document)
            
        except Exception as e:
            logger.error(f"Error getting entity {self.entity_type.__name__} by ID {entity_id}: {e}")
            raise
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        try:
            cursor = self.collection.find().skip(offset).limit(limit)
            documents = []
            
            async for document in cursor:
                documents.append(document)
            
            # Convert documents to entities
            return [self._dict_to_entity(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error getting all entities {self.entity_type.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity if successful, None otherwise
        """
        try:
            # Convert entity to dictionary
            entity_dict = self._entity_to_dict(entity)
            
            # Get the ID
            entity_id = entity_dict.pop('_id', None)
            if entity_id is None and hasattr(entity, 'id'):
                entity_id = getattr(entity, 'id')
                if isinstance(entity_id, str) and ObjectId.is_valid(entity_id):
                    entity_id = ObjectId(entity_id)
            
            if entity_id is None:
                logger.error(f"Cannot update entity {self.entity_type.__name__} without ID")
                return None
            
            # Update the document
            result = await self.collection.update_one(
                {'_id': entity_id},
                {'$set': entity_dict}
            )
            
            if result.matched_count == 0:
                return None
            
            # Get the updated document
            updated_doc = await self.collection.find_one({'_id': entity_id})
            return self._dict_to_entity(updated_doc)
            
        except Exception as e:
            logger.error(f"Error updating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(entity_id, str) and ObjectId.is_valid(entity_id):
                entity_id = ObjectId(entity_id)
            
            # Delete the document
            result = await self.collection.delete_one({'_id': entity_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting entity {self.entity_type.__name__} with ID {entity_id}: {e}")
            raise
    
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(entity_id, str) and ObjectId.is_valid(entity_id):
                entity_id = ObjectId(entity_id)
            
            # Count documents with this ID
            count = await self.collection.count_documents({'_id': entity_id})
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if entity {self.entity_type.__name__} exists with ID {entity_id}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching the filters
        """
        try:
            # Apply filters if provided, otherwise count all
            query = filters or {}
            
            # Convert string IDs to ObjectIds if necessary
            if '_id' in query and isinstance(query['_id'], str) and ObjectId.is_valid(query['_id']):
                query['_id'] = ObjectId(query['_id'])
            
            return await self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error counting entities {self.entity_type.__name__}: {e}")
            raise
    
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
        try:
            # Convert string IDs to ObjectIds if necessary
            query = filters.copy()
            if '_id' in query and isinstance(query['_id'], str) and ObjectId.is_valid(query['_id']):
                query['_id'] = ObjectId(query['_id'])
            
            # Query for matching documents
            cursor = self.collection.find(query).skip(offset).limit(limit)
            documents = []
            
            async for document in cursor:
                documents.append(document)
            
            # Convert documents to entities
            return [self._dict_to_entity(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error finding entities {self.entity_type.__name__}: {e}")
            raise
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary representation for MongoDB."""
        if hasattr(entity, 'dict'):
            # For Pydantic models
            entity_dict = entity.dict()
        elif hasattr(entity, '__dict__'):
            # For standard classes
            entity_dict = entity.__dict__.copy()
        else:
            # For dictionaries or other mappings
            entity_dict = dict(entity)
        
        # Handle ID conversion
        if 'id' in entity_dict and not '_id' in entity_dict:
            if entity_dict['id']:
                if isinstance(entity_dict['id'], str) and ObjectId.is_valid(entity_dict['id']):
                    entity_dict['_id'] = ObjectId(entity_dict['id'])
                else:
                    entity_dict['_id'] = entity_dict['id']
            
            # Remove the 'id' field since MongoDB uses '_id'
            del entity_dict['id']
        
        return entity_dict
    
    def _dict_to_entity(self, document: Dict[str, Any]) -> T:
        """Convert MongoDB document to entity."""
        # Convert ObjectId to string for ID
        if '_id' in document:
            document['id'] = str(document['_id'])
            del document['_id']
        
        # Use Pydantic model if the entity type is one
        if hasattr(self.entity_type, 'parse_obj'):
            return self.entity_type.parse_obj(document)
        elif hasattr(self.entity_type, 'from_dict'):
            return self.entity_type.from_dict(document)
        else:
            # For standard classes, use constructor
            return self.entity_type(**document)
