"""Smoke tests del webhook."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock

from src.payments.signature import build_manifest
from src.payments.webhook import WebhookConfig, handle_webhook

SECRET = "test-webhook-secret"


def _sign(data_id: str, request_id: str, ts: int) -> str:
    manifest = build_manifest(data_id, request_id, ts)
    return hmac.new(SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def _mock_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


def test_rejects_invalid_json() -> None:
    result = handle_webhook(
        _mock_conn(),
        raw_body=b"not json",
        headers={},
        config=WebhookConfig(secret=SECRET),
    )
    assert result.status_code == 400


def test_rejects_missing_data_id() -> None:
    result = handle_webhook(
        _mock_conn(),
        raw_body=json.dumps({"action": "x"}).encode(),
        headers={},
        config=WebhookConfig(secret=SECRET),
    )
    assert result.status_code == 400


def test_rejects_invalid_signature() -> None:
    body = json.dumps({"data": {"id": "123"}}).encode()
    result = handle_webhook(
        _mock_conn(),
        raw_body=body,
        headers={"x-request-id": "req", "x-signature": "ts=1,v1=bad"},
        config=WebhookConfig(secret=SECRET),
    )
    assert result.status_code == 401


def test_accepts_valid_webhook() -> None:
    now = int(time.time())
    data_id = "123"
    request_id = "req-1"
    v1 = _sign(data_id, request_id, now)
    body = json.dumps({"data": {"id": data_id}}).encode()

    result = handle_webhook(
        _mock_conn(),
        raw_body=body,
        headers={
            "x-request-id": request_id,
            "x-signature": f"ts={now},v1={v1}",
        },
        config=WebhookConfig(secret=SECRET),
    )
    assert result.status_code == 200
    assert result.body["status"] == "queued"
