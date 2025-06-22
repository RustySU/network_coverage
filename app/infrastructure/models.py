"""SQLAlchemy models for the database."""

import uuid
from typing import cast

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, Float, String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database import Base


class MobileSiteModel(Base):
    """Database model for mobile sites."""

    __tablename__ = "mobile_sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    geom = Column(
        Geometry("POINT", srid=4326), nullable=False
    )  # WGS84 for GPS coordinates
    has_2g = Column(Boolean, nullable=False, default=False)
    has_3g = Column(Boolean, nullable=False, default=False)
    has_4g = Column(Boolean, nullable=False, default=False)

    @property
    def x_value(self) -> float:
        return cast(float, self.x)

    @property
    def y_value(self) -> float:
        return cast(float, self.y)

    @property
    def operator_value(self) -> str:
        return cast(str, self.operator)

    @property
    def has_2g_value(self) -> bool:
        return cast(bool, self.has_2g)

    @property
    def has_3g_value(self) -> bool:
        return cast(bool, self.has_3g)

    @property
    def has_4g_value(self) -> bool:
        return cast(bool, self.has_4g)

    def __repr__(self) -> str:
        return f"<MobileSiteModel(id={self.id}, operator={self.operator})>"
