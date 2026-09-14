"""Smoke tests de S3ObjectLockAnchor con botocore stubber."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

botocore = pytest.importorskip("botocore")
from botocore.stub import Stubber

from src.audit.anchor import S3ObjectLockAnchor
from src.audit.errors import AuditAnchorError
from src.core.hashing import content_hash_bytes


@pytest.fixture
def s3_client():
    import boto3

    client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return client


def test_s3_put_creates_object(s3_client) -> None:
    anchor = S3ObjectLockAnchor(
        bucket="test-bucket",
        prefix="audit/",
        retention_days=30,
    )
    anchor._client = s3_client  # noqa: SLF001

    stubber = Stubber(s3_client)
    # head_object devuelve 404 (no existe)
    stubber.add_client_error(
        "head_object",
        service_error_code="404",
        http_status_code=404,
    )
    # put_object responde OK
    stubber.add_response("put_object", {})

    with stubber:
        record = anchor.put("close_abc", b"contenido")

    assert record.close_id == "close_abc"
    assert record.close_hash == content_hash_bytes(b"contenido").hex()
    assert "s3://test-bucket/audit/close_close_abc.bin" in record.location
    assert record.retention_until is not None


def test_s3_put_idempotent_same_content(s3_client) -> None:
    anchor = S3ObjectLockAnchor(bucket="test-bucket", prefix="audit/")
    anchor._client = s3_client  # noqa: SLF001

    data = b"mismo contenido"
    expected_hash = content_hash_bytes(data).hex()

    stubber = Stubber(s3_client)
    stubber.add_response(
        "head_object",
        {
            "Metadata": {"close-hash": expected_hash},
            "ObjectLockRetainUntilDate": datetime.now(timezone.utc),
        },
        {"Bucket": "test-bucket", "Key": "audit/close_close_x.bin"},
    )

    with stubber:
        record = anchor.put("close_x", data)

    assert record.close_hash == expected_hash


def test_s3_put_rejects_different_content(s3_client) -> None:
    anchor = S3ObjectLockAnchor(bucket="test-bucket", prefix="audit/")
    anchor._client = s3_client  # noqa: SLF001

    stubber = Stubber(s3_client)
    stubber.add_response(
        "head_object",
        {
            "Metadata": {"close-hash": "a" * 64},
            "ObjectLockRetainUntilDate": datetime.now(timezone.utc),
        },
        {"Bucket": "test-bucket", "Key": "audit/close_close_y.bin"},
    )

    with stubber, pytest.raises(AuditAnchorError):
        anchor.put("close_y", b"contenido distinto")


def test_s3_rejects_invalid_close_id() -> None:
    anchor = S3ObjectLockAnchor(bucket="test-bucket")
    with pytest.raises(AuditAnchorError):
        anchor._key("close/with/slash")  # noqa: SLF001


def test_s3_rejects_non_bytes() -> None:
    anchor = S3ObjectLockAnchor(bucket="test-bucket")
    with pytest.raises(AuditAnchorError):
        anchor.put("close_z", "no bytes")  # type: ignore[arg-type]
