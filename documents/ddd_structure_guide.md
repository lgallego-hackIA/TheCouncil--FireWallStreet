# Domain-Driven Design Structure Generation Guide

## Overview

theCouncil framework includes a powerful feature to automatically generate Domain-Driven Design (DDD) file structures when creating new automations. This guide explains how to use this feature and how to leverage the generated code structure.

## Why Domain-Driven Design?

Domain-Driven Design is an approach to software development that focuses on:

1. **Understanding the domain** - The business context in which your software operates
2. **Separating concerns** - Organizing code to maintain clear boundaries between different layers
3. **Shared language** - Using a consistent vocabulary between developers and domain experts
4. **Model-driven design** - Focusing on the core domain models that represent business entities

DDD helps create more maintainable, scalable, and business-aligned code, especially for complex applications.

## Enabling DDD Structure Generation

When creating a new automation through the Console API, set the `generate_ddd_structure` flag to `true`:

```bash
curl -X POST "http://localhost:8000/console/automations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "inventory",
    "description": "Inventory management system",
    "base_path": "/api/inventory",
    "version": "1.0.0",
    "db_config": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://localhost:27017",
        "database": "inventory_db"
      },
      "collection_name": "items"
    },
    "generate_ddd_structure": true
  }'
```

## Generated Structure

The system will create the following directory structure and files under `src/domain/automations/{automation_name}/`:

```
src/domain/automations/inventory/
├── README.md                 # Documentation and usage instructions
├── __init__.py
├── domain/                   # Domain Layer
│   ├── __init__.py
│   ├── models.py             # Domain models/entities using Pydantic
│   └── service.py            # Domain business logic
├── application/              # Application Layer
│   ├── __init__.py
│   └── service.py            # Application services and use cases
├── infrastructure/           # Infrastructure Layer
│   ├── __init__.py
│   └── repository.py         # Data access repositories
└── interface/                # Interface Layer
    ├── __init__.py
    └── handlers.py           # API endpoint handlers
```

## Layers Explanation

### 1. Domain Layer

The core of your business logic, containing:

- **Models**: Pydantic models representing your business entities and value objects
- **Services**: Core business rules and logic

**Example usage:**
```python
# In domain/models.py
from pydantic import BaseModel
from datetime import datetime

class InventoryItem(BaseModel):
    id: Optional[str] = None
    name: str
    quantity: int
    location: str
    updated_at: datetime = datetime.now()
```

### 2. Application Layer

Orchestrates the flow between domain and infrastructure:

- **Services**: Coordinates domain objects, repositories, and external services
- **Use Cases**: Implements specific application functionality

**Example usage:**
```python
# In application/service.py
async def add_inventory_item(self, item_data: Dict[str, Any]) -> InventoryItem:
    # Create domain entity
    item = InventoryItem(**item_data)
    
    # Apply domain logic
    validated_item = await self.domain_service.validate_item(item)
    
    # Save to repository
    return await self.repository.create(validated_item)
```

### 3. Infrastructure Layer

Handles external concerns:

- **Repositories**: Data access logic for persistence
- **External Services**: Integration with external systems

**Example usage:**
```python
# In infrastructure/repository.py
async def get_by_location(self, location: str) -> List[InventoryItem]:
    # Implement MongoDB query for location
    documents = await self.db_collection.find({"location": location}).to_list(length=100)
    return [InventoryItem(**doc) for doc in documents]
```

### 4. Interface Layer

Adapters to external interfaces:

- **Handlers**: API endpoint handlers for your automation
- **Controllers**: Interface adapters

**Example usage:**
```python
# In interface/handlers.py
async def get_items_by_location(params: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
    location = params.get("location")
    items = await app_service.get_by_location(location)
    return {"items": items, "total": len(items)}
```

## Connecting Custom Handlers to Endpoints

Once you've generated the DDD structure, you can connect your custom handlers to endpoints:

```bash
curl -X POST "http://localhost:8000/console/automations/{automation_id}/endpoints" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/location/{location}",
    "method": "GET",
    "summary": "Get inventory by location",
    "handler_path": "src.domain.automations.inventory.interface.handlers.get_items_by_location",
    "parameters": [
      {
        "name": "location",
        "in": "path",
        "required": true,
        "type": "string"
      }
    ]
  }'
```

## Best Practices

1. **Keep domain logic in the domain layer** - Don't mix business rules with database access
2. **Use repositories for data access** - Never access databases directly from services
3. **Implement validation in domain services** - Ensure domain rules are enforced
4. **Keep handlers thin** - Handlers should delegate to application services rather than implement logic
5. **Document your models** - Add docstrings to explain your domain model attributes and constraints

## Common Customizations

1. **Adding custom domain logic**:
   - Edit `domain/service.py` to implement business rules
   
2. **Database operations**:
   - Extend `infrastructure/repository.py` with database-specific operations
   
3. **API parameter validation**:
   - Add parameter validation in `interface/handlers.py`
   
4. **New entity relationships**:
   - Define related models in `domain/models.py` and implement relationship logic

## Troubleshooting

- **Handler not found**: Ensure your handler path matches the actual location of your function
- **Database connection issues**: Check your database connection configuration
- **Import errors**: Make sure all necessary dependencies are installed
- **Domain model validation errors**: Check that your data conforms to the model definitions
