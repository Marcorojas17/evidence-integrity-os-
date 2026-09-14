"""Smoke tests de AWSKMS con botocore stubber."""

from __future__ import annotations

import pytest

from src.core.kms import AWSKMS, KmsError


botocore = pytest.importorskip("botocore")
from botocore.stub import Stubber


@pytest.fixture
def aws_kms_client():
    import boto3

    client = boto3.client(
        "kms",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return client


def test_aws_sign_returns_32_bytes(aws_kms_client) -> None:
    kms = AWSKMS(region="us-east-1")
    kms._client = aws_kms_client  # noqa: SLF001

    stubber = Stubber(aws_kms_client)
    fake_mac = b"\x42" * 32
    stubber.add_response(
        "generate_mac",
        {"Mac": fake_mac},
        {
            "KeyId": "kms-key-1",
            "MacAlgorithm": "HMAC_SHA_256",
            "Message": b"payload",
        },
    )
    with stubber:
        result = kms.hmac_sign("kms-key-1", b"payload")
    assert result == fake_mac


def test_aws_verify_valid(aws_kms_client) -> None:
    kms = AWSKMS(region="us-east-1")
    kms._client = aws_kms_client  # noqa: SLF001

    stubber = Stubber(aws_kms_client)
    stubber.add_response(
        "verify_mac",
        {"MacValid": True},
        {
            "KeyId": "kms-key-1",
            "MacAlgorithm": "HMAC_SHA_256",
            "Message": b"payload",
            "Mac": b"\x42" * 32,
        },
    )
    with stubber:
        assert kms.hmac_verify("kms-key-1", b"payload", b"\x42" * 32)


def test_aws_verify_invalid(aws_kms_client) -> None:
    kms = AWSKMS(region="us-east-1")
    kms._client = aws_kms_client  # noqa: SLF001

    stubber = Stubber(aws_kms_client)
    stubber.add_client_error(
        "verify_mac",
        service_error_code="KMSInvalidMacException",
        http_status_code=400,
    )
    with stubber:
        assert not kms.hmac_verify("kms-key-1", b"payload", b"\x00" * 32)


def test_aws_sign_rejects_non_bytes(aws_kms_client) -> None:
    kms = AWSKMS(region="us-east-1")
    kms._client = aws_kms_client  # noqa: SLF001
    with pytest.raises(KmsError):
        kms.hmac_sign("kms-key-1", "no bytes")  # type: ignore[arg-type]
