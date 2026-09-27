

from datasift.cli import main


def test_cli_formats(capsys):
    assert main(["formats"]) == 0
    captured = capsys.readouterr()
    assert "json" in captured.out
    assert "csv" in captured.out
    assert "xml" in captured.out


def test_cli_convert(tmp_path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.yaml"
    src.write_text('{"name": "Alice", "age": 30}', encoding="utf-8")
    assert main(["convert", str(src), str(dst)]) == 0
    assert dst.exists()
    assert "Alice" in dst.read_text(encoding="utf-8")


def test_cli_query(tmp_path, capsys):
    src = tmp_path / "data.json"
    src.write_text('{"users": [{"name": "Alice"}, {"name": "Bob"}]}', encoding="utf-8")
    assert main(["query", str(src), "users[0].name"]) == 0
    captured = capsys.readouterr()
    assert "Alice" in captured.out
