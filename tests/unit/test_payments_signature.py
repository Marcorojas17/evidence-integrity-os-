"""Smoke tests de verificacion de firma."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from src.payments.exceptions import SignatureError, SignatureReplayError
from src.payments.signature import (
    build_manifest,
    parse_x_signature,
    verify_signature,
)

SECRET = "test-webhook-secret"


def _sign(data_id: str, request_id: str, ts: int, secret: str = SECRET) -> str:
    manifest = build_manifest(data_id, request_id, ts)
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def test_parse_valid_header() -> None:
    p = parse_x_signature("ts=1700000000,v1=abc,v1=def")
    assert p.ts == 1700000000
    assert p.v1_values == ("abc", "def")


def test_parse_rejects_empty() -> None:
    with pytest.raises(SignatureError):
        parse_x_signature("")


def test_parse_rejects_missing_ts() -> None:
    with pytest.raises(SignatureError):
        parse_x_signature("v1=abc")


def test_parse_rejects_missing_v1() -> None:
    with pytest.raises(SignatureError):
        parse_x_signature("ts=1700000000")


def test_verify_accepts_valid_signature() -> None:
    now = int(time.time())
    v1 = _sign("123", "req-1", now)
    verify_signature(
        header=f"ts={now},v1={v1}",
        request_id="req-1",
        data_id="123",
        secret=SECRET,
        now_ts=now,
    )


def test_verify_rejects_wrong_signature() -> None:
    now = int(time.time())
    with pytest.raises(SignatureError):
        verify_signature(
            header=f"ts={now},v1=deadbeef",
            request_id="req-1",
            data_id="123",
            secret=SECRET,
            now_ts=now,
        )


def test_verify_rejects_old_timestamp() -> None:
    now = int(time.time())
    old_ts = now - 400
    v1 = _sign("123", "req-1", old_ts)
    with pytest.raises(SignatureReplayError):
        verify_signature(
            header=f"ts={old_ts},v1={v1}",
            request_id="req-1",
            data_id="123",
            secret=SECRET,
            now_ts=now,
        )


def test_verify_accepts_previous_secret_during_rotation() -> None:
    now = int(time.time())
    old_secret = "old-secret"
    v1 = _sign("123", "req-1", now, secret=old_secret)
    verify_signature(
        header=f"ts={now},v1={v1}",
        request_id="req-1",
        data_id="123",
        secret=SECRET,
        previous_secret=old_secret,
        now_ts=now,
    )
