"""Smoke tests del builder de paquetes .evidence."""

from __future__ import annotations

import base64
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from src.core.kms import LocalKMS
from src.evidence.builder import BuildRequest, build_evidence_package
from src.evidence.verifier import verify_evidence_package


def _generate_cert(key: ec.EllipticCurvePrivateKey) -> tuple[x509.Certificate, str, str]:
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc).replace(year=2027))
        .sign(key, hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    return cert, base64.b64encode(der).decode(), pem


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.bin"
    p.write_bytes(b"evidence payload for test")
    return p


@pytest.fixture
def local_kms() -> LocalKMS:
    return LocalKMS({"kms-hmac-test": b"\x42" * 32})


@pytest.fixture
def signing_material() -> dict:
    key = ec.generate_private_key(ec.SECP256R1())
    _, x5c, cert_pem = _generate_cert(key)
    from src.core.jws import _jwk_thumbprint_sha256

    return {
        "key": key,
        "kid": _jwk_thumbprint_sha256(key.public_key()),
        "x5c": [x5c],
        "cert_pem": cert_pem,
        "ca_pem": cert_pem,
    }


def test_build_fails_without_tsa_url(sample_file, local_kms, signing_material) -> None:
    req = BuildRequest(
        evidence_id="ev_test0001",
        source_path=str(sample_file),
        mime_type="application/octet-stream",
        context_id="ctx_test_001",
        kms_hmac_key_id="kms-hmac-test",
        tsa_url="",
        signing_key=signing_material["key"],
        signing_kid=signing_material["kid"],
        signing_x5c=signing_material["x5c"],
        signing_cert_pem=signing_material["cert_pem"],
        ca_chain_pem=signing_material["ca_pem"],
    )
    with pytest.raises(Exception):
        build_evidence_package(req, local_kms)


def test_package_structure(sample_file, local_kms, signing_material, monkeypatch) -> None:
    """El paquete incluye los archivos esperados."""

    # Mock de request_timestamp para no requerir TSA real
    from src.core import timestamp as ts_mod

    class FakeToken:
        token_der = b"\x30\x03\x02\x01\x00"
        tsa_url = "mock"
        serial_number = 1
        gen_time = "2026-09-13T12:00:00+00:00"
        message_imprint = b""
        hash_algorithm = "sha256"

    def fake_request(tsa_url, digest, **kw):  # noqa: ANN001, ANN003
        return FakeToken()

    monkeypatch.setattr(ts_mod, "request_timestamp", fake_request)

    req = BuildRequest(
        evidence_id="ev_test0001",
        source_path=str(sample_file),
        mime_type="application/octet-stream",
        context_id="ctx_test_001",
        kms_hmac_key_id="kms-hmac-test",
        tsa_url="http://mock",
        signing_key=signing_material["key"],
        signing_kid=signing_material["kid"],
        signing_x5c=signing_material["x5c"],
        signing_cert_pem=signing_material["cert_pem"],
        ca_chain_pem=signing_material["ca_pem"],
    )
    result = build_evidence_package(req, local_kms)

    with zipfile.ZipFile(io.BytesIO(result.package_bytes)) as zf:
        names = set(zf.namelist())
        assert "manifest.payload.json" in names
        assert "manifest.jws.json" in names
        assert "operational.json" in names
        assert "proofs/token.rfc3161" in names

        manifest = json.loads(zf.read("manifest.payload.json"))
        assert manifest["evidence_id"] == "ev_test0001"
        assert manifest["content"]["hash_algorithm"] == "sha256"
        assert manifest["commitment"]["algorithm"] == "hmac-sha256"
        assert manifest["original_included"] is False
