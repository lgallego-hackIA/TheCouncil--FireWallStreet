# Creating Automations in theCouncil

This guide explains how to create and configure automations in theCouncil, which allows you to rapidly build and deploy APIs with database integration without writing code.

## What is an Automation?

An automation in theCouncil is a configurable API that includes:
- A collection of endpoints with defined HTTP methods
- Database configuration and connection details
- Parameter definitions for each endpoint
- Metadata and configuration options

## Two Ways to Create Automations

### 1. Using the Console API

The Console API provides endpoints for managing automations programmatically:

```bash
# Create a new automation
curl -X POST http://localhost:8000/console/automations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "users",
    "description": "User management API",
    "version": "1.0.0"
  }'

# Get automation details
curl http://localhost:8000/console/automations/users

# Adding endpoints to an automation
curl -X POST http://localhost:8000/console/automations/users/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/users",
    "method": "GET",
    "summary": "List all users",
    "description": "Retrieve a list of all users with optional filtering",
    "parameters": [
      {
        "name": "limit",
        "type": "integer",
        "description": "Maximum number of users to return",
        "required": false,
        "default": 10
      }
    ],
    "active": true
  }'
```

### 2. Creating Automation JSON Files Directly

You can also create automation JSON files directly in the `data/automations/` directory:

1. Create a new JSON file with a unique name (e.g., `my_automation.json`)
2. Define the automation structure (see example below)
3. Restart the application or use the reload endpoint to load the new automation

## Automation JSON Structure

Here's the complete structure of an automation configuration file:

```json
{
  "id": "unique-uuid-here",
  "name": "my_automation",
  "description": "Description of what this API does",
  "version": "1.0.0",
  "created_at": "2024-07-07T00:00:00.000000",
  "updated_at": "2024-07-07T00:00:00.000000",
  "status": "active",
  "endpoints": [
    {
      "path": "/items",
      "method": "GET",
      "summary": "List all items",
      "description": "Retrieve a list of all items with optional filtering",
      "parameters": [
        {
          "name": "limit",
          "type": "integer",
          "description": "Maximum number of items to return",
          "required": false,
          "default": 10
        }
      ],
      "requires_auth": false,
      "active": true,
      "wrap_response": true,
      "single_item": false
    }
  ],
  "db_config": {
    "type": "mongodb",
    "config": {
      "uri": "mongodb://localhost:27017",
      "database": "my_database"
    },
    "collection_name": "items"
  },
  "metadata": {
    "creator": "Your Name",
    "tags": ["example", "api"],
    "notes": "Any additional information"
  }
}
```

## Key Components of an Automation

### 1. Basic Information

- `id`: A unique identifier for the automation (UUID format)
- `name`: Name of the automation (used in API URLs)
- `description`: Description of what the automation does
- `version`: Version of the automation
- `status`: Status of the automation (active, inactive, draft)

### 2. Database Configuration

The `db_config` section defines the database connection:

```json
"db_config": {
  "type": "mongodb",  // Options: postgres, mongodb, redis, elasticsearch, dynamodb
  "config": {
    // Connection details (varies by database type)
    "uri": "mongodb://localhost:27017",
    "database": "my_database"
  },
  "collection_name": "items"  // For document databases
  // OR "table_name": "items"  // For relational databases
  // OR "index_name": "items"  // For Elasticsearch
}
```

#### Supported Database Types:

1. **PostgreSQL**
```json
"db_config": {
  "type": "postgres",
  "config": {
    "uri": "postgresql://username:password@localhost:5432/database",
    "schema": "public"
  },
  "table_name": "items"
}
```

2. **MongoDB**
```json
"db_config": {
  "type": "mongodb",
  "config": {
    "uri": "mongodb://localhost:27017",
    "database": "my_database"
  },
  "collection_name": "items"
}
```

3. **Redis**
```json
"db_config": {
  "type": "redis",
  "config": {
    "uri": "redis://localhost:6379",
    "db": 0
  }
}
```

4. **Elasticsearch**
```json
"db_config": {
  "type": "elasticsearch",
  "config": {
    "hosts": ["http://localhost:9200"],
    "username": "elastic",
    "password": "password"
  },
  "index_name": "items"
}
```

5. **DynamoDB**
```json
"db_config": {
  "type": "dynamodb",
  "config": {
    "region": "us-east-1",
    "access_key_id": "your_access_key",
    "secret_access_key": "your_secret_key"
  },
  "table_name": "items"
}
```

### 3. Endpoints

The `endpoints` array contains the API endpoints for the automation:

```json
"endpoints": [
  {
    "path": "/items",
    "method": "GET",  // GET, POST, PUT, DELETE, PATCH
    "summary": "Short description",
    "description": "Longer description of what this endpoint does",
    "parameters": [
      {
        "name": "param_name",
        "type": "string",  // string, integer, float, boolean, object, array, file
        "description": "Parameter description",
        "required": true,
        "default": "default_value"  // Optional default value
      }
    ],
    "requires_auth": false,  // Whether authentication is required
    "active": true,  // Whether this endpoint is active
    "wrap_response": false,  // Whether to wrap the response in a data object
    "single_item": false,  // For GET requests, whether this returns a single item
    "id_field": "id"  // Field to use as identifier for single items
  }
]
```

#### Parameter Types

The following parameter types are supported:
- `string`: Text values
- `integer`: Whole numbers
- `float`: Decimal numbers
- `boolean`: True/false values
- `object`: JSON objects
- `array`: Arrays/lists
- `file`: File uploads

## Common Endpoint Patterns

### List Endpoint (GET)

```json
{
  "path": "/items",
  "method": "GET",
  "summary": "List all items",
  "description": "Retrieve a list of all items with optional filtering",
  "parameters": [
    {
      "name": "limit",
      "type": "integer",
      "description": "Maximum number of items to return",
      "required": false,
      "default": 10
    },
    {
      "name": "offset",
      "type": "integer",
      "description": "Number of items to skip",
      "required": false,
      "default": 0
    },
    {
      "name": "sort",
      "type": "string",
      "description": "Field to sort by",
      "required": false
    }
  ],
  "single_item": false,
  "wrap_response": true
}
```

### Detail Endpoint (GET with ID)

```json
{
  "path": "/items/{item_id}",
  "method": "GET",
  "summary": "Get an item by ID",
  "description": "Retrieve a single item by its ID",
  "parameters": [
    {
      "name": "item_id",
      "type": "string",
      "description": "ID of the item to retrieve",
      "required": true
    }
  ],
  "single_item": true,
  "id_field": "item_id"
}
```

### Create Endpoint (POST)

```json
{
  "path": "/items",
  "method": "POST",
  "summary": "Create a new item",
  "description": "Create a new item with the provided details",
  "parameters": [
    {
      "name": "name",
      "type": "string",
      "description": "Name of the item",
      "required": true
    },
    {
      "name": "description",
      "type": "string",
      "description": "Description of the item",
      "required": false
    }
  ]
}
```

### Update Endpoint (PUT)

```json
{
  "path": "/items/{item_id}",
  "method": "PUT",
  "summary": "Update an item",
  "description": "Update an existing item with the provided details",
  "parameters": [
    {
      "name": "item_id",
      "type": "string",
      "description": "ID of the item to update",
      "required": true
    },
    {
      "name": "name",
      "type": "string",
      "description": "Name of the item",
      "required": true
    },
    {
      "name": "description",
      "type": "string",
      "description": "Description of the item",
      "required": false
    }
  ],
  "id_field": "item_id"
}
```

### Delete Endpoint (DELETE)

```json
{
  "path": "/items/{item_id}",
  "method": "DELETE",
  "summary": "Delete an item",
  "description": "Delete an item by its ID",
  "parameters": [
    {
      "name": "item_id",
      "type": "string",
      "description": "ID of the item to delete",
      "required": true
    }
  ],
  "id_field": "item_id"
}
```

## Best Practices

1. **Use clear naming conventions**:
   - Use plural nouns for collection endpoints (e.g., `/users`, `/products`)
   - Use consistent casing (e.g., `snake_case` for field names)

2. **Organize endpoints**:
   - Group endpoints by resource
   - Use consistent URL patterns

3. **Parameter documentation**:
   - Provide clear descriptions for all parameters
   - Specify default values when applicable
   - Mark required fields appropriately

4. **Security**:
   - Set `requires_auth: true` for sensitive endpoints
   - Be mindful of database connection security (use environment variables for credentials)

5. **Response formatting**:
   - Use `wrap_response: true` for list endpoints to include metadata
   - Keep responses consistent across similar endpoints

## Activating an Automation

After creating an automation, you need to activate it:

```bash
# Using the Console API
curl -X PUT http://localhost:8000/console/automations/my_automation/activate

# Or update the status field in the JSON file directly
"status": "active"
```

## Testing Your Automation

Once activated, your API endpoints will be available at:

```
http://localhost:8000/{automation_name}/{endpoint_path}
```

For example, if you created an automation named "users" with a `/list` endpoint:

```
http://localhost:8000/users/list
```

## Troubleshooting

If your automation isn't working as expected:

1. Check the logs for error messages
2. Verify the database connection is working
3. Ensure the automation status is set to "active"
4. Confirm endpoint parameters match what you're sending
5. Check for JSON syntax errors in your automation configuration

## Advanced Features

### Response Wrapping

When `wrap_response` is set to `true`, the API response will be wrapped in a structure like:

```json
{
  "data": [...],
  "success": true
}
```

This is useful for list endpoints where you might want to include metadata.

### Single Item Endpoints

For endpoints that return a single item (like GET by ID), set `single_item: true` and specify the `id_field` to identify which parameter contains the ID.
