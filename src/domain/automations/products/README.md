# Products Automation

## Description
Product management system with full CRUD operations

## Structure
This automation follows Domain-Driven Design principles:

- **Domain Layer**: Core business models and logic
- **Application Layer**: Orchestration of domain objects and use cases
- **Infrastructure Layer**: Technical implementations such as repositories
- **Interface Layer**: Handlers for API endpoints

## Usage

1. Implement your domain models in `domain/models.py`
2. Add business logic in `domain/service.py`
3. Configure application services in `application/service.py`
4. Implement data access in `infrastructure/repository.py`
5. Update the request handlers in `interface/handlers.py`

## Endpoints

No endpoints defined yet. Add endpoints to your automation configuration.

## Configuration

To use the custom handlers for your endpoints, update your automation configuration:

```python
# Example for updating an endpoint with custom handler
endpoint.handler_path = "src.domain.automations.products.interface.handlers.create_item"
```
