"""Firma JWS detached RFC 7797 con validacion estricta.

Reglas:
- Algoritmos en allowlist. Solo ES256 por defecto.
- alg=none rechazado.
- b64=false declarado en crit.
- kid obligatorio; debe coincidir con thumbprint RFC 7638 del cert hoja.
- x5c obligatorio; la clave publica se extrae del certificado hoja.
- Validacion de cadena contra trust store externo (obligatoria en prod).
"""

from __future__ import annotations

import base64
import json
from typing import Any, Callable, Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.x509 import Certificate, load_der_x509_certificate

from .errors import AlgorithmNotAllowedError, InvalidSignatureError, JwsError

ALLOWED_ALGORITHMS: Final[frozenset[str]] = frozenset({"ES256"})

TrustStore = Callable[[list[Certificate]], None]


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data + pad)
    except Exception as exc:
        raise JwsError("base64url invalido") from exc


def _decode_x5c(x5c: list[str]) -> list[Certificate]:
    if not isinstance(x5c, list) or not x5c:
        raise JwsError("x5c debe ser lista no vacia")
    certs: list[Certificate] = []
    for i, b64 in enumerate(x5c):
        if not isinstance(b64, str):
            raise JwsError(f"x5c[{i}] debe ser string base64")
        try:
            der = base64.b64decode(b64, validate=True)
            certs.append(load_der_x509_certificate(der))
        except Exception as exc:
            raise JwsError(f"x5c[{i}] no decodifica a certificado X.509") from exc
    return certs


def _jwk_thumbprint_sha256(public_key: EllipticCurvePublicKey) -> str:
    """RFC 7638 thumbprint de la clave publica EC P-256."""
    numbers = public_key.public_numbers()
    jwk = {
        "crv": "P-256",
        "kty": "EC",
        "x": _b64url_encode(numbers.x.to_bytes(32, "big")),
        "y": _b64url_encode(numbers.y.to_bytes(32, "big")),
    }
    canonical = json.dumps(jwk, separators=(",", ":"), sort_keys=True).encode("utf-8")
    import hashlib
    return _b64url_encode(hashlib.sha256(canonical).digest())


def sign_detached(
    payload_bytes: bytes,
    private_key: EllipticCurvePrivateKey,
    kid: str,
    x5c: list[str],
    alg: str = "ES256",
) -> dict[str, Any]:
    if alg not in ALLOWED_ALGORITHMS:
        raise AlgorithmNotAllowedError(f"Algoritmo no permitido: {alg}")
    if not kid:
        raise JwsError("kid es obligatorio")
    if not x5c:
        raise JwsError("x5c es obligatorio")

    protected = {
        "alg": alg,
        "b64": False,
        "crit": ["b64"],
        "cty": "application/json",
        "kid": kid,
        "x5c": x5c,
    }
    protected_b64 = _b64url_encode(
        json.dumps(protected, separators=(",", ":"), sort_keys=True).encode("utf-8")
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
    trust_store: TrustStore | None = None,
) -> EllipticCurvePublicKey:
    """Verifica JWS detached RFC 7797.

    - Requiere kid y x5c.
    - Valida kid contra thumbprint RFC 7638 del cert hoja.
    - Valida x5c decodificando todos los certificados.
    - Si trust_store se pasa, valida la cadena. Sin trust_store, la
      verificacion es solo criptografica contra la clave del cert hoja.
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
    crit = protected.get("crit")
    if not isinstance(crit, list) or "b64" not in crit:
        raise JwsError("crit debe ser lista y contener 'b64'")

    kid = protected.get("kid")
    if not isinstance(kid, str) or not kid:
        raise JwsError("kid es obligatorio")

    x5c = protected.get("x5c")
    certs = _decode_x5c(x5c)

    leaf = certs[0]
    leaf_pub = leaf.public_key()
    if not isinstance(leaf_pub, EllipticCurvePublicKey):
        raise JwsError("Certificado hoja no contiene clave EC")

    expected_kid = _jwk_thumbprint_sha256(leaf_pub)
    if kid != expected_kid:
        raise JwsError("kid no coincide con thumbprint del certificado hoja")

    if trust_store is not None:
        trust_store(certs)

    signing_input = protected_b64.encode("ascii") + b"." + payload_bytes
    raw_sig = _b64url_decode(signature_b64)
    if len(raw_sig) != 64:
        raise JwsError("Firma debe ser 64 bytes (ES256 raw)")

    r = int.from_bytes(raw_sig[:32], "big")
    s = int.from_bytes(raw_sig[32:], "big")
    der_sig = utils.encode_dss_signature(r, s)

    try:
        leaf_pub.verify(der_sig, signing_input, ECDSA(hashes.SHA256()))
    except InvalidSignature as exc:
        raise InvalidSignatureError("Firma no verifica") from exc

    return leaf_pub
