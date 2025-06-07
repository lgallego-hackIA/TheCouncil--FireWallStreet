"""
PostgreSQL repository implementation.
"""
import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.base_repository import BaseRepository

T = TypeVar('T')  # Type of domain entity
M = TypeVar('M')  # Type of SQLAlchemy model

logger = logging.getLogger(__name__)


class PostgreSQLRepository(BaseRepository[T], Generic[T, M]):
    """
    PostgreSQL repository implementation using SQLAlchemy.
    """

    def __init__(self, session_factory: sessionmaker, entity_type: Type[T], model_type: Type[M] = None):
        """
        Initialize the PostgreSQL repository.
        
        Args:
            session_factory: SQLAlchemy session factory
            entity_type: Domain entity type
            model_type: SQLAlchemy model type (if different from entity_type)
        """
        self.session_factory = session_factory
        self.entity_type = entity_type
        self.model_type = model_type or entity_type
    
    async def _get_session(self) -> AsyncSession:
        """Get a new session from the session factory."""
        return self.session_factory()
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the database.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID
        """
        async with await self._get_session() as session:
            try:
                # Convert entity to model if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    model = self.model_type(**entity.dict())
                else:
                    model = entity
                
                session.add(model)
                await session.commit()
                await session.refresh(model)
                
                # Convert model back to entity if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    return self.entity_type.from_orm(model)
                return model
                
            except Exception as e:
                await session.rollback()
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
        async with await self._get_session() as session:
            try:
                query = select(self.model_type).where(self.model_type.id == entity_id)
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                if model is None:
                    return None
                
                # Convert model to entity if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    return self.entity_type.from_orm(model)
                return model
                
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
        async with await self._get_session() as session:
            try:
                query = select(self.model_type).limit(limit).offset(offset)
                result = await session.execute(query)
                models = result.scalars().all()
                
                # Convert models to entities if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    return [self.entity_type.from_orm(model) for model in models]
                return list(models)
                
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
        async with await self._get_session() as session:
            try:
                # Check if the entity exists
                query = select(self.model_type).where(self.model_type.id == entity.id)
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                if model is None:
                    return None
                
                # Update model fields from entity
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    for key, value in entity.dict(exclude={"id"}).items():
                        setattr(model, key, value)
                else:
                    # If entity is the model, just merge it
                    model = await session.merge(entity)
                
                await session.commit()
                await session.refresh(model)
                
                # Convert model to entity if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    return self.entity_type.from_orm(model)
                return model
                
            except Exception as e:
                await session.rollback()
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
        async with await self._get_session() as session:
            try:
                query = delete(self.model_type).where(self.model_type.id == entity_id)
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
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
        async with await self._get_session() as session:
            try:
                query = select(self.model_type.id).where(self.model_type.id == entity_id)
                result = await session.execute(query)
                
                return result.scalar_one_or_none() is not None
                
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
        async with await self._get_session() as session:
            try:
                from sqlalchemy import func
                
                # Start with a base query
                query = select(func.count(self.model_type.id))
                
                # Apply filters if provided
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model_type, field):
                            query = query.where(getattr(self.model_type, field) == value)
                
                result = await session.execute(query)
                return result.scalar_one()
                
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
        async with await self._get_session() as session:
            try:
                # Start with a base query
                query = select(self.model_type)
                
                # Apply filters
                for field, value in filters.items():
                    if hasattr(self.model_type, field):
                        query = query.where(getattr(self.model_type, field) == value)
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                models = result.scalars().all()
                
                # Convert models to entities if necessary
                if self.model_type != self.entity_type:
                    # In a real application, you would use a mapper here
                    return [self.entity_type.from_orm(model) for model in models]
                return list(models)
                
            except Exception as e:
                logger.error(f"Error finding entities {self.entity_type.__name__}: {e}")
                raise
