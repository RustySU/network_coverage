#!/usr/bin/env python3
"""Script to preprocess CSV file for faster loading."""

import csv
import time
from pathlib import Path

from app.infrastructure.coordinate_utils import lamber93_to_gps
import typer

app = typer.Typer(help="Preprocess CSV file for faster loading")



@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        help="Input CSV file to preprocess",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_file: Path = typer.Argument(
        ...,
        help="Output CSV file path",
    ),
    convert_coordinates: bool = typer.Option(
        False,
        "--convert-coordinates",
        "-c",
        help="Convert Lambert 93 coordinates to GPS coordinates",
    ),
) -> None:
    """Preprocess CSV file for faster loading.
    
    This script validates and optionally converts coordinates in CSV files
    to prepare them for faster database loading.
    
    Examples:
        python scripts/preprocess_csv.py input.csv output.csv
        python scripts/preprocess_csv.py input.csv output.csv --convert-coordinates
    """
    preprocess_csv(input_file, output_file, convert_coordinates)


def preprocess_csv(
    input_file: Path,
    output_file: Path,
    convert_coordinates: bool = False
) -> None:
    """Preprocess CSV file for faster loading."""
    start_time = time.time()

    typer.echo(f"Preprocessing {input_file}...")

    # Valid operators
    valid_operators = {'Orange', 'SFR', 'Bouygues', 'Free'}

    if not input_file.exists():
        typer.echo(f"Input file not found: {input_file}", err=True)
        raise typer.Exit(1)

    processed_count = 0
    skipped_count = 0
    error_count = 0

    with open(input_file, encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)

        # Define output columns
        if convert_coordinates:
            fieldnames = ['Operateur', 'longitude', 'latitude', '2G', '3G', '4G']
        else:
            fieldnames = ['Operateur', 'x', 'y', '2G', '3G', '4G']

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
            # Skip empty rows (all values are empty strings, whitespace, or None)
            if not row or all(not value or not str(value).strip() for value in row.values()):
                skipped_count += 1
                continue

            try:
                # Validate operator
                operator = row['Operateur'].strip()
                if operator not in valid_operators:
                    error_count += 1
                    continue

                # Validate coordinates
                try:
                    x = float(row['x'])
                    y = float(row['y'])
                except (ValueError, KeyError) as e:
                    error_count += 1
                    continue

                # Validate coverage flags
                try:
                    has_2g = int(row['2G'])
                    has_3g = int(row['3G'])
                    has_4g = int(row['4G'])

                    if not all(flag in (0, 1) for flag in [has_2g, has_3g, has_4g]):
                        error_count += 1
                        continue

                except (ValueError, KeyError) as e:
                    error_count += 1
                    continue

                # Convert coordinates if requested
                if convert_coordinates:
                    try:
                        longitude, latitude = lamber93_to_gps(x, y)
                        output_row = {
                            'Operateur': operator,
                            'longitude': longitude,
                            'latitude': latitude,
                            '2G': has_2g,
                            '3G': has_3g,
                            '4G': has_4g,
                        }
                    except Exception as e:
                        error_count += 1
                        continue
                else:
                    output_row = {
                        'Operateur': operator,
                        'x': x,
                        'y': y,
                        '2G': has_2g,
                        '3G': has_3g,
                        '4G': has_4g,
                    }

                writer.writerow(output_row)
                processed_count += 1

            except Exception as e:
                error_count += 1
                continue

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Show summary
    typer.echo("\nPreprocessing complete!")
    typer.echo(f"Processed: {processed_count} valid rows")
    typer.echo(f"Skipped: {skipped_count} empty rows")
    typer.echo(f"Errors: {error_count} invalid rows")
    typer.echo(f"Output file: {output_file}")
    typer.echo(f"Total time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    app()
