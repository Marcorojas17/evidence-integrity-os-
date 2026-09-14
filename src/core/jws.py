"""Firma JWS detached segun RFC 7797.

Reglas estrictas:
- Algoritmos en allowlist. Por defecto: ES256.
- alg=none rechazado explicitamente.
- b64=false obligatorio, declarado en crit.
- Payload detached: el JWS no transporta el payload.
- El verificador recalcula el payload canonico desde el manifiesto.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)

from .errors import AlgorithmNotAllowedError, InvalidSignatureError, JwsError

ALLOWED_ALGORITHMS: Final[frozenset[str]] = frozenset({"ES256"})
CURVE_BY_ALG: Final[dict[str, ec.EllipticCurve]] = {
    "ES256": ec.SECP256R1(),
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def sign_detached(
    payload_bytes: bytes,
    private_key: EllipticCurvePrivateKey,
    kid: str,
    x5c: list[str],
    alg: str = "ES256",
) -> dict[str, Any]:
    """Genera un JWS detached RFC 7797.

    Args:
        payload_bytes: bytes canonicos del manifiesto.
        private_key: clave privada EC P-256.
        kid: thumbprint RFC 7638 de la clave publica.
        x5c: cadena de certificados en base64 DER.
        alg: algoritmo. Solo ES256 en v1.

    Returns:
        Dict con payload vacio, protected y signature (JWS JSON Flattened).
    """
    if alg not in ALLOWED_ALGORITHMS:
        raise AlgorithmNotAllowedError(f"Algoritmo no permitido: {alg}")
    if not kid:
        raise JwsError("kid es obligatorio")
    if not x5c:
        raise JwsError("x5c es obligatorio")

    protected_header = {
        "alg": alg,
        "b64": False,
        "crit": ["b64"],
        "cty": "application/json",
        "kid": kid,
        "x5c": x5c,
    }
    protected_b64 = _b64url_encode(
        json.dumps(protected_header, separators=(",", ":"), sort_keys=True)
        .encode("utf-8")
    )
    signing_input = protected_b64.encode("ascii") + b"." + payload_bytes

    der_sig = private_key.sign(signing_input, ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der_sig)
    raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")

    return {
        "payload": "",
        "protected": protected_b64,
        "signature": _b64url_encode(raw_sig),
    }


def verify_detached(
    jws: dict[str, Any],
    payload_bytes: bytes,
    public_key: EllipticCurvePublicKey,
) -> None:
    """Verifica un JWS detached RFC 7797.

    Raises:
        AlgorithmNotAllowedError, InvalidSignatureError, JwsError
    """
    if jws.get("payload", None) != "":
        raise JwsError("payload debe estar vacio (JWS detached)")

    protected_b64 = jws.get("protected")
    signature_b64 = jws.get("signature")
    if not isinstance(protected_b64, str) or not isinstance(signature_b64, str):
        raise JwsError("protected y signature deben ser strings")

    try:
        protected = json.loads(_b64url_decode(protected_b64))
    except Exception as exc:
        raise JwsError("protected no decodifica a JSON") from exc

    alg = protected.get("alg")
    if alg == "none":
        raise AlgorithmNotAllowedError("alg=none prohibido")
    if alg not in ALLOWED_ALGORITHMS:
        raise AlgorithmNotAllowedError(f"Algoritmo no permitido: {alg}")
    if protected.get("b64") is not False:
        raise JwsError("b64 debe ser false")
    if "b64" not in (protected.get("crit") or []):
        raise JwsError("b64 debe estar declarado en crit")

    signing_input = protected_b64.encode("ascii") + b"." + payload_bytes
    raw_sig = _b64url_decode(signature_b64)
    if len(raw_sig) != 64:
        raise JwsError("Firma debe ser 64 bytes (ES256 raw)")

    r = int.from_bytes(raw_sig[:32], "big")
    s = int.from_bytes(raw_sig[32:], "big")
    der_sig = utils.encode_dss_signature(r, s)

    try:
        public_key.verify(der_sig, signing_input, ECDSA(hashes.SHA256()))
    except InvalidSignature as exc:
        raise InvalidSignatureError("Firma no verifica") from exc
