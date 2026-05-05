"""
End-to-end CLI tests.
Tests CLI interface, exit codes, error handling, and user-facing behavior.
"""

import subprocess
import sys

import pandas as pd
import pytest


@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV file for testing."""
    file = tmp_path / "sample.csv"
    df = pd.DataFrame(
        {"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35], "city": ["NYC", "LA", "Chicago"]}
    )
    df.to_csv(file, index=False)
    return file


@pytest.fixture
def sample_json(tmp_path):
    """Create sample JSON file for testing."""
    import json

    file = tmp_path / "sample.json"
    data = [{"id": 1, "value": 100}, {"id": 2, "value": 200}]
    file.write_text(json.dumps(data))
    return file


def run_convert_cli(args, cwd=None):
    """Run convert CLI and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, "-m", "file_converter.cli"] + args
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_no_args_shows_error(self):
        """Test that running without input argument returns error code."""
        exit_code, stdout, stderr = run_convert_cli([])
        assert exit_code == 1
        assert "Error" in stderr or "Error" in stdout

    def test_cli_list_formats(self):
        """Test --list-formats argument."""
        exit_code, stdout, stderr = run_convert_cli(["--list-formats"])
        assert exit_code == 0
        assert ".csv" in stdout
        assert ".parquet" in stdout
        assert ".json" in stdout

    def test_cli_missing_input_file_returns_error(self):
        """Test that missing input file returns error code 1."""
        exit_code, stdout, stderr = run_convert_cli(["nonexistent.csv"])
        assert exit_code == 1
        assert "Error" in stderr


class TestCLIConversion:
    """Test actual conversion workflows."""

    def test_csv_to_parquet_default(self, sample_csv, tmp_path, monkeypatch):
        """Test default conversion from CSV to Parquet."""
        from file_converter.cli import main

        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", sample_csv.parent)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)
        monkeypatch.setattr("sys.argv", ["convert", str(sample_csv)])

        exit_code = main()

        assert exit_code == 0

        output_file = tmp_path / "sample.parquet"
        assert output_file.exists()

    def test_csv_to_csv_explicit(self, sample_csv, tmp_path, monkeypatch):
        """Test explicit CSV to CSV conversion."""
        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", sample_csv.parent)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        output_file = tmp_path / "result.csv"
        exit_code, stdout, stderr = run_convert_cli(
            [str(sample_csv), str(output_file)], cwd=tmp_path
        )

        assert exit_code == 0
        assert output_file.exists()

        df = pd.read_csv(output_file)
        assert df.shape == (3, 3)

    def test_json_to_csv(self, sample_json, tmp_path, monkeypatch):
        """Test JSON to CSV conversion."""
        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", sample_json.parent)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        output_file = tmp_path / "output.csv"
        exit_code, stdout, stderr = run_convert_cli(
            [str(sample_json), str(output_file)], cwd=tmp_path
        )

        assert exit_code == 0
        assert output_file.exists()


class TestCLIPreview:
    """Test --preview functionality."""

    def test_preview_shows_dataset_info(self, sample_csv, tmp_path, monkeypatch):
        """Test that --preview displays dataset structure."""
        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", sample_csv.parent)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        exit_code, stdout, stderr = run_convert_cli([str(sample_csv), "--preview"], cwd=tmp_path)

        assert exit_code == 0
        assert "Rows: 3" in stdout
        assert "Columns: 3" in stdout
        assert "name" in stdout
        assert "age" in stdout


class TestCLIDropEmpty:
    """Test --drop-empty functionality."""

    def test_drop_empty_removes_null_columns(self, tmp_path, monkeypatch):
        """Test that --drop-empty removes columns with all NaN values."""
        # Create CSV with empty column
        csv_file = tmp_path / "data_with_empty.csv"
        df = pd.DataFrame(
            {"col1": [1, 2, 3], "empty_col": [None, None, None], "col2": ["a", "b", "c"]}
        )
        df.to_csv(csv_file, index=False)

        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", tmp_path)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        output_file = tmp_path / "result.csv"
        exit_code, stdout, stderr = run_convert_cli(
            [str(csv_file), str(output_file), "--drop-empty"], cwd=tmp_path
        )

        assert exit_code == 0

        result = pd.read_csv(output_file)
        assert list(result.columns) == ["col1", "col2"]


class TestCLIErrorHandling:
    """Test CLI error handling and exit codes."""

    def test_unsupported_output_format(self, sample_csv, tmp_path, monkeypatch):
        """Test that unsupported output format returns error code 1."""
        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", sample_csv.parent)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        output_file = tmp_path / "output.xyz"
        exit_code, stdout, stderr = run_convert_cli(
            [str(sample_csv), str(output_file)], cwd=tmp_path
        )

        assert exit_code == 1
        assert "Unsupported output format" in stderr

    def test_malformed_json_returns_error(self, tmp_path, monkeypatch):
        """Test that malformed JSON file returns error code 1."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")

        monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", tmp_path)
        monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", tmp_path)

        exit_code, stdout, stderr = run_convert_cli([str(bad_json)], cwd=tmp_path)

        assert exit_code == 1
        assert "Error" in stderr
