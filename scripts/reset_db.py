#!/usr/bin/env python3
"""Reset database tables to include updated operator enum."""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
