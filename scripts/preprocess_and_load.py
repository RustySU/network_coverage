#!/usr/bin/env python3
"""Script to preprocess CSV and then load it for maximum efficiency."""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import typer

from app.infrastructure.data_loader import load_data
from app.infrastructure.database import create_data_loading_session
from scripts.preprocess_csv import preprocess_csv

app = typer.Typer(help="Preprocess CSV and load data for maximum efficiency")


@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        help="Input CSV file to preprocess and load",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_file: Path | None = typer.Argument(
        None,
        help="Output CSV file path (default: preprocessed_<input_name>.csv)",
    ),
    convert_coordinates: bool = typer.Option(
        True,
        "--convert-coordinates/--no-convert-coordinates",
        "-c/-nc",
        help="Convert Lambert 93 coordinates to GPS coordinates",
    ),
) -> None:
    """Preprocess CSV and load data for maximum efficiency.
    
    This script combines preprocessing and loading in one command for maximum efficiency.
    It first preprocesses the CSV file (validates data, converts coordinates) then loads
    the optimized data into the database.
    
    Examples:
        python scripts/preprocess_and_load.py data.csv
        python scripts/preprocess_and_load.py data.csv processed.csv --no-convert-coordinates
    """
    # Generate output filename if not provided
    if output_file is None:
        output_file = Path(f"preprocessed_{input_file.stem}.csv")

    asyncio.run(_preprocess_and_load(
        input_file,
        output_file,
        convert_coordinates
    ))


async def _preprocess_and_load(
    input_file: Path,
    output_file: Path,
    convert_coordinates: bool
) -> None:
    """Async function to preprocess and load data."""
    start_time = time.time()

    typer.echo("=" * 60)
    typer.echo("STEP 1: PREPROCESSING CSV")
    typer.echo("=" * 60)

    # Preprocess the CSV
    preprocess_csv(
        input_file,
        output_file,
        convert_coordinates
    )

    typer.echo("\n" + "=" * 60)
    typer.echo("STEP 2: LOADING PREPROCESSED DATA")
    typer.echo("=" * 60)

    typer.echo(f"Loading preprocessed data from {output_file}...")

    # Use data loading session factory (no SQLAlchemy echo)
    DataLoadingSessionLocal = create_data_loading_session()

    try:
        async with DataLoadingSessionLocal() as session:
            count = await load_data(str(output_file), session)
            typer.echo(f"Successfully loaded {count} mobile sites")
    except Exception as e:
        typer.echo(f"Error loading data: {e}", err=True)
        raise typer.Exit(1)

    end_time = time.time()
    total_elapsed_time = end_time - start_time

    typer.echo("\n" + "=" * 60)
    typer.echo("SUMMARY")
    typer.echo("=" * 60)
    typer.echo(f"Total time: {total_elapsed_time:.2f} seconds")
    typer.echo(f"Preprocessed file: {output_file}")
    typer.echo(f"Average speed: {count/total_elapsed_time:.1f} sites/second")
    typer.echo("=" * 60)


if __name__ == "__main__":
    app()
