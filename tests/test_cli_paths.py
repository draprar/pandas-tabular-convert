from pathlib import Path

from file_converter.cli import resolve_input_path, resolve_output_path


def test_resolve_input_direct_path(tmp_path):
    file = tmp_path / "data.csv"
    file.write_text("a,b\n1,2")

    resolved = resolve_input_path(str(file))
    assert resolved == file


def test_resolve_input_from_data_input(tmp_path, monkeypatch):
    data_input = tmp_path / "data/input"
    data_input.mkdir(parents=True)

    file = data_input / "data.csv"
    file.write_text("a,b\n1,2")

    monkeypatch.setattr("file_converter.cli.DATA_INPUT_DIR", data_input)

    resolved = resolve_input_path("data.csv")
    assert resolved == file


def test_resolve_output_default(tmp_path):
    input_file = tmp_path / "data.csv"

    output = resolve_output_path(None, input_file)
    assert output.name == "data.parquet"


def test_resolve_output_filename_only(tmp_path, monkeypatch):
    data_output = tmp_path / "data/output"
    monkeypatch.setattr("file_converter.cli.DATA_OUTPUT_DIR", data_output)

    output = resolve_output_path("result.csv", Path("input.csv"))
    assert output == data_output / "result.csv"
