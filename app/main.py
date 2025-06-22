"""Main FastAPI application."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.domain.exceptions import DomainException, GeocodingError, RepositoryError
from app.routes import router

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RepositoryError)
async def repository_exception_handler(request: Request, exc: RepositoryError) -> JSONResponse:
    """Handle repository errors."""
    logger.error(f"Repository error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=503, content={"detail": "Database service temporarily unavailable"}
    )


@app.exception_handler(GeocodingError)
async def geocoding_exception_handler(request: Request, exc: GeocodingError) -> JSONResponse:
    """Handle geocoding errors."""
    logger.error(f"Geocoding error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=503, content={"detail": "Geocoding service temporarily unavailable"}
    )


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle general domain errors."""
    logger.error(f"Domain error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include router
app.include_router(router)
