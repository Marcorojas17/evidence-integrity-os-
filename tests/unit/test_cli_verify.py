"""Smoke tests del CLI evidence-verify."""

from __future__ import annotations

from pathlib import Path

from src.cli.verify_independently import main


def test_cli_returns_2_for_missing_file(tmp_path: Path, capsys) -> None:
    rc = main(["--package", str(tmp_path / "nonexistent.evidence")])
    out = capsys.readouterr().out
    assert rc == 2
    assert "no encontrado" in out


def test_cli_returns_1_for_invalid_package(tmp_path: Path, capsys) -> None:
    p = tmp_path / "fake.evidence"
    p.write_bytes(b"not a zip")
    rc = main(["--package", str(p)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "INVALIDO" in out


def test_cli_json_mode(tmp_path: Path, capsys) -> None:
    p = tmp_path / "fake.evidence"
    p.write_bytes(b"not a zip")
    rc = main(["--package", str(p), "--json"])
    out = capsys.readouterr().out
    assert rc == 1
    assert '"valid": false' in out
