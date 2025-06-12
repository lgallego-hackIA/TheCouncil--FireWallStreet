# Creating and Managing Automations in theCouncil

This guide explains how to create, configure, and manage automations in theCouncil. This system allows you to rapidly build and deploy modular, test-friendly APIs.

## 1. What is an Automation?

An automation in theCouncil is a self-contained API module that includes:
- A collection of endpoints with defined HTTP methods.
- A dedicated, consolidated `handlers.py` file containing the business logic for each endpoint.
- A minimal `router.py` for health checks.
- A JSON configuration file defining its properties, endpoints, and database connections.
- Auto-generated test file stubs.

## 2. Creation Process

New automations are created using an interactive wizard.

### 2.1. Running the Creation Wizard

To start, run the following command from the project root:

```bash
python create_automation.py
```

The wizard will prompt you for:
- **Automation Name**: A unique, URL-friendly name (e.g., `market-prices`).
- **Display Name**: A human-readable name (e.g., `Market Prices`).
- **Description**: A brief summary of the automation's purpose.
- **Endpoints**: You can define one or more endpoints by specifying:
    - **Path**: The URL path (e.g., `/prices`).
    - **HTTP Method**: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`.
    - **Description**: A description for the endpoint.

### 2.2. Generated File Structure

After completing the wizard, the following structure is created under `src/interfaces/api/routers/<automation-name>/`:

-   `__init__.py`: Initializes the router module.
-   `router.py`: Contains only the FastAPI `APIRouter` and a default health check endpoint. All custom endpoint logic is delegated to handlers.
-   `handlers.py`: **(New Modular Approach)** A single, consolidated file containing a separate handler function for each endpoint you defined (e.g., `handle_get_prices`). This is where you will implement the business logic for your API.

A corresponding JSON configuration file is also created in `data/automations/`.

### 2.3. Automation Activation

As of the latest update, **new automations are created with `"status": "active"` by default**. You no longer need to manually edit the JSON file to activate them. The server will automatically load and register the routes upon restart.

## 3. Dynamic Routing and Handlers

The `RouterManager` is responsible for dynamically loading all active automations when the server starts.

-   It reads the JSON configuration for each active automation.
-   It dynamically imports the handler functions specified in the `handler_path` for each endpoint (e.g., `src.interfaces.api.routers.market-prices.handlers.handle_get_prices`).
-   It registers each route with FastAPI, wrapping the handler to inject dependencies like the automation configuration and background tasks.

**Key Improvement**: A critical late-binding closure bug in the `RouterManager` was fixed. This ensures that every endpoint is correctly mapped to its specific handler function and automation context, preventing issues where all routes would incorrectly point to the logic of the last-loaded endpoint.

## 4. Deleting Automations

To remove an automation and all its associated files (router, tests, configuration), use the `delete_automation.py` script.

```bash
python delete_automation.py --name <automation-name>
```

The script will ask for confirmation before deleting the files.

## 5. Server Restart

**Important**: After creating, modifying, or deleting any automation, you must **restart the FastAPI server** for the changes to take effect. The server only loads automation configurations on startup.
