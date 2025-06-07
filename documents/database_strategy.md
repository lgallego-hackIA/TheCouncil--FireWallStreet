# Database Strategy for theCouncil API System

## Overview

This document outlines the database strategy for theCouncil API system, providing a selector framework for choosing the appropriate database based on specific automation requirements. The system supports multiple database technologies, each optimized for different use cases.

## Database Selection Framework

### Selection Criteria

When creating a new automation endpoint group, consider these factors to select the appropriate database:

1. **Data Structure**: Relational, document, key-value, graph, time-series
2. **Query Patterns**: Simple lookups vs. complex queries
3. **Write Patterns**: Write frequency and volume
4. **Consistency Requirements**: ACID vs. eventual consistency
5. **Scalability Needs**: Vertical vs. horizontal scaling
6. **Performance Requirements**: Latency sensitivity
7. **Specialized Features**: Full-text search, geospatial, etc.

## Supported Databases and Use Cases

### PostgreSQL

**Best for:**
- Complex relational data with foreign key relationships
- Transactional systems requiring ACID compliance
- Data with complex schema and validation requirements
- Business-critical data requiring strong consistency

**Example Use Case: Account Management System**

```python
# Domain Model
class Account(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    role: AccountRole
    created_at: datetime
    updated_at: datetime

# Repository Implementation
class PostgreSQLAccountRepository(AccountRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def create(self, account: Account) -> Account:
        db_account = AccountModel(**account.dict())
        self.db_session.add(db_account)
        await self.db_session.commit()
        await self.db_session.refresh(db_account)
        return Account.from_orm(db_account)
    
    async def get_by_id(self, id: UUID) -> Optional[Account]:
        db_account = await self.db_session.query(AccountModel).filter(AccountModel.id == id).first()
        if db_account:
            return Account.from_orm(db_account)
        return None
```

**When to use PostgreSQL:**
- User account management
- Financial transactions
- Inventory management
- Any system requiring complex joins and transactions

### MongoDB

**Best for:**
- Semi-structured or document-oriented data
- Rapidly evolving schemas
- High write throughput applications
- Hierarchical data structures

**Example Use Case: Content Management System**

```python
# Domain Model
class Content(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    body: str
    author_id: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    status: ContentStatus
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Repository Implementation
class MongoDBContentRepository(ContentRepository):
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.content_db
        self.collection = self.db.contents
    
    async def create(self, content: Content) -> Content:
        content_dict = content.dict()
        result = await self.collection.insert_one(content_dict)
        content.id = str(result.inserted_id)
        return content
    
    async def find_by_tags(self, tags: List[str], limit: int = 10) -> List[Content]:
        cursor = self.collection.find({"tags": {"$in": tags}}).limit(limit)
        contents = []
        async for doc in cursor:
            contents.append(Content(**doc))
        return contents
```

**When to use MongoDB:**
- Content management systems
- Product catalogs with variable attributes
- User profiles with dynamic fields
- Log and event storage

### Redis

**Best for:**
- Caching and session storage
- Real-time analytics
- Leaderboards and counters
- Pub/Sub messaging
- Rate limiting and throttling

**Example Use Case: User Session Management**

```python
# Domain Model
class UserSession(BaseModel):
    session_id: str
    user_id: str
    data: Dict[str, Any]
    expires_at: datetime

# Repository Implementation
class RedisSessionRepository(SessionRepository):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:"
    
    async def save(self, session: UserSession) -> None:
        key = f"{self.prefix}{session.session_id}"
        value = json.dumps(session.dict())
        ttl = int((session.expires_at - datetime.now()).total_seconds())
        await self.redis.set(key, value, ex=ttl)
    
    async def get(self, session_id: str) -> Optional[UserSession]:
        key = f"{self.prefix}{session_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        
        session_dict = json.loads(data)
        return UserSession(**session_dict)
```

**When to use Redis:**
- Session storage
- Caching layers
- Real-time analytics
- Rate limiting
- Queues and pub/sub

### Elasticsearch

**Best for:**
- Full-text search requirements
- Log and event data analysis
- Complex search with faceting and filtering
- Search-heavy applications

**Example Use Case: Knowledge Base Search**

```python
# Domain Model
class KnowledgeArticle(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    author: str
    created_at: datetime
    updated_at: datetime

# Repository Implementation
class ElasticsearchKnowledgeRepository(KnowledgeRepository):
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.index = "knowledge_articles"
    
    async def index_article(self, article: KnowledgeArticle) -> None:
        doc = article.dict()
        await self.es.index(index=self.index, id=article.id, body=doc)
    
    async def search(self, query: str, filters: Dict = None, page: int = 1, size: int = 10) -> List[KnowledgeArticle]:
        search_query = {
            "query": {
                "bool": {
                    "must": [{"match": {"content": query}}],
                    "filter": []
                }
            },
            "from": (page - 1) * size,
            "size": size
        }
        
        if filters:
            for field, value in filters.items():
                search_query["query"]["bool"]["filter"].append({"term": {field: value}})
        
        response = await self.es.search(index=self.index, body=search_query)
        
        articles = []
        for hit in response["hits"]["hits"]:
            articles.append(KnowledgeArticle(**hit["_source"]))
        
        return articles
```

**When to use Elasticsearch:**
- Product search engines
- Content search systems
- Log analysis
- Analytics dashboards
- Recommendation systems with complex queries

### DynamoDB

**Best for:**
- Serverless applications
- High-scale applications with predictable access patterns
- Key-value access patterns
- Applications requiring consistent single-digit millisecond performance

**Example Use Case: IoT Device Data**

```python
# Domain Model
class DeviceReading(BaseModel):
    device_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    battery: float

# Repository Implementation
class DynamoDBDeviceRepository(DeviceRepository):
    def __init__(self, dynamo_resource):
        self.table = dynamo_resource.Table('device_readings')
    
    async def save_reading(self, reading: DeviceReading) -> None:
        await self.table.put_item(
            Item={
                'device_id': reading.device_id,
                'timestamp': reading.timestamp.isoformat(),
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'pressure': reading.pressure,
                'battery': reading.battery
            }
        )
    
    async def get_readings(self, device_id: str, start_time: datetime, end_time: datetime) -> List[DeviceReading]:
        response = await self.table.query(
            KeyConditionExpression=
                Key('device_id').eq(device_id) & 
                Key('timestamp').between(start_time.isoformat(), end_time.isoformat())
        )
        
        readings = []
        for item in response['Items']:
            readings.append(DeviceReading(
                device_id=item['device_id'],
                timestamp=datetime.fromisoformat(item['timestamp']),
                temperature=item['temperature'],
                humidity=item['humidity'],
                pressure=item['pressure'],
                battery=item['battery']
            ))
        
        return readings
```

**When to use DynamoDB:**
- Serverless applications
- High-scale web applications
- Gaming leaderboards
- Shopping carts
- IoT device data

## Polyglot Persistence Strategy

For complex automations, the system supports using multiple databases to leverage the strengths of each:

### Example: E-commerce System

```
┌─────────────────────────────────────┐
│ PostgreSQL                          │
│ - Product catalog (core data)       │
│ - Customer accounts                 │
│ - Orders and transactions           │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ Redis                               │
│ - Shopping cart (temporary)         │
│ - Session management                │
│ - Rate limiting                     │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ Elasticsearch                       │
│ - Product search                    │
│ - Search suggestions                │
│ - Recommendation engine             │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ MongoDB                             │
│ - Product reviews                   │
│ - Customer activity logs            │
│ - Wishlist management               │
└─────────────────────────────────────┘
```

## Implementation in theCouncil

The system implements a repository factory pattern that allows automations to select and use appropriate databases:

```python
# Database Factory
class DatabaseFactory:
    def __init__(self, config: Config):
        self.config = config
        self.db_clients = {}
        
    def get_repository(self, repo_type: str, db_type: str):
        """
        Get repository instance based on type and database preference
        
        Args:
            repo_type: Repository type (e.g., "account", "content")
            db_type: Database type (e.g., "postgres", "mongodb")
            
        Returns:
            Repository instance
        """
        if db_type == "postgres":
            if "postgres" not in self.db_clients:
                self.db_clients["postgres"] = create_postgres_client(self.config.postgres)
            
            if repo_type == "account":
                return PostgreSQLAccountRepository(self.db_clients["postgres"])
            # Add more repository types as needed
            
        elif db_type == "mongodb":
            if "mongodb" not in self.db_clients:
                self.db_clients["mongodb"] = create_mongodb_client(self.config.mongodb)
            
            if repo_type == "content":
                return MongoDBContentRepository(self.db_clients["mongodb"])
            # Add more repository types as needed
            
        # Add more database types as needed
        
        raise ValueError(f"Unsupported repository type {repo_type} for database {db_type}")
```

## Configuration Example

When creating a new automation through the console, the database configuration might look like:

```yaml
# Accounts automation database config
name: accounts
database:
  type: postgres
  config:
    host: ${POSTGRES_HOST}
    port: ${POSTGRES_PORT}
    username: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}
    database: accounts_db
    pool_size: 5
    ssl: true

# Content automation database config
name: content
database:
  type: mongodb
  config:
    connection_string: ${MONGODB_URI}
    database: content_db
    max_pool_size: 10
```

## Best Practices

1. **Start Simple**: Begin with PostgreSQL for most automations unless there's a clear need for specialized database features
2. **Consider Growth**: Factor in future scaling needs when selecting a database
3. **Maintain Boundaries**: Each automation should access only its own database resources
4. **Connection Pooling**: Implement proper connection pooling for all database connections
5. **Data Migration**: Design with potential future migrations in mind
6. **Monitoring**: Set up proper monitoring for all database connections and performance

## Migration Strategies

For automations that may need to change database types as requirements evolve:

1. **Dual Write**: Write to both old and new database during transition
2. **Read Migration**: Gradually shift read operations to new database
3. **Data Backfill**: Copy historical data in batches
4. **Validation**: Compare data between systems to ensure consistency
