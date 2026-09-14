"""Excepciones del log de auditoría."""

from __future__ import annotations

from src.core.errors import EvidenceError


class AuditError(EvidenceError):
    """Error base del log de auditoría."""


class AuditChainError(AuditError):
    """Cadena de eventos rota o manipulada."""


class AuditSignatureError(AuditError):
    """Firma de evento o cierre inválida."""


class AuditAnchorError(AuditError):
    """Error al anclar o recuperar un cierre externo."""


class AuditCloseError(AuditError):
    """Error al crear o verificar un cierre."""
