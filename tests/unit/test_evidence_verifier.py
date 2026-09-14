"""Smoke tests del verifier de paquetes .evidence."""

from __future__ import annotations

from src.evidence.verifier import VerifyResult, verify_evidence_package


def test_rejects_non_bytes() -> None:
    try:
        verify_evidence_package("not bytes")  # type: ignore[arg-type]
        assert False, "Debio lanzar"
    except Exception:
        pass


def test_rejects_invalid_zip() -> None:
    result: VerifyResult = verify_evidence_package(b"not a zip")
    assert result.valid is False
    assert any(s.name == "zip" and not s.passed for s in result.steps)


def test_rejects_empty_bytes() -> None:
    result = verify_evidence_package(b"")
    assert result.valid is False
