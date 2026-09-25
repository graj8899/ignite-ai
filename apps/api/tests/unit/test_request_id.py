from fastapi.testclient import TestClient

from app.observability.request_id import REQUEST_ID_HEADER, is_valid_request_id


def test_is_valid_request_id_accepts_safe_values():
    assert is_valid_request_id("abc123")
    assert is_valid_request_id("test-request-id-123")
    assert is_valid_request_id("a" * 64)  # exactly at the length limit


def test_is_valid_request_id_rejects_over_long_value():
    assert not is_valid_request_id("a" * 65)


def test_is_valid_request_id_rejects_newline():
    assert not is_valid_request_id("abc\ndef")


def test_is_valid_request_id_rejects_empty_string():
    assert not is_valid_request_id("")


def test_over_long_request_id_is_replaced_with_generated_one(client: TestClient):
    supplied = "a" * 65  # header-safe (no control chars), but too long

    response = client.get("/api/health", headers={REQUEST_ID_HEADER: supplied})

    returned = response.headers.get(REQUEST_ID_HEADER)
    assert returned != supplied
    assert len(returned) == 36  # UUID4 string length
