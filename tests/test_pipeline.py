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


def test_large_file_shows_loading_message(tmp_path, monkeypatch):
    """Test that files >100MB show loading message."""
    import io
    import sys

    # Create a moderately sized CSV file
    # We'll mock the LARGE_FILE_THRESHOLD_MB to be smaller for testing
    file = tmp_path / "medium.csv"

    # Generate ~5MB file (much faster than 100MB)
    rows = 50_000
    with open(file, "w") as f:
        f.write("a,b,c,d,e,f,g,h,i,j\n")
        for i in range(rows):
            f.write(
                f"{i},{i * 2},{i * 3},{i * 4},{i * 5},{i * 6},{i * 7},{i * 8},{i * 9},{i * 10}\n"
            )

    # Mock LARGE_FILE_THRESHOLD_MB to be very small (1 MB)
    from file_converter.core import pipeline

    original_threshold = pipeline.LARGE_FILE_THRESHOLD_MB
    monkeypatch.setattr("file_converter.core.pipeline.LARGE_FILE_THRESHOLD_MB", 1)

    # Capture stderr where the message is printed
    captured_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        df = load_file(file)
        stderr_output = sys.stderr.getvalue()
    finally:
        sys.stderr = captured_stderr
        # Restore original threshold
        monkeypatch.setattr(
            "file_converter.core.pipeline.LARGE_FILE_THRESHOLD_MB", original_threshold
        )

    # Verify loading message was shown
    assert "Loading large file" in stderr_output
    assert "MB" in stderr_output

    # Verify data loaded correctly
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == rows
    assert df.shape[1] == 10
