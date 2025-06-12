"""
Factory for creating database repositories based on automation configuration.
"""
import logging
from typing import Any, Dict, Generic, Optional, Type, TypeVar
import asyncio

from src.domain.automation.models import DatabaseConfig, DatabaseType
from src.infrastructure.database.base_repository import BaseRepository
from src.shared.exceptions import ConfigurationError, DatabaseConnectionError

# Import specific repository implementations
from src.infrastructure.database.postgresql.repository import PostgreSQLRepository
from src.infrastructure.database.mongodb.repository import MongoDBRepository
from src.infrastructure.database.redis.repository import RedisRepository
from src.infrastructure.database.elasticsearch.repository import ElasticsearchRepository
from src.infrastructure.database.dynamodb.repository import DynamoDBRepository

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type of entity


class DatabaseFactory:
    """Factory for creating database repositories based on database configuration."""

    def __init__(self):
        """Initialize the database factory."""
        self._db_clients: Dict[str, Any] = {}
    
    def create_repository(
        self, 
        entity_type: Type[T], 
        db_config: DatabaseConfig
    ) -> BaseRepository[T]:
        """
        Create a repository for the given entity type and database configuration.
        
        Args:
            entity_type: Type of entity to create a repository for
            db_config: Database configuration
            
        Returns:
            Repository instance
            
        Raises:
            ConfigurationError: If the database type is not supported
            DatabaseConnectionError: If there's an error connecting to the database
        """
        db_type = db_config.type
        
        try:
            if db_type == DatabaseType.POSTGRES:
                client = self._get_or_create_postgres_client(db_config.config)
                return PostgreSQLRepository(client, entity_type)
            
            elif db_type == DatabaseType.MONGODB:
                client = self._get_or_create_mongodb_client(db_config.config)
                return MongoDBRepository(client, entity_type)
            
            elif db_type == DatabaseType.REDIS:
                client = self._get_or_create_redis_client(db_config.config)
                return RedisRepository(client, entity_type)
            
            elif db_type == DatabaseType.ELASTICSEARCH:
                client = self._get_or_create_elasticsearch_client(db_config.config)
                return ElasticsearchRepository(client, entity_type)
            
            elif db_type == DatabaseType.DYNAMODB:
                client = self._get_or_create_dynamodb_client(db_config.config)
                return DynamoDBRepository(client, entity_type)
            
            else:
                raise ConfigurationError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Error creating repository for {entity_type.__name__}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to {db_type} database: {e}")
    
    def _get_or_create_postgres_client(self, config: Dict[str, Any]) -> Any:
        """
        Get or create a PostgreSQL client.
        
        Args:
            config: PostgreSQL configuration
            
        Returns:
            PostgreSQL client
        """
        client_key = f"postgres:{config.get('database', 'default')}"
        
        if client_key not in self._db_clients:
            # In a real implementation, this would create a SQLAlchemy engine or similar
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            
            connection_string = config.get('connection_string')
            if not connection_string:
                # Build connection string from individual config parameters
                user = config.get('username', '')
                password = config.get('password', '')
                host = config.get('host', 'localhost')
                port = config.get('port', 5432)
                database = config.get('database', '')
                
                connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
            
            engine = create_async_engine(
                connection_string,
                echo=config.get('echo', False),
                pool_size=config.get('pool_size', 5),
            )
            
            async_session = sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            self._db_clients[client_key] = async_session
            
        return self._db_clients[client_key]
    
    def _get_or_create_mongodb_client(self, config: Dict[str, Any]) -> Any:
        """
        Get or create a MongoDB client.
        
        Args:
            config: MongoDB configuration
            
        Returns:
            MongoDB client
        """
        client_key = f"mongodb:{config.get('database', 'default')}"
        
        if client_key not in self._db_clients:
            # In a real implementation, this would create a Motor client
            from motor.motor_asyncio import AsyncIOMotorClient
            import pymongo.errors
            
            connection_string = config.get('connection_string', 'mongodb://localhost:27017')
            database = config.get('database', 'default')
            
            try:
                # Create client with serverSelectionTimeoutMS to fail fast if server is unreachable
                client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
                
                # Trigger connection check with a lightweight command
                client.admin.command('ismaster')
                
                db = client[database]
                self._db_clients[client_key] = db
            except (pymongo.errors.ServerSelectionTimeoutError, 
                    pymongo.errors.ConnectionFailure,
                    pymongo.errors.NetworkTimeout) as e:
                logger.error(f"MongoDB connection error: {str(e)}")
                raise DatabaseConnectionError(
                    f"Failed to connect to MongoDB at {connection_string}. " 
                    f"Please ensure the MongoDB server is running and accessible: {str(e)}"
                )
            
        return self._db_clients[client_key]
    
    def _get_or_create_redis_client(self, config: Dict[str, Any]) -> Any:
        """
        Get or create a Redis client.
        
        Args:
            config: Redis configuration
            
        Returns:
            Redis client
        """
        client_key = f"redis:{config.get('host', 'localhost')}:{config.get('port', 6379)}"
        
        if client_key not in self._db_clients:
            # In a real implementation, this would create a Redis client
            import redis.asyncio as redis
            
            host = config.get('host', 'localhost')
            port = config.get('port', 6379)
            db = config.get('db', 0)
            password = config.get('password', None)
            
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            
            self._db_clients[client_key] = client
            
        return self._db_clients[client_key]
    
    def _get_or_create_elasticsearch_client(self, config: Dict[str, Any]) -> Any:
        """
        Get or create an Elasticsearch client.
        
        Args:
            config: Elasticsearch configuration
            
        Returns:
            Elasticsearch client
        """
        client_key = f"elasticsearch:{config.get('hosts', ['http://localhost:9200'])[0]}"
        
        if client_key not in self._db_clients:
            # In a real implementation, this would create an Elasticsearch client
            from elasticsearch import AsyncElasticsearch
            
            hosts = config.get('hosts', ['http://localhost:9200'])
            
            client = AsyncElasticsearch(
                hosts=hosts,
                basic_auth=(
                    config.get('username', ''),
                    config.get('password', '')
                ) if config.get('username') else None,
            )
            
            self._db_clients[client_key] = client
            
        return self._db_clients[client_key]
    
    def _get_or_create_dynamodb_client(self, config: Dict[str, Any]) -> Any:
        """
        Get or create a DynamoDB client.
        
        Args:
            config: DynamoDB configuration
            
        Returns:
            DynamoDB client
        """
        client_key = f"dynamodb:{config.get('region', 'us-east-1')}"
        
        if client_key not in self._db_clients:
            # In a real implementation, this would create a DynamoDB client
            import aioboto3
            
            region = config.get('region', 'us-east-1')
            endpoint_url = config.get('endpoint_url')
            
            session = aioboto3.Session()
            resource = session.resource(
                'dynamodb',
                region_name=region,
                endpoint_url=endpoint_url
            )
            
            self._db_clients[client_key] = resource
            
        return self._db_clients[client_key]
        
    async def close_connections(self):
        """Close all database connections."""
        for client_key, client in self._db_clients.items():
            try:
                db_type = client_key.split(':')[0]
                
                if db_type == 'postgres':
                    # SQLAlchemy engine
                    pass  # Handled by connection pool
                    
                elif db_type == 'mongodb':
                    # Motor client
                    client.client.close()
                    
                elif db_type == 'redis':
                    # Redis client
                    await client.close()
                    
                elif db_type == 'elasticsearch':
                    # Elasticsearch client
                    await client.close()
                    
                elif db_type == 'dynamodb':
                    # DynamoDB client
                    await client.__aexit__(None, None, None)
                    
                logger.debug(f"Closed database connection: {client_key}")
                
            except Exception as e:
                logger.error(f"Error closing database connection {client_key}: {e}")
        
        self._db_clients = {}
