"""Exception handlers for the FastAPI application."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainException, GeocodingError, RepositoryError

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    
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