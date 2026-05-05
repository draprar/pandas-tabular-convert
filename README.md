# Tabular Convert

![CI](https://github.com/draprar/pandas-tabular-convert/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Code style](https://img.shields.io/badge/code%20style-ruff-261230)

CLI tool for converting tabular data between common formats into a unified Pandas DataFrame and exporting it to CSV or Parquet.

## Features

- **Input formats**: CSV, Excel (.xlsx, .xls), JSON, Pickle, Parquet
- **Output formats**: CSV, Parquet (default)
- **Unified loading pipeline based on Pandas DataFrame**
- **Data preview** with `--preview`
- **Clean empty columns** with `--drop-empty`
- **Default input/output directories**: `data/input/` and `data/output/`

### ⚠️ Security Note: Pickle Format

Pickle files can execute arbitrary code during deserialization.

⚠️ They should only be used with trusted local files. Never use with external or user-provided data.

Enable only when necessary:
```
UNSAFE_PICKLE=1 convert data.pkl
```

---

## Installation

```
pip install .
```

Editable mode (recommended for development):

```
pip install -e .
```

After installation, CLI command becomes available: `convert`

---

## Usage

Basic conversion (default export to Parquet):

```
convert events.csv
```

Convert and export to CSV:

```
convert events.csv result.csv
```

Preview dataset structure:

```
convert events.csv --preview
```

Drop fully empty columns:

```
convert events.csv --drop-empty
```

List supported formats:

```
convert --list-formats
```

---

## Project Structure

```
project/
├── src/
│   └── file_converter/
├── tests/
├── data/
│   ├── input/
│   └── output/
└── pyproject.toml
```

---

## Development

Run tests:

```
pytest
```

Tests are run automatically on GitHub Actions for every push and pull request to ensure code quality.

---

## License

MIT License.

## Author

[Walery](https://github.com/draprar)
