"""Public error categories without response bodies or exception details."""
import io
from urllib.error import HTTPError, URLError

import pytest

from pokemind.cards import (ApiNotFound, CatalogApiClient, CatalogError,
                            MAX_JSON_BYTES, NetworkFailure)
from pokemind.security import neutral_exception_code
from test_cards import FakeResponse, SequenceOpener


class Response(FakeResponse):
    status = 200
    closed = False

    def close(self):
        self.closed = True


@pytest.mark.parametrize("length", ["not-a-number", "-1", str(MAX_JSON_BYTES + 1)])
def test_unusable_length_is_categorized_closed_and_counted(length):
    response = Response([])
    response.headers["Content-Length"] = length
    client = CatalogApiClient(1, opener=SequenceOpener([response]), interval=0)
    with pytest.raises(CatalogError) as raised:
        client.get_json("/en/cards")
    code = neutral_exception_code(raised.value, "TCGDEX")
    assert code == ("TCGDEX_RESPONSE_TOO_LARGE" if length == str(MAX_JSON_BYTES + 1)
                    else "TCGDEX_RESPONSE_LENGTH_INVALID")
    assert client.requests_made == 1 and client.last_http_status == 200 and response.closed


def test_malformed_json_never_echoes_response_and_preserves_observed_status():
    response = Response([])
    response.raw = b"malformed synthetic response with LOCAL_SENTINEL"
    client = CatalogApiClient(1, opener=SequenceOpener([response]), interval=0)
    with pytest.raises(CatalogError) as raised:
        client.get_json("/en/cards")
    assert neutral_exception_code(raised.value, "TCGDEX") == "TCGDEX_RESPONSE_JSON_INVALID"
    assert "LOCAL_SENTINEL" not in str(raised.value)
    assert response.closed and client.last_http_status == 200


@pytest.mark.parametrize("status", [401, 403, 429])
def test_access_denial_remains_terminal_without_retry(status):
    body = io.BytesIO(b"LOCAL_SENTINEL")
    error = HTTPError("https://api.tcgdex.net/v2/en/cards", status, "synthetic", {}, body)
    client = CatalogApiClient(5, opener=SequenceOpener([error]), interval=0, stop_on_access_denial=True)
    with pytest.raises(NetworkFailure):
        client.get_json("/en/cards")
    with pytest.raises(NetworkFailure):
        client.get_json("/fr/cards")
    assert client.requests_made == 1 and client.last_http_status == status and body.closed


def test_retry_http_status_and_closure_are_recorded_without_body():
    bodies = [io.BytesIO(b"LOCAL_SENTINEL") for _ in range(3)]
    errors = [HTTPError("https://api.tcgdex.net/v2/en/cards", 503, "synthetic", {}, body)
              for body in bodies]
    client = CatalogApiClient(3, opener=SequenceOpener(errors), interval=0, sleep=lambda _: None)
    with pytest.raises(NetworkFailure) as raised:
        client.get_json("/en/cards")
    assert neutral_exception_code(raised.value, "TCGDEX") == "TCGDEX_HTTP_503"
    assert client.requests_made == 3 and client.last_http_status == 503
    assert all(body.closed for body in bodies)


def test_network_failure_does_not_reuse_previous_http_status():
    body = io.BytesIO(b"synthetic")
    errors = [HTTPError("https://api.tcgdex.net/v2/en/cards", 503, "synthetic", {}, body),
              URLError("LOCAL_SENTINEL")]
    client = CatalogApiClient(2, opener=SequenceOpener(errors), interval=0, sleep=lambda _: None)
    with pytest.raises(NetworkFailure) as raised:
        client.get_json("/en/cards")
    assert neutral_exception_code(raised.value, "TCGDEX") == "TCGDEX_NETWORK_UNAVAILABLE"
    assert client.last_http_status is None and client.requests_made == 2 and body.closed
    assert "LOCAL_SENTINEL" not in str(raised.value)


def test_absent_resource_closes_response_and_keeps_neutral_code():
    body = io.BytesIO(b"synthetic")
    client = CatalogApiClient(1, opener=SequenceOpener([
        HTTPError("https://api.tcgdex.net/v2/en/cards", 404, "synthetic", {}, body),
    ]), interval=0)
    with pytest.raises(ApiNotFound) as raised:
        client.get_json("/en/cards/synthetic-1")
    assert neutral_exception_code(raised.value, "TCGDEX") == "TCGDEX_HTTP_404"
    assert client.last_http_status == 404 and body.closed
