"""JSON Canonicalization Scheme (RFC 8785).

Reglas aplicadas:
- Orden de claves: lexicografico por code point UTF-16.
- Strings: escapado minimo, sin normalizacion Unicode.
- Numeros: representacion segun ECMAScript, enteros grandes como strings.
- Sin espacios entre tokens.
"""

from __future__ import annotations

import json
from typing import Any

from .errors import CanonicalizationError

# Enteros por encima de 2^53 pierden precision en ECMAScript.
# El manifiesto v1 los representa como strings.
MAX_SAFE_INTEGER: int = 2**53 - 1


def canonicalize(payload: Any) -> bytes:
    """Serializa un objeto a JSON canonico RFC 8785.

    Args:
        payload: objeto JSON-compatible.

    Returns:
        Bytes UTF-8 del JSON canonico.

    Raises:
        CanonicalizationError: si el objeto contiene tipos no soportados
            o enteros fuera del rango seguro.
    """
    _validate(payload)
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    return text.encode("utf-8")


def _validate(value: Any, path: str = "$") -> None:
    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, str):
        return
    if isinstance(value, int):
        if value > MAX_SAFE_INTEGER or value < -MAX_SAFE_INTEGER:
            raise CanonicalizationError(
                f"Entero fuera de rango seguro en {path}. "
                f"Represente como string."
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
                raise CanonicalizationError(
                    f"Clave no string en {path}: {k!r}"
                )
            _validate(v, f"{path}.{k}")
        return
    raise CanonicalizationError(
        f"Tipo no soportado en {path}: {type(value).__name__}"
    )
