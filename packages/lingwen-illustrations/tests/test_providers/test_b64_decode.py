"""Test shared b64_json envelope decoder (Phase 96 _b64_decode helper)."""
from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock

import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers._b64_decode import decode_b64_envelope


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    fake.json.return_value = body
    return fake


def test_decode_returns_b64_decoded_bytes():
    b64 = base64.b64encode(b"hello-world-bytes").decode("ascii")
    api_body = {"created": 1234, "data": [{"b64_json": b64}]}
    resp = _json_response(api_body)
    result = decode_b64_envelope(resp, provider="openai")
    assert result == b"hello-world-bytes"


def test_decode_picks_first_data_item():
    b64_first = base64.b64encode(b"FIRST").decode("ascii")
    b64_second = base64.b64encode(b"SECOND").decode("ascii")
    api_body = {"data": [{"b64_json": b64_first}, {"b64_json": b64_second}]}
    resp = _json_response(api_body)
    assert decode_b64_envelope(resp, provider="openai") == b"FIRST"


def test_decode_malformed_json_raises_with_provider():
    resp = MagicMock()
    resp.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="stability")
    assert exc.value.provider == "stability"
    assert exc.value.retryable is True


def test_decode_missing_data_array_raises():
    resp = _json_response({"created": 1234, "no_data_here": []})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert exc.value.provider == "openai"


def test_decode_empty_data_array_raises():
    resp = _json_response({"data": []})
    with pytest.raises(GenerateError) as exc:  # noqa: F841
        decode_b64_envelope(resp, provider="openai")


def test_decode_missing_b64_json_field_raises():
    resp = _json_response({"data": [{"url": "https://x"}]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert "b64_json" in str(exc.value)


def test_decode_invalid_base64_raises():
    resp = _json_response({"data": [{"b64_json": "!!!not-base64!!!"}]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert exc.value.provider == "openai"


def test_decode_non_dict_data_item_raises():
    resp = _json_response({"data": ["raw-base64-string"]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert "object" in str(exc.value)
