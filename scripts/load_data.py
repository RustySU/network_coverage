#!/usr/bin/env python3
"""Script to load CSV data into the database."""

import asyncio
import logging
import sys
import time
from pathlib import Path

import typer

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Disable SQLAlchemy verbose logging for better performance
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from app.infrastructure.data_loader import load_data
from app.infrastructure.database import create_data_loading_session

app = typer.Typer(help="Load CSV data into the database")


@app.command()
def main(
    csv_file: Path = typer.Argument(
        ...,
        help="Path to the CSV file to load",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Load CSV data into the database.
    
    This script loads mobile site data from a CSV file into the database.
    The CSV should have columns: Operateur, x, y, 2G, 3G, 4G
    Coordinates are in GPS coordinates (WGS84)
    
    Examples:
        python scripts/load_data.py data.csv
    """
    asyncio.run(_load_data(csv_file))


async def _load_data(csv_file: Path) -> None:
    """Async function to load data."""
    start_time = time.time()

    typer.echo(f"Loading data from {csv_file}...")

    # Use data loading session factory (no SQLAlchemy echo)
    DataLoadingSessionLocal = create_data_loading_session()

    try:
        async with DataLoadingSessionLocal() as session:
            count = await load_data(str(csv_file), session)

            typer.echo(f"Successfully loaded {count} mobile sites")
    except Exception as e:
        typer.echo(f"Error loading data: {e}", err=True)
        raise typer.Exit(1)

    end_time = time.time()
    elapsed_time = end_time - start_time

    typer.echo(f"Total time: {elapsed_time:.2f} seconds")
    typer.echo(f"Average speed: {count/elapsed_time:.1f} sites/second")


if __name__ == "__main__":
    app()
