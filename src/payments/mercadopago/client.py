"""Cliente HTTP de Mercado Pago."""

from __future__ import annotations

from typing import Any

import httpx

from src.payments.exceptions import PaymentError

from .constants import MP_API_BASE

DEFAULT_TIMEOUT: float = 15.0


class MercadoPagoClient:
    """Cliente HTTP con autenticación por access token."""

    def __init__(
        self,
        access_token: str,
        *,
        base_url: str = MP_API_BASE,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not access_token:
            raise PaymentError("MP_ACCESS_TOKEN no configurado")
        self._token = access_token
        self._base = base_url
        self._timeout = timeout
        self._transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base,
            timeout=self._timeout,
            transport=self._transport,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
        )

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        with self._client() as client:
            r = client.get(f"/v1/payments/{payment_id}")
            r.raise_for_status()
            return r.json()

    def get_refunds(self, payment_id: str) -> list[dict[str, Any]]:
        with self._client() as client:
            r = client.get(f"/v1/payments/{payment_id}/refunds")
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []

    def create_preference(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        with self._client() as client:
            r = client.post(
                "/checkout/preferences",
                json=payload,
                headers={"X-Idempotency-Key": idempotency_key},
            )
            r.raise_for_status()
            return r.json()
