"""Canonicalizacion JCS RFC 8785.

Se delega en la libreria rfc8785, auditada contra los vectores
oficiales del RFC. No se implementa JCS a mano.
"""

from __future__ import annotations

from typing import Any

import rfc8785

from .errors import CanonicalizationError

MAX_SAFE_INTEGER: int = 2**53 - 1


def canonicalize(payload: Any) -> bytes:
    """Serializa un objeto a JSON canonico RFC 8785.

    Raises:
        CanonicalizationError: tipos no soportados o valores fuera de rango.
    """
    _validate(payload)
    try:
        return rfc8785.dumps(payload)
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc


def _validate(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        if value > MAX_SAFE_INTEGER or value < -MAX_SAFE_INTEGER:
            raise CanonicalizationError(
                f"Entero fuera de rango seguro en {path}. Use string."
            )
        return
    if isinstance(value, float):
        raise CanonicalizationError(
            f"Float no soportado en {path}. Use enteros o strings."
        )
    if isinstance(value, list):
        for i, item in enumerate(value):
            _validate(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise CanonicalizationError(f"Clave no string en {path}: {k!r}")
            _validate(v, f"{path}.{k}")
        return
    raise CanonicalizationError(
        f"Tipo no soportado en {path}: {type(value).__name__}"
    )
