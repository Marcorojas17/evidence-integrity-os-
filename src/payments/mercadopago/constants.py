"""Constantes de Mercado Pago."""

from __future__ import annotations

from typing import Final

MP_API_BASE: Final[str] = "https://api.mercadopago.com"

# status_detail aceptados para status=approved
APPROVED_STATUS_DETAILS: Final[frozenset[str]] = frozenset({
    "accredited",
    "partially_refunded",
})

# live_mode esperado segun entorno
LIVE_MODE_BY_ENV: Final[dict[str, bool]] = {
    "sandbox": False,
    "production": True,
}
