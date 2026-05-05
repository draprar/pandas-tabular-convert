"""
Comprehensive loader tests for all supported formats.
"""

import json

import pandas as pd
import pytest

from file_converter.loaders.csv_loader import CSVLoader
from file_converter.loaders.excel_loader import ExcelLoader
from file_converter.loaders.json_loader import JSONLoader
from file_converter.loaders.parquet_loader import ParquetLoader
from file_converter.loaders.pickle_loader import PickleLoader


class TestCSVLoader:
    """Tests for CSV loader."""

    def test_load_simple_csv(self, tmp_path):
        """Test loading simple CSV file."""
        file = tmp_path / "data.csv"
        file.write_text("name,age\nAlice,30\nBob,25")

        loader = CSVLoader()
        df = loader.load(file)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["name", "age"]
        assert list(df["name"]) == ["Alice", "Bob"]

    def test_load_csv_with_special_chars(self, tmp_path):
        """Test loading CSV with special characters and Unicode."""
        file = tmp_path / "data.csv"
        file.write_text("name,city\nMaria,São Paulo\nJörg,München", encoding="utf-8")

        loader = CSVLoader()
        df = loader.load(file)

        assert df.shape == (2, 2)
        assert "São Paulo" in df["city"].values


class TestExcelLoader:
    """Tests for Excel loader."""

    def test_load_excel(self, tmp_path):
        """Test loading Excel file."""
        file = tmp_path / "data.xlsx"
        df_original = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        df_original.to_excel(file, index=False)

        loader = ExcelLoader()
        df = loader.load(file)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["col1", "col2"]


class TestJSONLoader:
    """Tests for JSON loader."""

    def test_load_simple_json(self, tmp_path):
        """Test loading simple JSON array."""
        file = tmp_path / "data.json"
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        file.write_text(json.dumps(data))

        loader = JSONLoader()
        df = loader.load(file)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["id", "name"]

    def test_load_json_no_auto_datetime(self, tmp_path, monkeypatch):
        """Test that datetime parsing is OFF by default (safe mode)."""
        file = tmp_path / "data.json"
        data = [
            {"event": "login", "timestamp": "2024-01-15 10:00:00"},
            {"event": "logout", "timestamp": "2024-01-15 11:00:00"},
        ]
        file.write_text(json.dumps(data))

        # Ensure env var is NOT set
        monkeypatch.delenv("PARSE_JSON_DATETIME", raising=False)

        loader = JSONLoader()
        df = loader.load(file)

        # Timestamp should remain text-like and must not be converted to datetime.
        # Depending on pandas version/config, text columns may use object or StringDtype.
        assert pd.api.types.is_string_dtype(df["timestamp"])
        assert not pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert isinstance(df["timestamp"].iloc[0], str)
        assert list(df["timestamp"]) == [
            "2024-01-15 10:00:00",
            "2024-01-15 11:00:00",
        ]

    def test_load_json_with_auto_datetime_enabled(self, tmp_path, monkeypatch):
        """Test that datetime parsing works when explicitly enabled."""
        file = tmp_path / "data.json"
        data = [
            {
                "event": "login",
                "created_date": "2024-01-15",
                "modified_time": "2024-01-15 10:00:00",
            },
        ]
        file.write_text(json.dumps(data))

        monkeypatch.setenv("PARSE_JSON_DATETIME", "1")

        loader = JSONLoader()
        df = loader.load(file)

        # Both columns should be parsed as datetime
        assert pd.api.types.is_datetime64_any_dtype(df["created_date"])
        assert pd.api.types.is_datetime64_any_dtype(df["modified_time"])

    def test_load_json_datetime_coercion_safe(self, tmp_path, monkeypatch):
        """Test that datetime coercion with errors='coerce' is safe."""
        file = tmp_path / "data.json"
        # "runtime" contains non-date values - should NOT be affected without env var
        data = [
            {"event": "video", "runtime": "120 mins"},
            {"event": "movie", "runtime": "invalid_date"},
        ]
        file.write_text(json.dumps(data))

        monkeypatch.delenv("PARSE_JSON_DATETIME", raising=False)

        loader = JSONLoader()
        df = loader.load(file)

        # runtime should stay text-like and not be converted to datetime
        assert pd.api.types.is_string_dtype(df["runtime"])
        assert not pd.api.types.is_datetime64_any_dtype(df["runtime"])
        assert list(df["runtime"]) == ["120 mins", "invalid_date"]


class TestParquetLoader:
    """Tests for Parquet loader."""

    def test_load_parquet(self, tmp_path):
        """Test loading Parquet file."""
        file = tmp_path / "data.parquet"
        df_original = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.5, 30.5]})
        df_original.to_parquet(file, index=False)

        loader = ParquetLoader()
        df = loader.load(file)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ["id", "value"]


class TestPickleLoader:
    """Tests for Pickle loader (with security checks)."""

    def test_pickle_disabled_by_default(self, tmp_path, monkeypatch):
        """Test that pickle loading is disabled without UNSAFE_PICKLE env var."""
        file = tmp_path / "data.pkl"
        df_original = pd.DataFrame({"data": [1, 2, 3]})
        df_original.to_pickle(file)

        # Ensure env var is NOT set (cleanup from previous tests)
        monkeypatch.delenv("UNSAFE_PICKLE", raising=False)

        loader = PickleLoader()

        # Should raise RuntimeError when env var is not set
        with pytest.raises(RuntimeError, match="Pickle loading disabled"):
            loader.load(file)

    def test_pickle_enabled_with_env_var(self, tmp_path, monkeypatch):
        """Test that pickle loading works when UNSAFE_PICKLE=1."""
        file = tmp_path / "data.pkl"
        df_original = pd.DataFrame({"x": [1, 2], "y": ["a", "b"]})
        df_original.to_pickle(file)

        monkeypatch.setenv("UNSAFE_PICKLE", "1")

        loader = PickleLoader()
        df = loader.load(file)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)

    def test_pickle_enabled_with_true_variant(self, tmp_path, monkeypatch):
        """Test that pickle works with UNSAFE_PICKLE=true."""
        file = tmp_path / "data.pkl"
        df_original = pd.DataFrame({"col": [100, 200]})
        df_original.to_pickle(file)

        monkeypatch.setenv("UNSAFE_PICKLE", "true")

        loader = PickleLoader()
        df = loader.load(file)

        assert df.shape == (2, 1)
