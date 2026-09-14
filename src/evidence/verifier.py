"""Verificacion end-to-end de un paquete .evidence.

Valida:
1. Estructura del ZIP (archivos esperados).
2. Manifiesto canonico y esquema.
3. Firma JWS detached contra trust store.
4. Token RFC 3161 contra messageImprint.
5. Hash chain local (chain_<position>.json).
6. Estado de revocacion declarado en operational.json.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Final

from src.core.errors import EvidenceError
from src.core.hash_chain import ChainEntry, verify_chain
from src.core.hashing import content_hash_bytes
from src.core.jcs import canonicalize
from src.core.jws import verify_detached
from src.core.timestamp import verify_token_imprint

MANIFEST_PAYLOAD_NAME: Final[str] = "manifest.payload.json"
MANIFEST_JWS_NAME: Final[str] = "manifest.jws.json"
OPERATIONAL_NAME: Final[str] = "operational.json"
TOKEN_NAME: Final[str] = "proofs/token.rfc3161"
REQUIRED_FILES: Final[frozenset[str]] = frozenset(
    {MANIFEST_PAYLOAD_NAME, MANIFEST_JWS_NAME, OPERATIONAL_NAME, TOKEN_NAME}
)

TrustStore = Callable[[list], None]


class VerifyError(EvidenceError):
    """Error de verificacion del paquete."""


@dataclass
class VerifyStep:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerifyResult:
    valid: bool
    steps: list[VerifyStep] = field(default_factory=list)
    evidence_id: str | None = None
    manifest_digest: str | None = None
    tsa_gen_time: str | None = None
    revocation_state: str | None = None

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "evidence_id": self.evidence_id,
            "manifest_digest": self.manifest_digest,
            "tsa_gen_time": self.tsa_gen_time,
            "revocation_state": self.revocation_state,
            "steps": [
                {"name": s.name, "passed": s.passed, "detail": s.detail}
                for s in self.steps
            ],
        }


def verify_evidence_package(
    package_bytes: bytes,
    *,
    trust_store: TrustStore | None = None,
) -> VerifyResult:
    """Verifica el paquete y devuelve un resultado estructurado.

    Nunca lanza por fallo de verificacion; devuelve valid=False.
    Solo lanza por errores de programacion (tipos incorrectos).
    """
    if not isinstance(package_bytes, (bytes, bytearray)):
        raise VerifyError("package_bytes debe ser bytes")

    result = VerifyResult(valid=False)
    try:
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as zf:
            _verify_package(zf, trust_store, result)
    except zipfile.BadZipFile as exc:
        result.steps.append(VerifyStep("zip", False, f"ZIP invalido: {exc}"))
        return result
    except Exception as exc:
        result.steps.append(VerifyStep("unexpected", False, str(exc)))
        return result

    result.valid = all(s.passed for s in result.steps)
    return result


def _verify_package(
    zf: zipfile.ZipFile,
    trust_store: TrustStore | None,
    result: VerifyResult,
) -> None:
    names = set(zf.namelist())

    # 1. Estructura
    missing = REQUIRED_FILES - names
    if missing:
        result.steps.append(
            VerifyStep("estructura", False, f"Faltan archivos: {sorted(missing)}")
        )
        return
    result.steps.append(VerifyStep("estructura", True))

    # 2. Manifiesto: parsear y recalcular canonico
    raw_manifest = zf.read(MANIFEST_PAYLOAD_NAME)
    try:
        manifest_obj = json.loads(raw_manifest)
    except json.JSONDecodeError as exc:
        result.steps.append(VerifyStep("manifest.parse", False, str(exc)))
        return

    try:
        canonical = canonicalize(manifest_obj)
    except Exception as exc:
        result.steps.append(VerifyStep("manifest.canonical", False, str(exc)))
        return

    if canonical != raw_manifest:
        result.steps.append(
            VerifyStep("manifest.canonical", False, "Manifiesto no es canonico RFC 8785")
        )
        return
    result.steps.append(VerifyStep("manifest.canonical", True))

    result.evidence_id = manifest_obj.get("evidence_id")
    digest = content_hash_bytes(raw_manifest)
    result.manifest_digest = digest.hex()

    # 3. Esquema del manifiesto
    try:
        import jsonschema
        from src.core.manifest import _schema  # acceso controlado al cache

        jsonschema.validate(manifest_obj, _schema())
        result.steps.append(VerifyStep("manifest.schema", True))
    except Exception as exc:
        result.steps.append(VerifyStep("manifest.schema", False, str(exc)))
        return

    # 4. Firma JWS detached
    try:
        jws = json.loads(zf.read(MANIFEST_JWS_NAME))
        verify_detached(jws, raw_manifest, trust_store=trust_store)
        result.steps.append(
            VerifyStep("jws", True, "firma valida" if trust_store else "firma valida sin trust store")
        )
    except Exception as exc:
        result.steps.append(VerifyStep("jws", False, str(exc)))
        return

    # 5. Token RFC 3161 contra messageImprint
    try:
        token_der = zf.read(TOKEN_NAME)
        verify_token_imprint(token_der, digest)
        result.steps.append(VerifyStep("rfc3161.imprint", True))
    except Exception as exc:
        result.steps.append(VerifyStep("rfc3161.imprint", False, str(exc)))
        return

    # 6. Hash chain local
    chain_files = sorted(
        n for n in names if n.startswith("proofs/chain_") and n.endswith(".json")
    )
    if not chain_files:
        result.steps.append(
            VerifyStep("hash_chain", False, "No se encontro entrada de cadena")
        )
        return

    try:
        entries = []
        for name in chain_files:
            data = json.loads(zf.read(name))
            entries.append(
                ChainEntry(
                    event_id=data["event_id"],
                    evidence_id=data["evidence_id"],
                    event_type=data["event_type"],
                    payload=data["payload"],
                    occurred_at=data["occurred_at"],
                    prev_event_hash=data["prev_event_hash"],
                    chain_position=data["chain_position"],
                    event_hash=data["event_hash"],
                )
            )
        verify_chain(entries)
        result.steps.append(VerifyStep("hash_chain", True))
    except Exception as exc:
        result.steps.append(VerifyStep("hash_chain", False, str(exc)))
        return

    # 7. Estado operativo (informativo, no bloqueante)
    try:
        operational = json.loads(zf.read(OPERATIONAL_NAME))
        revocation = operational.get("revocation", {})
        result.revocation_state = revocation.get("state", "unknown")
        ts_ref = operational.get("timestamp_ref", {})
        result.tsa_gen_time = ts_ref.get("gen_time")
        result.steps.append(
            VerifyStep(
                "operational",
                True,
                f"revocacion: {result.revocation_state}",
            )
        )
    except Exception as exc:
        result.steps.append(VerifyStep("operational", False, str(exc)))
