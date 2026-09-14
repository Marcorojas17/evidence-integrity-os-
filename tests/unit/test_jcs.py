"""Smoke tests de canonicalizacion RFC 8785."""

from __future__ import annotations

import pytest

from src.core.errors import CanonicalizationError
from src.core.jcs import canonicalize


def test_sorts_keys() -> None:
    assert canonicalize({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_no_whitespace() -> None:
    assert canonicalize({"a": [1, 2, 3]}) == b'{"a":[1,2,3]}'


def test_unicode_preserved() -> None:
    assert canonicalize({"a": "café"}) == '{"a":"café"}'.encode("utf-8")


def test_rejects_float() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({"a": 1.5})


def test_rejects_large_int() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({"a": 2**60})


def test_accepts_large_int_as_string() -> None:
    assert canonicalize({"a": "1152921504606846976"}) == \
        b'{"a":"1152921504606846976"}'


def test_rejects_non_string_key() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize({1: "a"})  # type: ignore[dict-item]
