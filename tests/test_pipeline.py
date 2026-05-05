import pandas as pd
import pytest

from file_converter.core.pipeline import load_file


def test_load_csv_success(tmp_path):
    file = tmp_path / "data.csv"
    file.write_text("a,b\n1,2\n3,4")

    df = load_file(file)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)


def test_load_csv_with_string_path(tmp_path):
    """Test that load_file accepts both Path and str types."""
    file = tmp_path / "data.csv"
    file.write_text("x,y\n10,20\n30,40")

    # Pass as string instead of Path
    df = load_file(str(file))

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert list(df.columns) == ["x", "y"]


def test_load_missing_file(tmp_path):
    file = tmp_path / "missing.csv"

    with pytest.raises(ValueError, match="does not exist"):
        load_file(file)


def test_load_unsupported_extension(tmp_path):
    file = tmp_path / "data.xyz"
    file.write_text("dummy")

    with pytest.raises(ValueError, match="Unsupported input format"):
        load_file(file)


def test_load_error_message_lists_formats(tmp_path):
    """Test that error message for unsupported format lists available options."""
    file = tmp_path / "data.abc"
    file.write_text("dummy")

    with pytest.raises(ValueError) as exc_info:
        load_file(file)

    error_msg = str(exc_info.value)
    assert ".csv" in error_msg
    assert ".parquet" in error_msg
    assert ".json" in error_msg
