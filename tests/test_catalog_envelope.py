"""Cumulative body cap and strict first-error collection boundaries."""
import importlib.util
import io
from pathlib import Path
from urllib.error import HTTPError

import pytest

from pokemind.cards import CatalogApiClient, NetworkFailure, RequestBudgetExhausted
from test_cards import SequenceOpener


class Stream(io.BytesIO):
    status = 200

    def __init__(self, body, length=None):
        super().__init__(body)
        self.headers = {"Content-Type": "application/json"}
        if length is not None:
            self.headers["Content-Length"] = str(length)

    def geturl(self):
        return "https://api.tcgdex.net/v2/en/cards"


def test_declared_body_over_remaining_budget_is_never_read():
    first, second = Stream(b"[]", 2), Stream(b"[1]", 3)
    client = CatalogApiClient(3, maximum_body_bytes=4, interval=0,
                              opener=SequenceOpener([first, second]))
    assert client.get_json("/en/cards")[0] == []
    with pytest.raises(RequestBudgetExhausted, match="TCGDEX_BODY_BUDGET_EXHAUSTED"):
        client.get_json("/en/cards")
    assert client.body_bytes_read == 2 and client.requests_made == 2 and second.closed


def test_unknown_length_does_not_read_one_byte_past_cap():
    response = Stream(b"[123456789]")
    client = CatalogApiClient(2, maximum_body_bytes=4, interval=0,
                              opener=SequenceOpener([response]))
    with pytest.raises(RequestBudgetExhausted):
        client.get_json("/en/cards")
    with pytest.raises(RequestBudgetExhausted):
        client.get_json("/en/cards")
    assert client.body_bytes_read == 4 and client.requests_made == 1 and response.closed


def test_exact_known_length_can_finish_at_cap():
    client = CatalogApiClient(1, maximum_body_bytes=2, interval=0,
                              opener=SequenceOpener([Stream(b"[]", 2)]))
    assert client.get_json("/en/cards")[0] == [] and client.body_bytes_read == 2


def test_strict_source_error_does_not_retry():
    error = HTTPError("https://api.tcgdex.net/v2/en/cards", 503, "synthetic", {}, io.BytesIO(b"sentinel"))
    client = CatalogApiClient(10, maximum_attempts=1, interval=0,
                              opener=SequenceOpener([error]))
    with pytest.raises(NetworkFailure, match="TCGDEX_HTTP_503"):
        client.get_json("/en/cards")
    assert client.requests_made == 1 and client.body_bytes_read == 0


def test_detail_sync_stops_the_whole_phase_when_next_body_cannot_fit(tmp_path):
    from pokemind.cards import sync_cards
    from test_cards import FakeCatalogClient, _routes
    db = tmp_path / "synthetic.sqlite3"
    sync_cards(db, max_requests=4, phase="balanced", client=FakeCatalogClient(4, _routes()))
    client = CatalogApiClient(5, maximum_body_bytes=1, interval=0,
                              opener=SequenceOpener([Stream(b"{}", 2)]))
    result = sync_cards(db, max_requests=5, phase="details", client=client)
    assert result["error"] == "TCGDEX_BODY_BUDGET_EXHAUSTED"
    assert result["stopped_reason"] == "body_budget_exhausted"
    assert client.requests_made == 1 and client.body_bytes_read == 0


def runner():
    spec = importlib.util.spec_from_file_location("public_catalog_runner", Path(__file__).parents[1] / "scripts/collect_public_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preview_creates_nothing_and_existing_campaign_is_never_reused(tmp_path):
    module = runner()
    assert module.collect(tmp_path, "synthetic")["status"] == "DRY_RUN"
    assert not list(tmp_path.iterdir())
    target = tmp_path / "data/local/public-campaigns/lot-i-synthetic"
    target.mkdir(parents=True)
    (target / "sentinel").write_text("unchanged")
    with pytest.raises(FileExistsError):
        module.collect(tmp_path, "synthetic", execute=True)
    assert (target / "sentinel").read_text() == "unchanged"


def test_redirect_closes_body_and_never_follows():
    stream = Stream(b"unbounded redirect body")
    with pytest.raises(NetworkFailure, match="TCGDEX_REDIRECT_STOPPED"):
        runner().NoRedirect().redirect_request(None, stream, 302, "", {}, "https://api.tcgdex.net/v2/fr/cards")
    assert stream.closed


def test_collection_stops_after_first_source_error_and_keeps_cumulative_counts(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, "require_public_database", lambda *_: None)
    calls = []

    def sync(db, *, max_requests, phase, client):
        calls.append(phase)
        client.requests_made = 3
        client.body_bytes_read = 17
        client.last_http_status = 503
        return {"error": "TCGDEX_HTTP_503", "stopped_reason": "source_error", "coverage": {
            "unique_printings": 2, "languages": {lang: {"details_present": 0} for lang in ("en", "fr")}}}

    monkeypatch.setattr(module, "sync_cards", sync)
    report = module.collect(tmp_path, "synthetic", execute=True)
    assert calls == ["index"] and report["status"] == "SOURCE_STOP"
    assert report["get_attempts"] == 3 and report["body_bytes_read"] == 17
    assert report["maximum_gets_respected"] and report["maximum_body_bytes_respected"]


def test_collection_carries_both_remaining_budgets_between_clients(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, "require_public_database", lambda *_: None)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    limits = []

    def sync(db, *, max_requests, phase, client):
        limits.append((max_requests, client.maximum_body_bytes))
        client.requests_made = max_requests
        client.body_bytes_read = 70 if len(limits) == 1 else 30
        return {"error": None, "stopped_reason": "budget_exhausted", "coverage": {
            "complete": False, "discovery": {"complete": False}, "unique_printings": 1,
            "languages": {lang: {"details_present": 0} for lang in ("en", "fr")}}}

    monkeypatch.setattr(module, "sync_cards", sync)
    report = module.collect(tmp_path, "synthetic", execute=True,
                            maximum_gets=150, maximum_body_bytes=100)
    assert limits == [(100, 100), (50, 30)]
    assert report["status"] == "ENVELOPE_STOP"
    assert report["get_attempts"] == 150 and report["body_bytes_read"] == 100
