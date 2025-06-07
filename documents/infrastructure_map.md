# theCouncil Infrastructure Map

## Domain-Driven Design Architecture

```mermaid
graph TD
    subgraph "User Interface Layer"
        A[Web Console] --> B[FastAPI]
        G[GPT Models] --> B
    end
    
    subgraph "API Layer (Interfaces)"
        B --> C[Dynamic Router]
        C --> D1[Accounts Endpoints]
        C --> D2[Other Automation Endpoints]
        C --> D3[New Endpoints...]
    end
    
    subgraph "Application Layer"
        D1 --> E1[Accounts Use Cases]
        D2 --> E2[Other Automation Use Cases]
        D3 --> E3[New Use Cases...]
        
        F[Automation Registry]
        F1[Automation Factory]
    end
    
    subgraph "Domain Layer"
        E1 --> H1[Account Domain Models]
        E2 --> H2[Other Domain Models]
        E3 --> H3[New Domain Models...]
        
        I[Domain Services]
        J[Domain Events]
    end
    
    subgraph "Infrastructure Layer"
        K[Repository Factory]
        
        K --> L1[PostgreSQL Adapter]
        K --> L2[MongoDB Adapter]
        K --> L3[Redis Adapter]
        K --> L4[Elasticsearch Adapter]
        K --> L5[DynamoDB Adapter]
        
        L1 --> M1[(PostgreSQL)]
        L2 --> M2[(MongoDB)]
        L3 --> M3[(Redis)]
        L4 --> M4[(Elasticsearch)]
        L5 --> M5[(DynamoDB)]
        
        N[External Services]
        O[Message Bus]
    end
    
    subgraph "Cross-Cutting Concerns"
        P[Authentication]
        Q[Logging]
        R[Monitoring]
        S[Configuration]
    end
```

## System Components

### Console Automation Creation Flow

```mermaid
sequenceDiagram
    actor Admin
    participant Console
    participant Factory as Automation Factory
    participant Registry as Automation Registry
    participant Router as Dynamic Router
    participant DB as Database Adapter
    
    Admin->>Console: Create new automation "Accounts"
    Console->>Factory: createAutomation("Accounts")
    Factory->>Registry: register(accountsAutomation)
    Registry->>Router: addRoutes("/accounts", endpoints)
    Factory->>DB: createRepositoryFor("Accounts")
    DB-->>Factory: Return repository instance
    Factory-->>Console: Return success
    Console-->>Admin: Display created automation
```

### Request Processing Flow

```mermaid
sequenceDiagram
    actor GPT
    participant API as FastAPI
    participant Router as Dynamic Router
    participant UseCase as Use Case
    participant Domain as Domain Model
    participant Repo as Repository
    participant DB as Database
    
    GPT->>API: Request to /accounts/123
    API->>Router: Route request
    Router->>UseCase: getAccount(123)
    UseCase->>Repo: findById(123)
    Repo->>DB: Query
    DB-->>Repo: Raw data
    Repo-->>UseCase: Account entity
    UseCase-->>Router: Account DTO
    Router-->>API: JSON response
    API-->>GPT: HTTP response
```

## Database Selection Decision Tree

```mermaid
graph TD
    A[New Automation] --> B{Data Structure Type?}
    
    B -->|Relational| C{Need ACID?}
    C -->|Yes| D[PostgreSQL]
    C -->|No| E{High write throughput?}
    E -->|Yes| F[MongoDB]
    E -->|No| D
    
    B -->|Document| F
    
    B -->|Key-Value| G{Need persistence?}
    G -->|Yes| H{Serverless?}
    G -->|No| I[Redis]
    
    H -->|Yes| J[DynamoDB]
    H -->|No| K{Need complex queries?}
    K -->|Yes| D
    K -->|No| F
    
    B -->|Search| L[Elasticsearch]
```

## Deployment Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        A1[GPT Models]
        A2[Console Users]
    end
    
    subgraph "API Gateway"
        B[API Gateway/Load Balancer]
    end
    
    subgraph "Application Layer"
        B --> C1[API Server 1]
        B --> C2[API Server 2]
        B --> C3[API Server n...]
    end
    
    subgraph "Persistence Layer"
        C1 --> D1[(Primary Database)]
        C2 --> D1
        C3 --> D1
        
        D1 --> D2[(Read Replica)]
        
        C1 --> E1[(Service-Specific DB)]
        C2 --> E2[(Service-Specific DB)]
        C3 --> E3[(Service-Specific DB)]
    end
    
    subgraph "Supporting Services"
        F1[Cache]
        F2[Message Queue]
        F3[Search Index]
        F4[File Storage]
    end
```

## Security Architecture

```mermaid
graph TD
    A[Client Request] --> B{Has API Key?}
    B -->|No| C[Reject]
    B -->|Yes| D{Validate API Key}
    D -->|Invalid| C
    D -->|Valid| E{Check Rate Limit}
    E -->|Exceeded| F[Throttle]
    E -->|Within Limit| G{Check Permissions}
    G -->|Unauthorized| H[Forbidden]
    G -->|Authorized| I[Process Request]
    
    I --> J[Generate Audit Log]
    I --> K[Return Response]
```
