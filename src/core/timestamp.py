"""Cliente RFC 3161.

Reglas:
- El messageImprint es SHA-256(canonical_bytes del manifiesto).
- El token se valida contra el certificado de la TSA embebido.
- La cadena de la TSA se valida contra un trust store explicito.
- No se confia en genTime como fuente de tiempo sin validar el imprint.
"""

from __future__ import annotations

import hashlib
import httpx
from dataclasses import dataclass
from typing import Callable, Final

from asn1crypto import algos, cms, tsp
from asn1crypto.core import OctetString

from .errors import EvidenceError

DEFAULT_TIMEOUT: Final[float] = 10.0
DEFAULT_MAX_RETRIES: Final[int] = 3
HASH_ALGORITHM: Final[str] = "sha256"


class TimestampError(EvidenceError):
    """Error al solicitar o validar un sello de tiempo."""


class TimestampRejectedError(TimestampError):
    """La TSA devolvio estado distinto de granted."""


class TimestampMismatchError(TimestampError):
    """El messageImprint no coincide con el digest esperado."""


@dataclass(frozen=True)
class TimestampToken:
    """Resultado de un sellado RFC 3161."""

    token_der: bytes
    tsa_url: str
    serial_number: int
    gen_time: str
    message_imprint: bytes
    hash_algorithm: str


def _build_request(digest: bytes) -> bytes:
    if len(digest) != 32:
        raise TimestampError("El digest debe ser SHA-256 (32 bytes)")
    req = tsp.TimeStampReq(
        {
            "version": "v1",
            "message_imprint": {
                "hash_algorithm": {"algorithm": "sha256"},
                "hashed_message": digest,
            },
            "cert_req": True,
            "nonce": int.from_bytes(hashlib.sha256(digest).digest()[:8], "big"),
        }
    )
    return req.dump()


def _parse_response(response_der: bytes, expected_digest: bytes) -> TimestampToken:
    try:
        resp = tsp.TimeStampResp.load(response_der)
    except Exception as exc:
        raise TimestampError("Respuesta ASN.1 invalida") from exc

    status = resp["status"]
    status_value = status["status"].native
    if status_value != "granted":
        raise TimestampRejectedError(f"TSA devolvio estado: {status_value}")

    token = resp["time_stamp_token"]
    if token is None:
        raise TimestampError("Respuesta sin time_stamp_token")

    try:
        content_info = cms.ContentInfo.load(token.dump())
    except Exception as exc:
        raise TimestampError("Token CMS invalido") from exc

    signed_data = content_info["content"]
    tst_info_bytes = signed_data["encap_content_info"]["content"].native
    if tst_info_bytes is None:
        raise TimestampError("Token sin contenido TSTInfo")
    tst_info = tsp.TSTInfo.load(tst_info_bytes)

    imprint = tst_info["message_imprint"]
    hash_alg = imprint["hash_algorithm"]["algorithm"].native
    if hash_alg != HASH_ALGORITHM:
        raise TimestampError(f"Algoritmo de imprint no soportado: {hash_alg}")
    imprint_bytes = imprint["hashed_message"].native
    if imprint_bytes != expected_digest:
        raise TimestampMismatchError("messageImprint no coincide con el digest")

    gen_time = tst_info["gen_time"].native.isoformat()
    serial = int(tst_info["serial_number"].native)

    return TimestampToken(
        token_der=token.dump(),
        tsa_url="",
        serial_number=serial,
        gen_time=gen_time,
        message_imprint=imprint_bytes,
        hash_algorithm=hash_alg,
    )


def request_timestamp(
    tsa_url: str,
    digest: bytes,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    transport: httpx.BaseTransport | None = None,
) -> TimestampToken:
    """Solicita un sello RFC 3161 a la TSA indicada.

    Solo se usa en tests con `transport` mockeado o con TSA real configurada.
    En produccion, `tsa_url` debe apuntar a una TSA cualificada contratada.
    """
    if not tsa_url:
        raise TimestampError("tsa_url vacio. Configure TSA antes de operar.")

    request_der = _build_request(digest)
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout, transport=transport) as client:
                response = client.post(
                    tsa_url,
                    content=request_der,
                    headers={"Content-Type": "application/timestamp-query"},
                )
                response.raise_for_status()
                token = _parse_response(response.content, digest)
                return TimestampToken(
                    token_der=token.token_der,
                    tsa_url=tsa_url,
                    serial_number=token.serial_number,
                    gen_time=token.gen_time,
                    message_imprint=token.message_imprint,
                    hash_algorithm=token.hash_algorithm,
                )
        except (httpx.HTTPError, TimestampError) as exc:
            last_exc = exc
            if attempt == max_retries:
                break

    raise TimestampError(
        f"Fallo al solicitar sello tras {max_retries} intentos: {last_exc}"
    )


def verify_token_imprint(token_der: bytes, expected_digest: bytes) -> None:
    """Verifica solo el messageImprint del token contra el digest esperado.

    La verificacion criptografica de la firma de la TSA y de su cadena
    se realiza en src/evidence/verifier.py con un trust store explicito.
    """
    try:
        content_info = cms.ContentInfo.load(token_der)
    except Exception as exc:
        raise TimestampError("Token CMS invalido") from exc
    tst_info_bytes = content_info["content"]["encap_content_info"]["content"].native
    tst_info = tsp.TSTInfo.load(tst_info_bytes)
    imprint = tst_info["message_imprint"]["hashed_message"].native
    if imprint != expected_digest:
        raise TimestampMismatchError("messageImprint no coincide")
