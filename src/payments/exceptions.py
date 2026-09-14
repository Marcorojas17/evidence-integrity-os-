"""Excepciones del procesador de pagos."""

from __future__ import annotations

from src.core.errors import EvidenceError


class PaymentError(EvidenceError):
    """Error base del procesador de pagos."""


class SignatureError(PaymentError):
    """Firma de webhook inválida o replay detectado."""


class SignatureReplayError(SignatureError):
    """Timestamp del webhook fuera de la ventana permitida."""


class ValidationError(PaymentError):
    """El pago no pasó la validación de campos."""


class PaymentNotApprovedYetError(ValidationError):
    """El pago aún no está aprobado. Reintentar en el siguiente webhook."""


class FulfillmentError(PaymentError):
    """Error al crear o actualizar un fulfillment."""


class FulfillmentConflictError(FulfillmentError):
    """Otro worker ya reclamó este pago."""


class WorkerLeaseError(FulfillmentError):
    """El worker ya no es dueño del lease."""


class RecoveryError(PaymentError):
    """Error en el job de recuperación."""
