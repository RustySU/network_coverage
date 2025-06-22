"""Domain-specific exceptions."""


class DomainException(Exception):
    """Base exception for domain errors."""

    pass


class RepositoryError(DomainException):
    """Exception raised when repository operations fail."""

    pass


class GeocodingError(DomainException):
    """Exception raised when geocoding operations fail."""

    pass


class CoverageServiceError(DomainException):
    """Exception raised when coverage service operations fail."""

    pass
