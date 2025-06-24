"""Tests for CSV preprocessing functionality."""

import csv
import tempfile
from pathlib import Path

import pytest
import typer

from scripts.preprocess_csv import preprocess_csv


class TestPreprocessing:
    """Test CSV preprocessing functionality."""

    @pytest.fixture
    def sample_csv_file(self) -> Path:
        """Create a temporary CSV file with sample data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Operateur", "x", "y", "2G", "3G", "4G"])
            writer.writerow(["Orange", "102980", "6847973", "1", "1", "0"])
            writer.writerow(["SFR", "103113", "6848661", "1", "1", "0"])
            writer.writerow(["Bouygues", "103114", "6848664", "1", "1", "1"])
            writer.writerow(["Free", "112032", "6840427", "0", "1", "1"])
            return Path(f.name)

    @pytest.fixture
    def csv_with_empty_lines(self) -> Path:
        """Create a CSV file with empty lines and invalid data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Operateur", "x", "y", "2G", "3G", "4G"])
            writer.writerow(["Orange", "102980", "6847973", "1", "1", "0"])
            writer.writerow([])  # Empty line
            writer.writerow(["SFR", "103113", "6848661", "1", "1", "0"])
            writer.writerow(["", "", "", "", "", ""])  # Empty values
            writer.writerow(
                ["InvalidOperator", "103114", "6848664", "1", "1", "1"]
            )  # Invalid operator
            writer.writerow(
                ["Bouygues", "invalid", "6848664", "1", "1", "1"]
            )  # Invalid coordinates
            writer.writerow(
                ["Free", "112032", "6840427", "2", "1", "1"]
            )  # Invalid coverage flag
            return Path(f.name)

    def test_preprocess_csv_basic(self, sample_csv_file: Path) -> None:
        """Test basic CSV preprocessing without coordinate conversion."""
        output_file = Path("test_output.csv")

        try:
            preprocess_csv(sample_csv_file, output_file, convert_coordinates=False)

            # Check that output file was created
            assert output_file.exists()

            # Read and verify the output
            with open(output_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have 4 valid rows
            assert len(rows) == 4

            # Check that coordinates are not converted
            assert "x" in rows[0]
            assert "y" in rows[0]
            assert "longitude" not in rows[0]
            assert "latitude" not in rows[0]

            # Check operators
            operators = [row["Operateur"] for row in rows]
            assert operators == ["Orange", "SFR", "Bouygues", "Free"]

        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()

    def test_preprocess_csv_with_coordinate_conversion(
        self, sample_csv_file: Path
    ) -> None:
        """Test CSV preprocessing with coordinate conversion."""
        output_file = Path("test_output_converted.csv")

        try:
            preprocess_csv(sample_csv_file, output_file, convert_coordinates=True)

            # Check that output file was created
            assert output_file.exists()

            # Read and verify the output
            with open(output_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have 4 valid rows
            assert len(rows) == 4

            # Check that coordinates are converted
            assert "longitude" in rows[0]
            assert "latitude" in rows[0]
            assert "x" not in rows[0]
            assert "y" not in rows[0]

            # Check that coordinates are valid floats
            for row in rows:
                longitude = float(row["longitude"])
                latitude = float(row["latitude"])
                assert -180 <= longitude <= 180
                assert -90 <= latitude <= 90

        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()

    def test_preprocess_csv_with_empty_lines(self, csv_with_empty_lines: Path) -> None:
        """Test CSV preprocessing with empty lines and invalid data."""
        output_file = Path("test_output_cleaned.csv")

        try:
            preprocess_csv(csv_with_empty_lines, output_file, convert_coordinates=False)

            # Check that output file was created
            assert output_file.exists()

            # Read and verify the output
            with open(output_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have only 2 valid rows (Orange and SFR)
            # InvalidOperator, invalid coordinates, and invalid coverage should be skipped
            assert len(rows) == 2

            # Check operators
            operators = [row["Operateur"] for row in rows]
            assert operators == ["Orange", "SFR"]

        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()

    def test_preprocess_csv_file_not_found(self) -> None:
        """Test preprocessing with non-existent input file."""
        output_file = Path("test_output.csv")

        with pytest.raises((SystemExit, typer.Exit)):
            preprocess_csv(Path("non_existent_file.csv"), output_file)

    def test_preprocess_csv_invalid_coordinates(self) -> None:
        """Test preprocessing with invalid coordinates."""
        # Create CSV with invalid coordinates
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Operateur", "x", "y", "2G", "3G", "4G"])
            writer.writerow(["Orange", "invalid", "6847973", "1", "1", "0"])
            input_file = Path(f.name)

        output_file = Path("test_output_invalid.csv")

        try:
            preprocess_csv(input_file, output_file, convert_coordinates=True)

            # Should skip the invalid row
            with open(output_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have 0 valid rows
            assert len(rows) == 0

        finally:
            # Clean up
            input_file.unlink()
            if output_file.exists():
                output_file.unlink()
