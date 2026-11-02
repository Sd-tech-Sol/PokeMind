"""No network: public fixed queries, cumulative caps, terminal denial and retry."""
import io
import json
from urllib.error import HTTPError

import pytest

from pokemind.cards import CatalogError, NetworkFailure, RequestBudgetExhausted
from pokemind.tcgdex_batch import BatchClient, ENDPOINT


class Response(io.BytesIO):
    status = 200

    def __init__(self, value, *, raw=None, length=True, url=ENDPOINT):
        super().__init__(raw if raw is not None else json.dumps(value).encode())
        self.url = url
        self.headers = {"Content-Type": "application/json"}
        if length:
            self.headers["Content-Length"] = str(len(self.getvalue()))

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def open(self, request, **kwargs):
        self.requests.append(request)
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def test_fixed_query_reads_details_in_one_public_post():
    opener = Opener(Response({"data": {"cards": []}}))
    client = BatchClient(opener=opener, sleep=lambda _: None)
    assert client.page("cards", "fr", 1) == []
    request = opener.requests[0]
    query = json.loads(request.data)["query"]
    assert request.get_method() == "POST" and request.full_url == ENDPOINT
    assert 'filters: {}' in query and 'itemsPerPage: 100' in query and '@locale(lang: "fr")' in query
    assert "attacks" in query and "image" not in query and "mutation" not in query
    assert not request.has_header("Authorization") and client.requests_made == 1
    assert client.last_evidence["operation"] == "query" and client.last_raw


@pytest.mark.parametrize("status", [401, 403, 429])
def test_denial_is_closed_and_blocks_every_following_request(status):
    stream = io.BytesIO(b"challenge never read")
    opener = Opener(HTTPError(ENDPOINT, status, "synthetic", {}, stream))
    client = BatchClient(opener=opener, sleep=lambda _: None)
    with pytest.raises(NetworkFailure, match="BLOCKED"):
        client.page("cards", "en", 1)
    with pytest.raises(NetworkFailure, match="BLOCKED"):
        client.page("cards", "fr", 1)
    assert len(opener.requests) == 1 and stream.closed and client.body_bytes_read == 0


def test_transient_retry_counts_all_attempts_under_same_budget():
    stream = io.BytesIO(b"server error not read")
    opener = Opener(HTTPError(ENDPOINT, 503, "synthetic", {}, stream), Response({"data": {"sets": []}}))
    sleeps = []
    client = BatchClient(opener=opener, sleep=sleeps.append)
    assert client.page("sets", "en", 1) == []
    assert client.requests_made == 2 and stream.closed and 3 in sleeps and .5 in sleeps


def test_three_failed_attempts_are_terminal_for_the_call():
    bodies = [io.BytesIO(b"synthetic") for _ in range(3)]
    opener = Opener(*(HTTPError(ENDPOINT, 503, "synthetic", {}, body) for body in bodies))
    client = BatchClient(opener=opener, sleep=lambda _: None)
    with pytest.raises(NetworkFailure, match="HTTP_503"):
        client.page("cards", "en", 1)
    assert client.requests_made == 3 and all(body.closed for body in bodies)


@pytest.mark.parametrize("length", [True, False])
def test_read_limit_never_uses_a_sentinel_byte_past_global_cap(length):
    response = Response({}, raw=b"x" * 100, length=length)
    client = BatchClient(maximum_body_bytes=7, opener=Opener(response))
    with pytest.raises(RequestBudgetExhausted):
        client.page("cards", "en", 1)
    assert client.body_bytes_read == (0 if length else 7) and response.closed


@pytest.mark.parametrize("value", [
    {"data": {"cards": []}, "errors": [{"message": "synthetic secret"}]},
    {"data": {"cards": [None]}},
    {"data": {"cards": [{}] * 101}},
])
def test_partial_graphql_or_bad_page_is_not_accepted(value):
    client = BatchClient(opener=Opener(Response(value)))
    with pytest.raises(CatalogError) as exc:
        client.page("cards", "en", 1)
    assert "synthetic secret" not in str(exc.value)


def test_non_json_challenge_blocks_future_requests():
    response = Response({}, raw=b"<html>challenge</html>")
    response.headers["Content-Type"] = "text/html"
    client = BatchClient(opener=Opener(response))
    with pytest.raises(NetworkFailure, match="NON_JSON_BLOCKED"):
        client.page("cards", "en", 1)
    assert client.body_bytes_read == 0 and response.closed


def test_known_item_serialization_failure_is_restored_by_exact_rest_detail():
    broken = {"data": {"cards": [{"id": "syn-1", "attacks": [None]}]},
              "errors": [{"message": "synthetic missing name", "path": ["cards", 0, "attacks", 0, "name"]}]}
    complete = {"id": "syn-1", "name": "Synthetic", "attacks": [{"damage": 10}]}
    post, rest = Response(broken), Response(complete, url="https://api.tcgdex.net/v2/en/cards/syn-1")
    sizes = len(post.getvalue()) + len(rest.getvalue())
    opener = Opener(post, rest)
    client = BatchClient(opener=opener, sleep=lambda _: None)
    assert client.page("cards", "en", 1) == [complete]
    assert client.requests_made == 2 and client.body_bytes_read == sizes
    assert [r.get_method() for r in opener.requests] == ["POST", "GET"]
    assert client.last_evidence["rest_repairs"][0]["source_url"] == "https://api.tcgdex.net/v2/en/cards/syn-1"


def test_repair_cannot_reset_body_budget_or_continue_after_access_denial():
    broken = {"data": {"cards": [{"id": "syn-1"}]},
              "errors": [{"path": ["cards", 0, "attacks"]}]}
    post = Response(broken)
    size = len(post.getvalue())
    opener = Opener(post)
    client = BatchClient(maximum_body_bytes=size, opener=opener, sleep=lambda _: None)
    with pytest.raises(RequestBudgetExhausted):
        client.page("cards", "en", 1)
    assert client.requests_made == 1 and client.body_bytes_read == size
    body = io.BytesIO(b"synthetic access denial")
    opener = Opener(Response(broken), HTTPError("https://api.tcgdex.net/v2/en/cards/syn-1", 403, "", {}, body))
    client = BatchClient(opener=opener, sleep=lambda _: None)
    with pytest.raises(NetworkFailure):
        client.page("cards", "en", 1)
    with pytest.raises(NetworkFailure):
        client.page("cards", "fr", 1)
    assert client.requests_made == 2 and body.closed


def test_missing_query_uses_exact_id_and_escaped_literal():
    opener = Opener(Response({"data": {"p0": None}}))
    client = BatchClient(opener=opener)
    assert client.missing("cards", "fr", ['syn-"quoted']) == {'syn-"quoted': None}
    query = json.loads(opener.requests[0].data)["query"]
    assert 'id: "eq:syn-\\"quoted"' in query


@pytest.mark.parametrize("kind,lang,page", [("mutation", "en", 1), ("cards", "de", 1), ("cards", "en", 0)])
def test_invalid_scope_cannot_start_a_request(kind, lang, page):
    opener = Opener()
    with pytest.raises(CatalogError):
        BatchClient(opener=opener).page(kind, lang, page)
    assert not opener.requests
