# Mobile Coverage API

A FastAPI-based backend application for mobile coverage data in France, following Domain-Driven Design (DDD) and Test-Driven Development (TDD) principles.

## Performance Rationale

This application uses PostgreSQL with PostGIS for data storage instead of in-memory solutions for the following performance reasons:

### Scale Requirements
- **Estimated Coverage**: ~77,147 mobile sites across France
- **Concurrent Users**: 15,000 agencies 
- **Simultaneous Requests**: All agencies potentially querying at the same time (15,000 agencies × 100 houses each)

### Why Database Over In-Memory
- **Concurrent Access**: Database provides efficient concurrent read access for multiple simultaneous requests
- **Spatial Indexing**: PostGIS spatial indexes enable fast geographic queries (O(log n) vs O(n) for in-memory)
- **Connection Pooling**: Database connection pooling handles high concurrent load efficiently
- **Scalability**: Database can be scaled horizontally if needed

### Performance Benefits
- **Spatial Queries**: PostGIS `ST_DWithin` with spatial indexes for efficient radius searches
- **Async Operations**: Non-blocking database operations with SQLAlchemy async
- **Optimized Queries**: Single query with 30km radius instead of multiple smaller queries
- **Connection Management**: Efficient connection pooling and session management

## Features

- **Nearby Search**: Find mobile sites near a given location with radius filtering
- **Operator Filtering**: Filter results by specific mobile operators (Orange, SFR, Bouygues)
- **Geographic Queries**: Uses PostGIS for efficient spatial queries
- **Async Support**: Built with SQLAlchemy async and FastAPI
- **Comprehensive Testing**: Full test coverage with pytest
- **Test Coverage**: 76%
- **Type Safety**: Full type hints with mypy validation
- **Code Quality**: Ruff for linting and formatting
- **Docker-First Development**: All commands run inside Docker containers


## Architecture

The application follows Domain-Driven Design (DDD) principles with clear separation of concerns:

```
app/
├── domain/           # Domain layer (entities, services, repositories)
├── application/      # Application layer (use cases, schemas)
├── infrastructure/   # Infrastructure layer (database, external services)
└── main.py          # FastAPI application entry point
```

### Domain Layer
- **Entities**: Core business objects (MobileSite, Location, Coverage, etc.)
- **Services**: Business logic and domain services
- **Repositories**: Abstract interfaces for data access

### Application Layer
- **Use Cases**: Application-specific business logic
- **Schemas**: Pydantic models for API requests/responses

### Infrastructure Layer
- **Database**: SQLAlchemy models and async session management
- **Repositories**: Concrete implementations of repository interfaces

## Technology Stack

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **Testing**: pytest with async support
- **Linting**: Ruff
- **Type Checking**: mypy
- **Package Management**: uv
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker & Docker Compose
- No local Python installation required!

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd mobile-coverage-api
```

### 2. Run the complete setup (recommended)
```bash
make setup
```

This single command will:
- Build Docker images
- Start all services
- Install dependencies
- Run database migrations
- Load CSV data
- Start the application

### 3. Access the API
- API Documentation: http://localhost:8000/docs
- Root Endpoint: http://localhost:8000/

## Development Workflow

All development commands run inside Docker containers, ensuring consistent environments across all developers.

### Starting the Environment
```bash
# Start all services (PostgreSQL + App)
make docker-up

# Check if services are running
docker-compose ps
```

### Development Commands

All commands run inside the Docker development container:

```bash
# Run tests
make test

# Code quality checks
make lint
make format
make type-check

# Database operations
make migrate
make reset-db
make load-preprocessed
make preprocess-csv
make preprocess-and-load
make debug-load-data
```

### Docker Commands

```bash
# Build images
make docker-build

# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs
```

## API Endpoints

### Root Endpoint
```http
GET /
```

### Health Endpoint
```http
GET /heatlh
```

### Find Nearby Sites
```http
POST /api/v1/nearby
Content-Type: application/json

[(
    id: "id1",
    address: "157 boulevard Mac Donald 75019 Paris"
), (
    id: "id4",
    address: "5 avenue Anatole France 75007 Paris"
), (
    id: "id5",
    address: "1 Bd de Parc, 77700 Coupvray"
),(
    id: "id6",
    address: "Place d'Armes, 78000 Versailles"
),(
    id: "id7",
    address: "7 Rue René Cassin, 51430 Bezannes"
),(
    id: "id8",
    address: "78 Le Poujol, 30125 L'Estréchure"
),

]

```

**Response:**
```json
[
    {
        "id": "id1", 
        "orange":{ "2G": true, "3G": true, "4G": false}, 
        "SFR":{"2G": true, "3G": true, "4G": true},
        "bouygues":{ "2G": true, "3G": true, "4G": false},
    },
    {
        "id": "id4",
        "orange":{"2G": true, "3G": true, "4G": false}, "bouygues":{ "2G": true, "3G": false, "4G": false},
        "SFR":{ "2G": true, "3G": true, "4G": false}
    }
]

```

## Testing

### Run all tests
```bash
make test
```

### Run specific test file
```bash
# for example
docker-compose exec app pytest tests/scripts/test_preprocessing.py -v
```

## Code Quality

### Linting
```bash
make lint
```

### Formatting
```bash
make format
```

### Type Checking
```bash
make type-check
```

## Database Management

### Apply migrations
```bash
make migrate
```

### Reset DB
```bash
make reset-db
```

### Load data
```bash
make load-preprocessed
make preprocess-csv
make preprocess-and-load
make debug-load-data
```

## Project Structure

```
├── app/
│   ├── domain/              # Domain layer
│   │   ├── entities.py      # Domain entities (MobileSite, Location, Coverage, Operator)
│   │   ├── repositories.py  # Repository interfaces
│   │   ├── services.py      # Domain services (MobileCoverageService)
│   │   └── exceptions.py    # Domain exceptions
│   ├── application/         # Application layer
│   │   ├── schemas.py       # Pydantic schemas (API request/response models)
│   │   └── use_cases.py     # Use cases (FindNearbySitesByAddressUseCase)
│   ├── infrastructure/      # Infrastructure layer
│   │   ├── database.py      # Database configuration
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── repositories.py  # Repository implementations
│   │   ├── data_loader.py   # CSV data loader
│   │   ├── geocode_service.py # Address geocoding service
│   │   └── coordinate_utils.py # Lambert 93 to GPS conversion
│   ├── config.py            # Application configuration
│   ├── exception_handlers.py # Exception handlers for FastAPI
│   ├── routes.py            # API routes
│   └── main.py              # FastAPI application
├── tests/                   # Test suite (organized by layers)
│   ├── application/         # Application layer tests
│   │   └── test_use_cases.py
│   ├── domain/              # Domain layer tests
│   │   └── test_domain_entities.py
│   ├── infrastructure/      # Infrastructure layer tests
│   │   ├── test_repository.py    # Combined unit & integration tests
│   │   ├── test_data_loader.py
│   │   ├── test_coordinate_utils.py
│   │   └── test_geocode_service.py # Geocoding service tests
│   ├── scripts/             # Script tests
│   │   └── test_preprocessing.py
│   └── test_routes.py       # API routes tests
├── resources/               # Data and documentation files
│   ├── 2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv
│   ├── Backend developer technical test.pdf
│   └── preprocessed_mobile_sites.csv
├── alembic/                 # Database migrations
│   ├── env.py               # Alembic environment
│   └── versions/            # Migration files
├── scripts/                 # Utility scripts
│   ├── load_data.py         # Data loading script
│   ├── preprocess_csv.py    # CSV preprocessing
│   ├── preprocess_and_load.py # Combined preprocessing and loading
│   ├── reset_db.py          # Database reset utility
│   └── setup.sh             # Setup script
├── docker-compose.yml       # Docker services (app + postgres + postgis)
├── Dockerfile               # Application container
├── pyproject.toml           # Project configuration (uv-based)
├── uv.lock                  # Dependency lock file
├── alembic.ini             # Alembic configuration
├── Makefile                 # Development tasks
└── README.md               # This file
```

## Docker Services

The project includes three Docker services:

1. **postgres**: PostgreSQL database with PostGIS extension
2. **app**: FastAPI application with hot reload

## Data Format

The application expects CSV data in the following format:

```csv
Operateur,x,y,2G,3G,4G
Orange,102980,6847973,1,1,0
SFR,103113,6848661,1,1,0
Bouygues,103114,6848664,1,1,1
```

- **Operateur**: Mobile operator (Orange, SFR, Bouygues)
- **x, y**: Coordinates in L93 projection
- **2G, 3G, 4G**: Coverage flags (1 = available, 0 = not available)

## Troubleshooting

### Container Issues
```bash
# Rebuild containers
make docker-down
make docker-build
make docker-up

# Check container logs
make docker-logs
```

### Database Issues
```bash
# Reset database
make reset-db
make migrate
make load-preprocessed
```