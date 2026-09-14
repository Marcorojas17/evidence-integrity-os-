"""Vectores oficiales RFC 8785 y casos de error."""

from __future__ import annotations

import pytest

from src.core.errors import CanonicalizationError
from src.core.jcs import canonicalize


def test_rfc8785_key_sorting() -> None:
    # Vectores derivados de RFC 8785 Appendix B.
    assert canonicalize({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    assert canonicalize({"1": "One", "\u20ac": "Euro", "\U0001F600": "Emoji"}) == (
        '{"1":"One","€":"Euro","😀":"Emoji"}'.encode("utf-8")
    )


def test_utf16_order_differs_from_codepoint() -> None:
    # U+E000 va despues de U+10000 en UTF-16 pero antes por code point.
    result = canonicalize({"\uE000": "a", "\U00010000": "b"})
    assert result == '{"𐀀":"b","":"a"}'.encode("utf-8")


def test_string_escaping() -> None:
    assert canonicalize({"a": "\u20ac"}) == '{"a":"€"}'.encode("utf-8")
    assert canonicalize({"a": "\n"}) == b'{"a":"\\n"}'


def test_rejects_float() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({"a": 1.5})


def test_rejects_large_int() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({"a": 2**60})


def test_rejects_non_string_key() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({1: "a"})
