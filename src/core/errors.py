"""Excepciones del nucleo criptografico."""


class EvidenceError(Exception):
    """Error base del nucleo."""


class HashingError(EvidenceError):
    """Error al calcular hashes o compromisos."""


class CanonicalizationError(EvidenceError):
    """Error al canonicalizar JSON (RFC 8785)."""


class ManifestError(EvidenceError):
    """Error al construir o validar el manifiesto."""


class ManifestValidationError(ManifestError):
    """El manifiesto no cumple el esquema."""


class JwsError(EvidenceError):
    """Error al firmar o verificar JWS."""


class AlgorithmNotAllowedError(JwsError):
    """El algoritmo solicitado no esta en la allowlist."""


class InvalidSignatureError(JwsError):
    """La firma no verifica."""
