import argparse
import sys
from pathlib import Path

from file_converter.core.pipeline import LOADERS, load_file
from file_converter.exporters.csv_exporter import export_csv
from file_converter.exporters.parquet_exporter import export_parquet

DATA_INPUT_DIR = Path("data/input")
DATA_OUTPUT_DIR = Path("data/output")


def resolve_input_path(input_arg: str) -> Path:
    """
    Resolve input file path.

    Resolution order:
    1. If absolute/relative path exists -> use it
    2. Otherwise search in data/input/

    Args:
        input_arg: Input file path or filename.

    Returns:
        Resolved Path object.

    Raises:
        FileNotFoundError: If file cannot be found.
    """
    input_path = Path(input_arg)

    if input_path.exists():
        return input_path

    alt_path = DATA_INPUT_DIR / input_arg
    if alt_path.exists():
        return alt_path

    raise FileNotFoundError(f"Input file does not exist: {input_arg}")


def resolve_output_path(output_arg: str | None, input_path: Path) -> Path:
    """
    Resolve output file path.

    Rules:
    - If provided:
        - If only filename -> save to data/output/
        - If full path -> use as-is
    - If not provided:
        - Save to data/output/ with .parquet extension

    Args:
        output_arg: Optional output file path or filename.
        input_path: Input Path object (used for default naming).

    Returns:
        Resolved output Path object.
    """
    if output_arg:
        output_path = Path(output_arg)

        if output_path.parent == Path("."):
            return DATA_OUTPUT_DIR / output_path

        return output_path

    return DATA_OUTPUT_DIR / input_path.with_suffix(".parquet").name


def main() -> int:
    """
    Main CLI entry point for tabular data conversion.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(description="Universal tabular format converter")

    parser.add_argument("input", nargs="?", help="Input file path")
    parser.add_argument("output", nargs="?", help="Optional output file path")

    parser.add_argument("--preview", action="store_true", help="Show dataset structure")

    parser.add_argument("--list-formats", action="store_true", help="List supported formats")

    parser.add_argument(
        "--drop-empty", action="store_true", help="Drop columns with all NaN values"
    )

    args = parser.parse_args()

    # list formats
    if args.list_formats:
        print("Supported input formats:")
        for ext in sorted(LOADERS.keys()):
            print(f"  {ext}")

        print("\nSupported output formats:")
        print("  .csv")
        print("  .parquet")
        return 0

    if not args.input:
        print("Error: input file is required", file=sys.stderr)
        return 1

    # Resolve input
    try:
        input_path = resolve_input_path(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Resolve output
    output_path = resolve_output_path(args.output, input_path)

    # Load
    try:
        df = load_file(input_path)
    except (ValueError, RuntimeError) as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error loading file: Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if args.drop_empty:
        df = df.dropna(axis=1, how="all")

    # Preview
    if args.preview:
        print("\nPreview:")
        print(f"  Rows: {df.shape[0]}")
        print(f"  Columns: {df.shape[1]}")
        print("  Column names:")
        for col in df.columns:
            print(f"    - {col}")

    # Ensure output dir
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        return 1

    suffix = output_path.suffix.lower()

    # Export
    try:
        if suffix == ".csv":
            export_csv(df, output_path)
        elif suffix == ".parquet":
            export_parquet(df, output_path)
        else:
            print(
                f"Error: Unsupported output format: {suffix} (Supported: .csv, .parquet)",
                file=sys.stderr,
            )
            return 1
    except Exception as e:
        print(f"Error exporting file: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"\nSuccess: Saved to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
