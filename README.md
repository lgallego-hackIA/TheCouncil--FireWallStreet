# theCouncil

A dynamic FastAPI backend automation framework for rapid API development with Domain-Driven Design principles.

## Overview

theCouncil is a flexible API automation framework that enables rapid development of backend services without writing boilerplate code. The system uses a configuration-based approach to dynamically generate API endpoints with database integration, while supporting custom business logic through a Domain-Driven Design architecture.

### Key Features

- **Dynamic API Generation**: Create API endpoints through configuration rather than coding
- **Multiple Database Support**: MongoDB, PostgreSQL, DynamoDB, Redis, Elasticsearch
- **Domain-Driven Design**: Automatic generation of DDD-structured code for business logic
- **Console Management API**: RESTful interface for managing automations
- **Flexible Extension Points**: Custom handlers for business logic implementation

## Setup

1. Clone this repository
   ```bash
   git clone https://github.com/GeoPark-hackers/theCouncil
   cd theCouncil
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python -m src.main
   ```

## Usage

### Creating Automations

Create a new automation with a database connection and endpoints:

```bash
# Create a new automation with DDD structure generation
curl -X POST "http://localhost:8000/console/automations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "orders",
    "description": "Order management automation",
    "base_path": "/api/orders",
    "version": "1.0.0",
    "db_config": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://localhost:27017",
        "database": "orders_db"
      },
      "collection_name": "orders"
    },
    "generate_ddd_structure": true
  }'
```

This will generate a complete Domain-Driven Design folder structure under `src/domain/automations/orders/` with the following components:

- **Domain Layer**: Models and business logic
- **Application Layer**: Service orchestration and use cases
- **Infrastructure Layer**: Data access and external services
- **Interface Layer**: API handlers and controllers

Refer to the [documentation](./documents/creating_automations.md) for more details.
