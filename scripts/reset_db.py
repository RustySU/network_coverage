#!/usr/bin/env python3
"""Reset database tables to include updated operator enum."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from app.infrastructure.database import Base, engine


async def reset_database():
    """Drop and recreate all tables."""
    print("Resetting database...")

    async with engine.begin() as conn:
        # Drop all tables
        await conn.execute(text("DROP TABLE IF EXISTS mobile_sites CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))

        # Recreate all tables with updated enum
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
