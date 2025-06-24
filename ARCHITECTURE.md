# Mobile Coverage API - Architecture Documentation

## Overview

The Mobile Coverage API is a FastAPI-based service that provides mobile network coverage information for addresses in France. The application follows Domain-Driven Design (DDD) principles with clear separation of concerns across multiple layers.

## Architecture Principles

- **Domain-Driven Design (DDD)**: Clear separation between domain, application, and infrastructure layers
- **Clean Architecture**: Dependencies flow inward, with domain at the center
- **SOLID Principles**: Single responsibility, dependency inversion, and interface segregation
- **Async-First**: Built with async/await for better performance and scalability
- **Error Handling**: Comprehensive error handling with domain-specific exceptions
- **Docker-First**: Containerized deployment with Docker and Docker Compose

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Main App      │  │    Routes       │  │ Exception    │ │
│  │   (FastAPI)     │  │   (Endpoints)   │  │  Handlers    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Application Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Use Cases     │  │    Schemas      │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                   Domain Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Entities      │  │   Services      │  │ Repositories │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Database      │  │  Geocoding      │  │ Data Loader  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    External Services                        │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   PostgreSQL    │  │ French Gov API  │                   │
│  │   (PostGIS)     │  │  (Geocoding)    │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. API Layer (`app/main.py`, `app/routes.py`)

**Responsibilities:**
- HTTP request/response handling
- CORS configuration
- Global exception handling
- API documentation (OpenAPI/Swagger)
- Route definitions and endpoint handling

**Key Components:**
- FastAPI application instance (`main.py`)
- Route definitions (`routes.py`)
- Exception handlers (`exception_handlers.py`)
- CORS middleware
- API documentation generation

**Error Handling:**
```python
# app/exception_handlers.py
def register_exception_handlers(app):
    @app.exception_handler(RepositoryError)
    async def repository_exception_handler(request: Request, exc: RepositoryError):
        # Returns 503 for database errors
    
    @app.exception_handler(GeocodingError)
    async def geocoding_exception_handler(request: Request, exc: GeocodingError):
        # Returns 503 for geocoding service errors
    
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        # Returns 500 for domain errors
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Returns 500 for unexpected errors
```

### 2. Application Layer (`app/application/`)

**Responsibilities:**
- Application-specific business logic
- Request/response data transformation
- Use case orchestration

**Components:**

#### Use Cases (`use_cases.py`)
- `FindNearbySitesByAddressUseCase`: Main business logic for finding coverage
- Orchestrates geocoding and coverage lookup
- Handles error scenarios gracefully

#### Schemas (`schemas.py`)
- Pydantic models for API requests/responses
- Data validation and serialization
- Type safety for API contracts

### 3. Domain Layer (`app/domain/`)

**Responsibilities:**
- Core business logic and rules
- Domain entities and value objects
- Business services
- Repository interfaces

**Components:**

#### Entities (`entities.py`)
- `MobileSite`: Core business entity representing a mobile network site
- `Location`: Value object for geographic coordinates
- `Coverage`: Value object for technology coverage (2G, 3G, 4G)
- `Operator`: Enum for mobile operators (Orange, SFR, Bouygues, Free)

#### Services (`services.py`)
- `MobileCoverageService`: Domain service for coverage operations
- Business logic for finding nearby sites

#### Repositories (`repositories.py`)
- Abstract repository interfaces
- `MobileSiteRepository`: Interface for mobile site data access

#### Exceptions (`exceptions.py`)
- Domain-specific exceptions
- `DomainException`: Base domain exception
- `RepositoryError`: Database operation errors
- `GeocodingError`: External geocoding service errors

### 4. Infrastructure Layer (`app/infrastructure/`)

**Responsibilities:**
- External service integrations
- Database implementations
- Data persistence
- Technical concerns

**Components:**

#### Database (`database.py`, `models.py`)
- SQLAlchemy async configuration
- Database models and migrations
- Connection pooling and session management

#### Repositories (`repositories.py`)
- `SQLAlchemyMobileSiteRepository`: Concrete repository implementation
- PostgreSQL with PostGIS for spatial queries
- Async database operations

#### Geocoding Service (`geocoding_service.py`)
- `GeocodingService`: External API integration
- French government geocoding API
- Concurrent address geocoding
- Error handling and retry logic

#### Data Loader (`data_loader.py`)
- CSV data import functionality
- Batch processing for large datasets
- Data validation and transformation

## Data Flow

### 1. Coverage Lookup Request

```
Client Request
    ↓
FastAPI Router
    ↓
Use Case (FindNearbySitesByAddressUseCase)
    ↓
Geocoding Service (batch geocoding)
    ↓
Coverage Service (find nearby sites)
    ↓
Repository (spatial database query)
    ↓
Response (coverage information)
```

### 2. Error Handling Flow

```
Exception Occurs
    ↓
Domain Exception (RepositoryError, GeocodingError, etc.)
    ↓
Exception Handler (FastAPI)
    ↓
Structured Error Response
    ↓
Client receives appropriate HTTP status + error details
```

## Database Design

### Schema Overview

```sql
-- Mobile sites table with PostGIS spatial support
CREATE TABLE mobile_sites (
    id SERIAL PRIMARY KEY,
    operator VARCHAR(50) NOT NULL,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(POINT, 4326),  -- PostGIS spatial column
    has_2g BOOLEAN NOT NULL,
    has_3g BOOLEAN NOT NULL,
    has_4g BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Spatial index for performance
CREATE INDEX idx_mobile_sites_geom ON mobile_sites USING GIST (geom);
```

### Spatial Queries

The application uses PostGIS for efficient spatial queries:

```sql
-- Find sites within radius (example)
SELECT * FROM mobile_sites 
WHERE ST_DWithin(
    geom, 
    ST_SetSRID(ST_MakePoint($1, $2), 4326), 
    $3 * 1000  -- Convert km to meters
);
```

## External Integrations

### 1. French Government Geocoding API

- **URL**: `https://api-adresse.data.gouv.fr/search/`
- **Purpose**: Convert French addresses to GPS coordinates
- **Features**: 
  - Concurrent geocoding for multiple addresses
  - Confidence scoring for result quality
  - Automatic retry and error handling

### 2. PostgreSQL with PostGIS

- **Purpose**: Spatial database for mobile site storage
- **Features**:
  - Spatial indexing for fast geographic queries
  - Support for complex spatial operations
  - ACID compliance and data integrity

## Error Handling Strategy

### 1. Exception Hierarchy

```
DomainException (base)
├── RepositoryError (database issues)
├── GeocodingError (external service issues)
└── CoverageServiceError (business logic issues)
```

### 2. Error Response Strategy

- **Repository Errors**: Return 503 (Service Unavailable)
- **Geocoding Errors**: Return 503 (Service Unavailable)
- **Domain Errors**: Return 500 (Internal Server Error)
- **Unexpected Errors**: Return 500 (Internal Server Error)

### 3. Graceful Degradation

- Failed geocoding → Return empty coverage
- Database errors → Return empty coverage
- Partial failures → Return partial results

## Performance Considerations

### 1. Database Optimization

- **Spatial Indexing**: PostGIS spatial indexes for fast geographic queries
- **Connection Pooling**: SQLAlchemy async connection pooling
- **Query Optimization**: Efficient spatial queries with proper indexing

### 2. Concurrency

- **Async/Await**: Full async stack for better I/O performance
- **Concurrent Geocoding**: Batch geocoding with asyncio.gather()
- **Database Sessions**: Proper session management to avoid concurrency issues

### 3. Caching Strategy

- **No Caching**: Currently no caching implemented
- **Future Consideration**: Redis for geocoding results and coverage data

## Security Considerations

### 1. Input Validation

- Pydantic schemas for request validation
- Address sanitization and validation
- SQL injection prevention through ORM

### 2. CORS Configuration

- Currently allows all origins (`*`)
- Production should restrict to specific domains

### 3. Error Information

- Generic error messages to clients
- Detailed logging for debugging
- No sensitive information in error responses

## Deployment Architecture

### Docker Setup

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgis/postgis
    environment:
      POSTGRES_DB: mobile_coverage
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/mobile_coverage
```

### Environment Configuration

- **Development**: Debug mode, verbose logging
- **Production**: Optimized logging, proper error handling
- **Database**: Connection pooling, read replicas (future)

## Monitoring and Observability

### 1. Logging

- Standard Python logging
- Structured log messages
- Error tracking and debugging information

### 2. Health Checks

- Database connectivity checks
- External service availability
- Application health endpoints

### 3. Metrics (Future)

- Request/response times
- Error rates by type
- Database query performance
- Geocoding success rates

## Scalability Considerations

### 1. Horizontal Scaling

- Stateless application design
- Database connection pooling
- Load balancer ready

### 2. Database Scaling

- Read replicas for query distribution
- Connection pooling optimization
- Query performance monitoring

### 3. External Services

- Geocoding service rate limiting
- Retry mechanisms with exponential backoff
- Circuit breaker pattern (future)

## Future Enhancements

### 1. Caching Layer

- Redis for geocoding results
- Coverage data caching
- Distributed caching for scalability

### 2. Advanced Monitoring

- APM integration (e.g., New Relic, DataDog)
- Custom metrics and dashboards
- Alerting and notification systems

### 3. Performance Optimizations

- Database query optimization
- Response compression
- CDN integration for static assets

### 4. Security Enhancements

- API authentication and authorization
- Rate limiting
- Input sanitization improvements

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | Latest | Web framework |
| **Database** | PostgreSQL + PostGIS | 15+ | Spatial database |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Async** | asyncio | Built-in | Concurrency |
| **HTTP Client** | httpx | Latest | External API calls |
| **Validation** | Pydantic | Latest | Data validation |
| **Migrations** | Alembic | Latest | Database migrations |
| **Testing** | pytest | Latest | Testing framework |
| **Linting** | Ruff | Latest | Code quality |
| **Container** | Docker | Latest | Containerization |
| **Orchestration** | Docker Compose | Latest | Multi-service setup |

## Conclusion

The Mobile Coverage API follows modern architectural patterns with clear separation of concerns, comprehensive error handling, and scalability considerations. The DDD approach ensures maintainable and testable code, while the async-first design provides good performance characteristics for I/O-intensive operations.

The architecture supports future enhancements while maintaining simplicity and clarity in the current implementation. 