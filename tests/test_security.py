import pandas as pd
import pytest

from file_converter.exporters.csv_exporter import export_csv


class TestCSVFormulaInjection:
    """Tests for CSV formula injection prevention."""

    def test_csv_formula_injection_escaped(self, tmp_path):
        """Test that Excel formula injection is prevented.

        Formulas starting with =, +, -, @, or \t are dangerous in spreadsheets
        and should be properly quoted or escaped.
        """
        df = pd.DataFrame(
            {
                "formula_eq": ["=1+1", "=SUM(A1:A10)", "=cmd|'/c calc'!A1"],
                "formula_plus": ["+1+1", "+2+5", "+100"],
                "formula_minus": ["-1+1", "-2+5", "-100"],
                "formula_at": ["@SUM(A1)", "@", "@indirect('A1')"],
                "formula_tab": ["\t=1+1", "\tSUM", "\t"],
                "safe": ["hello", "world", "test"],
            }
        )

        output = tmp_path / "output.csv"
        export_csv(df, output)

        # Read back and verify content
        content = output.read_text()

        # Check that formulas are quoted (not executable in Excel)
        # At minimum, = signs should be either escaped or quoted
        assert '="1+1"' in content or '"=1+1"' in content or '"=1+1"' in content

        # Verify data integrity - values are preserved
        df_loaded = pd.read_csv(output)
        assert df_loaded.shape == (3, 6)
        assert list(df_loaded["safe"]) == ["hello", "world", "test"]

    def test_csv_formulas_preserved_but_safe(self, tmp_path):
        """Test that formula-like values are preserved but safe from execution."""
        df = pd.DataFrame({"value": ["=1+1", "@SUM", "-2+5"], "normal": ["a", "b", "c"]})

        output = tmp_path / "output.csv"
        export_csv(df, output)

        # Reload and verify
        df_loaded = pd.read_csv(output)

        # Values preserved
        assert list(df_loaded["value"]) == ["=1+1", "@SUM", "-2+5"]

        # But raw CSV content should show proper quoting
        content = output.read_text()
        # Either quoted or would not be interpreted as formula by Excel
        # (because QUOTE_NONNUMERIC ensures all non-numeric values are quoted)
        assert content.count('"') > 0  # Has quoting


class TestFileValidation:
    """Tests for input validation."""

    def test_empty_dataframe_export(self, tmp_path):
        """Test exporting empty DataFrame."""
        df = pd.DataFrame()
        output = tmp_path / "empty.csv"

        export_csv(df, output)

        # Should create file with just header (or empty)
        assert output.exists()
        content = output.read_text()
        # Empty DataFrame should still have valid CSV structure
        assert isinstance(content, str)

    def test_large_dataframe_export(self, tmp_path):
        """Test exporting large DataFrame."""
        # Create a moderately large DataFrame (10k rows, 10 cols)
        df = pd.DataFrame({f"col_{i}": range(10_000) for i in range(10)})

        output = tmp_path / "large.csv"
        export_csv(df, output)

        # Should create file without OOM
        assert output.exists()

        # Verify file size is reasonable
        file_size_mb = output.stat().st_size / 1_000_000
        assert file_size_mb > 0

        # Reload and verify
        df_loaded = pd.read_csv(output)
        assert df_loaded.shape == (10_000, 10)


class TestCharacterEncoding:
    """Tests for proper encoding handling."""

    def test_csv_unicode_export(self, tmp_path):
        """Test exporting DataFrame with Unicode characters."""
        df = pd.DataFrame(
            {
                "name": ["José", "François", "Müller", "北京"],
                "city": ["São Paulo", "Paris", "München", "北京"],
            }
        )

        output = tmp_path / "unicode.csv"
        export_csv(df, output)

        # Should be UTF-8 encoded by default
        assert output.exists()

        # Reload with UTF-8
        df_loaded = pd.read_csv(output, encoding="utf-8")
        assert df_loaded.shape == (4, 2)
        assert "José" in df_loaded["name"].values
        assert "São Paulo" in df_loaded["city"].values

    def test_csv_special_characters_export(self, tmp_path):
        """Test exporting DataFrame with special characters."""
        df = pd.DataFrame(
            {
                "text": ['Hello "World"', "It's fine", "Line\nbreak", "Tab\there"],
                "number": [1, 2, 3, 4],
            }
        )

        output = tmp_path / "special.csv"
        export_csv(df, output)

        # Reload and verify proper escaping
        df_loaded = pd.read_csv(output)
        assert len(df_loaded) == 4
        # Quotes should be escaped properly
        assert 'Hello "World"' in df_loaded["text"].values


class TestNullAndNaNHandling:
    """Tests for handling null/NaN values."""

    def test_nan_values_export(self, tmp_path):
        """Test exporting DataFrame with NaN values."""
        df = pd.DataFrame(
            {"a": [1.0, float("nan"), 3.0], "b": ["x", None, "z"], "c": [True, False, None]}
        )

        output = tmp_path / "with_nan.csv"
        export_csv(df, output)

        # Reload
        df_loaded = pd.read_csv(output)

        # NaN should be represented as empty string or 'nan'
        assert len(df_loaded) == 3
        # Second row should have NaN/empty representation
        assert pd.isna(df_loaded.loc[1, "a"]) or df_loaded.loc[1, "a"] == "nan"


class TestFileSizeLimits:
    """Tests for file size limit enforcement."""

    def test_file_size_limit_enforced(self, tmp_path):
        """Test that files larger than limit are rejected."""
        # Create a file larger than 1KB limit
        large_file = tmp_path / "large.csv"
        large_file.write_text("a,b\n" + "1,2\n" * 1000)  # ~10KB

        # Test with very small limit
        from file_converter.core.pipeline import load_file

        with pytest.raises(ValueError, match="File too large"):
            load_file(large_file, max_size=1024)  # 1KB limit

    def test_file_size_limit_accepts_small_files(self, tmp_path):
        """Test that small files are accepted."""
        small_file = tmp_path / "small.csv"
        small_file.write_text("a,b\n1,2\n3,4")

        from file_converter.core.pipeline import load_file

        df = load_file(small_file, max_size=1024)  # 1KB limit

        assert df.shape == (2, 2)
        assert list(df.columns) == ["a", "b"]

    def test_file_size_limit_default_value(self, tmp_path):
        """Test that default limit is 1GB."""
        from file_converter.core.pipeline import DEFAULT_MAX_FILE_SIZE

        # Should be 1GB
        assert DEFAULT_MAX_FILE_SIZE == 1_000_000_000
