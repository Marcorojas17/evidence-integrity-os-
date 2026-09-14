"""Construccion del paquete .evidence.

Estructura del ZIP:

    paquete.evidence
    ├── manifest.payload.json
    ├── manifest.jws.json
    ├── operational.json
    ├── evidence-report.pdf
    ├── proofs/
    │   ├── token.rfc3161
    │   └── anchor_<position>.json   (opcional)
    ├── signatures/
    │   ├── signing_cert.pem
    │   └── ca_chain.pem
    └── README.txt

No incluye el archivo original por defecto. Si se activa, va cifrado
y con consentimiento explicito (fuera del alcance del MVP).
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Final

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

from src.core.errors import EvidenceError
from src.core.hash_chain import ChainEntry, genesis
from src.core.hashing import (
    content_hash_bytes,
    content_hash_file,
    private_commitment,
)
from src.core.jcs import canonicalize
from src.core.jws import sign_detached
from src.core.kms import KMSProvider
from src.core.manifest import Chain, Commitment, Content, Manifest
from src.core.timestamp import TimestampToken, request_timestamp

PACKAGE_FORMAT_VERSION: Final[str] = "1"
MANIFEST_PAYLOAD_NAME: Final[str] = "manifest.payload.json"
MANIFEST_JWS_NAME: Final[str] = "manifest.jws.json"
OPERATIONAL_NAME: Final[str] = "operational.json"
REPORT_NAME: Final[str] = "evidence-report.pdf"
PROOFS_DIR: Final[str] = "proofs"
TOKEN_NAME: Final[str] = f"{PROOFS_DIR}/token.rfc3161"
SIGNATURES_DIR: Final[str] = "signatures"
SIGNING_CERT_NAME: Final[str] = f"{SIGNATURES_DIR}/signing_cert.pem"
CA_CHAIN_NAME: Final[str] = f"{SIGNATURES_DIR}/ca_chain.pem"
README_NAME: Final[str] = "README.txt"


class BuilderError(EvidenceError):
    """Error al construir el paquete .evidence."""


@dataclass(frozen=True)
class BuildRequest:
    """Datos necesarios para construir un paquete .evidence."""

    evidence_id: str
    source_path: str
    mime_type: str
    context_id: str
    kms_hmac_key_id: str
    tsa_url: str
    signing_key: EllipticCurvePrivateKey
    signing_kid: str
    signing_x5c: list[str]
    signing_cert_pem: str
    ca_chain_pem: str
    previous_manifest_hash: str = ""
    chain_position: str = "0"
    original_included: bool = False


@dataclass(frozen=True)
class BuildResult:
    """Resultado de una construccion exitosa."""

    package_bytes: bytes
    manifest_bytes: bytes
    manifest_digest: bytes
    timestamp: TimestampToken
    chain_entry: ChainEntry


def build_evidence_package(
    request: BuildRequest,
    kms: KMSProvider,
    *,
    created_at: datetime | None = None,
) -> BuildResult:
    """Construye el paquete .evidence en memoria.

    Returns:
        BuildResult con el ZIP completo y artefactos intermedios.
    """
    if not request.source_path:
        raise BuilderError("source_path vacio")
    if not request.tsa_url:
        raise BuilderError("tsa_url vacio. Configure TSA antes de operar.")
    if not request.signing_x5c:
        raise BuilderError("signing_x5c vacio")
    if not request.signing_cert_pem:
        raise BuilderError("signing_cert_pem vacio")

    when = created_at or datetime.now(timezone.utc)

    # 1. Hash del archivo
    try:
        content_hash_hex = content_hash_file(request.source_path)
    except Exception as exc:
        raise BuilderError(f"No se pudo leer el archivo: {exc}") from exc

    import os
    size_bytes = str(os.path.getsize(request.source_path))
    content_hash_bin = bytes.fromhex(content_hash_hex)

    # 2. Compromiso privado via KMS
    commitment_bin = private_commitment(
        kms,
        request.kms_hmac_key_id,
        request.context_id,
        content_hash_bin,
    )

    # 3. Manifiesto
    manifest = Manifest(
        evidence_id=request.evidence_id,
        created_at=when,
        content=Content(
            content_hash=content_hash_hex,
            size_bytes=size_bytes,
            mime_type=request.mime_type,
        ),
        commitment=Commitment(
            context_id=request.context_id,
            private_commitment=commitment_bin.hex(),
            kms_key_id=request.kms_hmac_key_id,
        ),
        chain=Chain(
            previous_manifest_hash=request.previous_manifest_hash,
            chain_position=request.chain_position,
        ),
        original_included=request.original_included,
    )
    manifest.validate()

    manifest_bytes = manifest.canonical_bytes()
    manifest_digest = content_hash_bytes(manifest_bytes)

    # 4. Firma JWS detached
    jws = sign_detached(
        payload_bytes=manifest_bytes,
        private_key=request.signing_key,
        kid=request.signing_kid,
        x5c=request.signing_x5c,
    )

    # 5. Sello de tiempo RFC 3161
    token = request_timestamp(request.tsa_url, manifest_digest)

    # 6. Entrada de hash chain (genesis o append)
    if request.chain_position == "0":
        entry = genesis(
            event_id=f"evt_{request.evidence_id}_0000",
            evidence_id=request.evidence_id,
            event_type="created",
            payload={"manifest_digest": manifest_digest.hex()},
            occurred_at=_iso8601(when),
        )
    else:
        # El llamante debe encadenar externamente; aqui solo creamos
        # una entrada suelta para el paquete actual.
        from src.core.hash_chain import ChainEntry as _CE  # local import

        placeholder_prev = _CE(
            event_id="",
            evidence_id=request.evidence_id,
            event_type="",
            payload={},
            occurred_at="",
            prev_event_hash="",
            chain_position=str(int(request.chain_position) - 1),
        )
        object.__setattr__(placeholder_prev, "event_hash", request.previous_manifest_hash)
        from src.core.hash_chain import append as _append

        entry = _append(
            placeholder_prev,
            event_id=f"evt_{request.evidence_id}_{request.chain_position.zfill(4)}",
            event_type="created",
            payload={"manifest_digest": manifest_digest.hex()},
            occurred_at=_iso8601(when),
        )

    # 7. operational.json
    operational = {
        "evidence_id": request.evidence_id,
        "manifest_digest": manifest_digest.hex(),
        "timestamp_ref": {
            "token_file": TOKEN_NAME,
            "tsa_url": request.tsa_url,
            "serial_number": str(token.serial_number),
            "gen_time": token.gen_time,
        },
        "anchor_refs": [],
        "disclosure": {
            "public": False,
            "public_token": None,
            "content_hash_visible": False,
            "consent_recorded_at": None,
        },
        "retention": {
            "policy": "standard",
            "expires_at": None,
            "nom151_applicable": False,
        },
        "revocation": {
            "state": "active",
            "revoked_at": None,
            "reason": None,
        },
        "original_included": request.original_included,
    }

    # 8. Empaquetado
    package_bytes = _build_zip(
        manifest_bytes=manifest_bytes,
        jws=jws,
        operational=operational,
        token_der=token.token_der,
        signing_cert_pem=request.signing_cert_pem,
        ca_chain_pem=request.ca_chain_pem,
        chain_entry=entry,
    )

    return BuildResult(
        package_bytes=package_bytes,
        manifest_bytes=manifest_bytes,
        manifest_digest=manifest_digest,
        timestamp=token,
        chain_entry=entry,
    )


def _build_zip(
    *,
    manifest_bytes: bytes,
    jws: dict[str, Any],
    operational: dict[str, Any],
    token_der: bytes,
    signing_cert_pem: str,
    ca_chain_pem: str,
    chain_entry: ChainEntry,
) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_PAYLOAD_NAME, manifest_bytes)
        zf.writestr(MANIFEST_JWS_NAME, json.dumps(jws, indent=2))
        zf.writestr(OPERATIONAL_NAME, json.dumps(operational, indent=2))
        zf.writestr(TOKEN_NAME, token_der)
        zf.writestr(SIGNING_CERT_NAME, signing_cert_pem)
        zf.writestr(CA_CHAIN_NAME, ca_chain_pem)
        zf.writestr(
            f"{PROOFS_DIR}/chain_{chain_entry.chain_position}.json",
            json.dumps(chain_entry.to_dict(), indent=2),
        )
        zf.writestr(README_NAME, _readme_text())
    return buf.getvalue()


def _readme_text() -> str:
    return (
        "EVIDENCE INTEGRITY OS - Paquete .evidence\n"
        "=========================================\n\n"
        "Este paquete contiene artefactos criptograficos verificables.\n\n"
        "Contenido:\n"
        "  manifest.payload.json   Manifiesto canonico (JCS RFC 8785)\n"
        "  manifest.jws.json       Firma JWS detached (RFC 7797)\n"
        "  operational.json        Estado operativo del expediente\n"
        "  evidence-report.pdf     Reporte tecnico legible (PAdES-B-T)\n"
        "  proofs/token.rfc3161    Sello de tiempo RFC 3161\n"
        "  signatures/             Cadena de confianza de firma\n\n"
        "Verificacion:\n"
        "  evidence-verify --package <paquete.evidence>\n\n"
        "Aviso:\n"
        "  Este paquete no certifica autoria ni titularidad. Solo\n"
        "  vincula un hash con una fecha verificable emitida por TSA\n"
        "  externa. No constituye constancia NOM-151 ni FEA.\n"
    )


def _iso8601(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{dt.microsecond // 1000:03d}Z"
