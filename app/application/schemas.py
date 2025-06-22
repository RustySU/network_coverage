"""Application schemas for request/response models."""

from pydantic import BaseModel, Field


class NearbyAddressRequestItem(BaseModel):
    """Request item for nearby address search."""

    id: str = Field(..., description="Unique identifier for the address")
    address: str = Field(..., description="Address to search for")


class CoverageInfo(BaseModel):
    """Coverage information for a mobile operator."""

    has_2g: bool = Field(..., alias="2G")
    has_3g: bool = Field(..., alias="3G")
    has_4g: bool = Field(..., alias="4G")

    model_config = {"populate_by_name": True}


class NearbyAddressResponseItem(BaseModel):
    """Response item for nearby address search."""

    id: str = Field(..., description="Unique identifier for the address")
    orange: CoverageInfo = Field(..., description="Orange coverage information")
    SFR: CoverageInfo = Field(..., description="SFR coverage information")
    bouygues: CoverageInfo = Field(..., description="Bouygues coverage information")
    free: CoverageInfo = Field(..., description="Free coverage information")
