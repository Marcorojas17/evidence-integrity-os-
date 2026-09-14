"""Smoke tests de cadena de hashes."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.hash_chain import (
    ChainEntry,
    ChainForkError,
    ChainReorderError,
    ChainTamperError,
    append,
    genesis,
    verify_chain,
)


def _chain3() -> list[ChainEntry]:
    e0 = genesis("e0", "ev_abc", "created", {"a": 1}, "2026-09-13T10:00:00.000Z")
    e1 = append(e0, "e1", "validated", {"b": 2}, "2026-09-13T10:01:00.000Z")
    e2 = append(e1, "e2", "emitted", {"c": 3}, "2026-09-13T10:02:00.000Z")
    return [e0, e1, e2]


def test_valid_chain_passes() -> None:
    verify_chain(_chain3())


def test_detects_tamper_in_payload() -> None:
    chain = _chain3()
    tampered = replace(chain[1], payload={"b": 999})
    with pytest.raises(ChainTamperError):
        verify_chain([chain[0], tampered, chain[2]])


def test_detects_tamper_in_event_hash() -> None:
    chain = _chain3()
    tampered = replace(chain[2], event_hash="0" * 64)
    with pytest.raises(ChainTamperError):
        verify_chain([chain[0], chain[1], tampered])


def test_detects_reorder() -> None:
    chain = _chain3()
    with pytest.raises((ChainReorderError, ChainTamperError)):
        verify_chain([chain[0], chain[2], chain[1]])


def test_detects_missing_genesis() -> None:
    chain = _chain3()
    with pytest.raises(ChainReorderError):
        verify_chain([chain[1], chain[2]])


def test_detects_fork() -> None:
    chain = _chain3()
    forked = append(
        chain[1], "e2b", "forked", {"x": 1}, "2026-09-13T10:03:00.000Z"
    )
    with pytest.raises(ChainForkError):
        verify_chain([chain[0], chain[1], chain[2], forked])
