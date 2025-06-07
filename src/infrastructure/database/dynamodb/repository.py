"""
DynamoDB repository implementation.
"""
import logging
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import aioboto3
from botocore.exceptions import ClientError

from src.infrastructure.database.base_repository import BaseRepository

T = TypeVar('T')  # Type of domain entity

logger = logging.getLogger(__name__)


class DynamoDBRepository(BaseRepository[T], Generic[T]):
    """
    DynamoDB repository implementation using aioboto3.
    """

    def __init__(self, resource, entity_type: Type[T], table_name: str = None):
        """
        Initialize the DynamoDB repository.
        
        Args:
            resource: DynamoDB resource from aioboto3
            entity_type: Domain entity type
            table_name: Name of the DynamoDB table (defaults to entity_type name in lowercase)
        """
        self.resource = resource
        self.entity_type = entity_type
        self.table_name = table_name or entity_type.__name__.lower()
    
    async def _get_table(self):
        """Get the DynamoDB table resource."""
        return await self.resource.Table(self.table_name)
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity in DynamoDB.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID
        """
        try:
            # Convert entity to dictionary
            item = self._entity_to_dict(entity)
            
            # Generate ID if not present
            if 'id' not in item or not item['id']:
                item['id'] = str(uuid.uuid4())
                if hasattr(entity, 'id'):
                    setattr(entity, 'id', item['id'])
            
            # Put item in DynamoDB
            table = await self._get_table()
            await table.put_item(Item=item)
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity by ID from DynamoDB.
        
        Args:
            entity_id: ID of the entity to get
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            table = await self._get_table()
            response = await table.get_item(Key={'id': str(entity_id)})
            
            item = response.get('Item')
            if not item:
                return None
            
            return self._dict_to_entity(item)
            
        except ClientError as e:
            logger.error(f"Error getting entity {self.entity_type.__name__} by ID {entity_id}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting entity {self.entity_type.__name__} by ID {entity_id}: {e}")
            raise
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination from DynamoDB.
        
        Note: DynamoDB doesn't support direct offset pagination, so this
        implementation is less efficient than for other databases.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        try:
            table = await self._get_table()
            
            # DynamoDB doesn't have built-in offset pagination, so we need to scan all
            # items and then apply offset/limit manually
            scan_params = {
                'Limit': offset + limit  # Fetch enough items to apply offset
            }
            
            response = await table.scan(**scan_params)
            items = response.get('Items', [])
            
            # Handle pagination for large datasets
            while 'LastEvaluatedKey' in response and len(items) < offset + limit:
                scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = await table.scan(**scan_params)
                items.extend(response.get('Items', []))
            
            # Apply offset and limit
            items = items[offset:offset + limit]
            
            # Convert to entities
            return [self._dict_to_entity(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting all entities {self.entity_type.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an entity in DynamoDB.
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity if successful, None otherwise
        """
        try:
            # Convert entity to dictionary
            item = self._entity_to_dict(entity)
            
            # Get ID
            entity_id = item.get('id')
            if not entity_id:
                logger.error(f"Cannot update entity {self.entity_type.__name__} without ID")
                return None
            
            # Check if the entity exists
            exists = await self.exists(entity_id)
            
            if not exists:
                return None
            
            # Update in DynamoDB (put_item replaces the entire item)
            table = await self._get_table()
            await table.put_item(Item=item)
            
            return entity
            
        except Exception as e:
            logger.error(f"Error updating entity {self.entity_type.__name__}: {e}")
            raise
    
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity from DynamoDB.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        try:
            # Check if the entity exists first
            exists = await self.exists(entity_id)
            
            if not exists:
                return False
            
            # Delete from DynamoDB
            table = await self._get_table()
            await table.delete_item(Key={'id': str(entity_id)})
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entity {self.entity_type.__name__} with ID {entity_id}: {e}")
            raise
    
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if an entity exists in DynamoDB.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        try:
            table = await self._get_table()
            response = await table.get_item(
                Key={'id': str(entity_id)},
                ProjectionExpression='id'  # Only fetch the ID to minimize transferred data
            )
            
            return 'Item' in response
            
        except Exception as e:
            logger.error(f"Error checking if entity {self.entity_type.__name__} exists with ID {entity_id}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters in DynamoDB.
        
        Note: For filtered counts, this implementation performs a full scan
        with a filter expression, which can be inefficient for large tables.
        Consider using a secondary index for frequently filtered queries.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching the filters
        """
        try:
            table = await self._get_table()
            
            if not filters:
                # Count all items (no filters)
                response = await table.scan(Select='COUNT')
                return response.get('Count', 0)
            
            # For filtered count, use a filter expression
            filter_expression = ' AND '.join([f"{k} = :val_{i}" for i, k in enumerate(filters.keys())])
            expression_values = {f":val_{i}": v for i, (_, v) in enumerate(filters.items())}
            
            response = await table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                Select='COUNT'
            )
            
            count = response.get('Count', 0)
            
            # Handle pagination for large datasets
            while 'LastEvaluatedKey' in response:
                response = await table.scan(
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values,
                    Select='COUNT',
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                count += response.get('Count', 0)
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting entities {self.entity_type.__name__}: {e}")
            raise
    
    async def find(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find entities matching the given filters in DynamoDB.
        
        Note: DynamoDB doesn't support direct offset pagination with filters, so this
        implementation is less efficient than for other databases.
        
        Args:
            filters: Filters to apply
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities matching the filters
        """
        try:
            table = await self._get_table()
            
            if not filters:
                # If no filters, use the get_all method
                return await self.get_all(limit, offset)
            
            # For filtered queries, use a filter expression
            filter_expression = ' AND '.join([f"{k} = :val_{i}" for i, k in enumerate(filters.keys())])
            expression_values = {f":val_{i}": v for i, (_, v) in enumerate(filters.items())}
            
            # DynamoDB doesn't have built-in offset pagination, so we need to scan all
            # items matching the filter and then apply offset/limit manually
            scan_params = {
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_values,
                'Limit': offset + limit  # Fetch enough items to apply offset
            }
            
            response = await table.scan(**scan_params)
            items = response.get('Items', [])
            
            # Handle pagination for large datasets
            while 'LastEvaluatedKey' in response and len(items) < offset + limit:
                scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = await table.scan(**scan_params)
                items.extend(response.get('Items', []))
            
            # Apply offset and limit
            items = items[offset:offset + limit]
            
            # Convert to entities
            return [self._dict_to_entity(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error finding entities {self.entity_type.__name__}: {e}")
            raise
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary representation for DynamoDB."""
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
    
    def _dict_to_entity(self, item: Dict[str, Any]) -> T:
        """Convert DynamoDB item to entity."""
        # Use Pydantic model if the entity type is one
        if hasattr(self.entity_type, 'parse_obj'):
            return self.entity_type.parse_obj(item)
        elif hasattr(self.entity_type, 'from_dict'):
            return self.entity_type.from_dict(item)
        else:
            # For standard classes, use constructor
            return self.entity_type(**item)
