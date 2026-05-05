import pandas as pd

from file_converter.exporters.csv_exporter import export_csv
from file_converter.exporters.parquet_exporter import export_parquet


def test_export_csv_creates_file(tmp_path):
    """Test CSV export creates file with correct content."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    output = tmp_path / "out.csv"

    export_csv(df, output)

    assert output.exists()
    loaded = pd.read_csv(output)
    assert loaded.shape == (3, 1)
    assert list(loaded["a"]) == [1, 2, 3]


def test_export_csv_no_index(tmp_path):
    """Test CSV export excludes index column."""
    df = pd.DataFrame({"col1": [10, 20], "col2": [30, 40]})
    output = tmp_path / "test.csv"

    export_csv(df, output)

    loaded = pd.read_csv(output)
    assert list(loaded.columns) == ["col1", "col2"]
    assert loaded.shape == (2, 2)


def test_export_parquet_creates_file(tmp_path):
    """Test Parquet export creates file with correct content."""
    df = pd.DataFrame({"x": [1.5, 2.5, 3.5], "y": ["a", "b", "c"]})
    output = tmp_path / "out.parquet"

    export_parquet(df, output)

    assert output.exists()
    loaded = pd.read_parquet(output)
    assert loaded.shape == (3, 2)
    assert list(loaded.columns) == ["x", "y"]


def test_export_parquet_no_index(tmp_path):
    """Test Parquet export excludes index column."""
    df = pd.DataFrame({"data": [100, 200, 300]})
    output = tmp_path / "test.parquet"

    export_parquet(df, output)

    loaded = pd.read_parquet(output)
    assert list(loaded.columns) == ["data"]
    assert loaded.shape == (3, 1)
