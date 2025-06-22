"""Domain entities for mobile coverage."""

from dataclasses import dataclass
from enum import Enum


class Operator(str, Enum):
    """Mobile network operators."""

    ORANGE = "Orange"
    SFR = "SFR"
    BOUYGUES = "Bouygues"
    FREE = "Free"


@dataclass
class Coverage:
    """Coverage information for a mobile site."""

    has_2g: bool
    has_3g: bool
    has_4g: bool


@dataclass
class Location:
    """Geographic location in GPS coordinates (WGS84)."""

    x: float  # longitude
    y: float  # latitude


@dataclass
class MobileSite:
    """Mobile site entity."""

    operator: Operator
    location: Location
    coverage: Coverage

    def __post_init__(self) -> None:
        """Validate the mobile site data."""
        if not isinstance(self.operator, Operator):
            raise ValueError("Invalid operator", self.operator)

        if not isinstance(self.location, Location):
            raise ValueError("Invalid location")

        if not isinstance(self.coverage, Coverage):
            raise ValueError("Invalid coverage")
