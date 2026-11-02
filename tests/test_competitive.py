from __future__ import annotations

import io
import json
import hashlib
from html import escape
from pathlib import Path
from urllib.error import HTTPError

import pytest

from pokemind import competitive as c


URL = "https://www.limitlesstcg.com/tournaments/123/decklists"


class Response(io.BytesIO):
    def __init__(self, body, *, headers=None, status=200):
        super().__init__(body)
        self.headers = headers or {}
        self.status = status


class Opener:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def open(self, request, timeout):
        self.calls.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def client(local_tmp, response):
    target = c.create_workspace(local_tmp, "synthetic-competitive")
    sleeps = []
    opener = Opener(response)
    return c.BoundedPages(target, opener=opener, clock=lambda: 0, sleep=sleeps.append), opener, sleeps


@pytest.mark.parametrize("url", [
    "https://play.limitlesstcg.com/api/tournaments",
    "https://www.limitlesstcg.com/tournaments",
    "https://www.limitlesstcg.com/tournaments/123?all=1",
    "https://www.limitlesstcg.com/tournaments/123#x",
    "https://www.limitlesstcg.com:443/tournaments/123",
    "https://www.limitlesstcg.com.evil.invalid/tournaments/123",
    "https://user@www.limitlesstcg.com/tournaments/123",
    "http://www.limitlesstcg.com/tournaments/123",
])
def test_narrow_url_scope(url):
    with pytest.raises(ValueError, match="URL_NOT_ALLOWED"):
        c.page_url(url)


def test_one_attempt_persistent_ledger_and_offline_cache(local_tmp):
    api, opener, sleeps = client(local_tmp, Response(b"synthetic", headers={"Content-Length": "9"}))
    assert api.get(URL) == b"synthetic"
    assert sleeps == [1]
    assert api.report["gets"] == 1 and api.report["bytes"] == 9
    again = c.BoundedPages(api.target, opener=opener, sleep=lambda _: None)
    with pytest.raises(ValueError, match="ALREADY_ATTEMPTED"):
        again.get(URL)
    assert again.cached(URL) == b"synthetic"
    assert len(opener.calls) == 1
    (api.target / "pages" / (api.report["requests"][0]["sha256"] + ".body")).write_bytes(b"changed")
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        again.cached(URL)


@pytest.mark.parametrize("response", [
    Response(b"verify you are human"),
    Response(b"captcha"),
    Response(b"x", headers={"cf-mitigated": "challenge"}),
    Response(b"x", headers={"Content-Encoding": "gzip"}),
    Response(b"x", headers={"Content-Length": str(c.MAX_RESPONSE + 1)}),
    Response(b"x", headers={"Content-Length": "2"}),
    Response(b"x", status=403),
])
def test_response_refusal_closes_provider(local_tmp, response):
    api, opener, _ = client(local_tmp, response)
    with pytest.raises(ValueError):
        api.get(URL)
    with pytest.raises(ValueError, match="PROVIDER_CLOSED"):
        api.get("https://www.limitlesstcg.com/tournaments/456")
    assert len(opener.calls) == 1
    assert api.report["gets"] == 1
    assert api.report["stopped"]


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_http_denial_no_retry(local_tmp, status):
    api, opener, _ = client(local_tmp, HTTPError(URL, status, "synthetic", {}, io.BytesIO(b"unused")))
    with pytest.raises(ValueError):
        api.get(URL)
    assert api.report["requests"][0]["http_status"] == status
    assert len(opener.calls) == 1


def test_byte_cap_and_get_envelope(local_tmp, monkeypatch):
    api, opener, sleeps = client(local_tmp, Response(b"abcdef"))
    monkeypatch.setattr(c, "MAX_RESPONSE", 5)
    with pytest.raises(ValueError, match="RESPONSE_CAP"):
        api.get(URL)
    assert api.report["bytes"] == 5
    assert api.report["requests"][0]["bytes"] == 5


def test_interruption_cannot_restart_network(local_tmp):
    api, opener, _ = client(local_tmp, Response(b"unused"))
    api.report["requests"].append({"url": URL, "state": "reserved"})
    api._save()
    resumed = c.BoundedPages(api.target, opener=opener)
    with pytest.raises(ValueError, match="PROVIDER_CLOSED"):
        resumed.get("https://www.limitlesstcg.com/robots.txt")
    assert not opener.calls


def test_existing_workspace_never_reused(local_tmp):
    c.create_workspace(local_tmp, "synthetic-competitive")
    with pytest.raises(FileExistsError):
        c.create_workspace(local_tmp, "synthetic-competitive")


@pytest.mark.parametrize("budget", ["gets", "bytes"])
def test_cumulative_envelope_checked_before_io(local_tmp, budget):
    api, opener, _ = client(local_tmp, Response(b"unused"))
    api.report[budget] = c.MAX_GETS if budget == "gets" else c.MAX_BYTES
    api._save()
    with pytest.raises(ValueError, match="BUDGET_EXHAUSTED"):
        api.get(URL)
    assert not opener.calls


def test_spacing_across_requests_and_explicit_batch_close(local_tmp):
    api, opener, sleeps = client(local_tmp, Response(b"synthetic"))
    api.get(URL)
    opener.response = Response(b"another synthetic")
    api.get("https://www.limitlesstcg.com/tournaments/456")
    assert sleeps == [1, 1]
    api.close()
    with pytest.raises(ValueError, match="PROVIDER_CLOSED"):
        c.BoundedPages(api.target, opener=opener).get("https://www.limitlesstcg.com/robots.txt")
    assert len(opener.calls) == 2


def test_cache_rejects_digest_path_traversal(local_tmp):
    api, opener, _ = client(local_tmp, Response(b"synthetic"))
    api.get(URL)
    api.report["requests"][0]["sha256"] = "../../outside"
    with pytest.raises(ValueError, match="DIGEST_INVALID"):
        api.cached(URL)


def synthetic_list():
    fixture = Path(__file__).parent / "fixtures/decks/valid_en.txt"
    parsed = c.parse_deck_export(fixture.read_text(encoding="utf-8"))
    result = '<div data-text-decklist>'
    for kind, label in (("pokemon", "Pokémon"), ("trainer", "Trainer"), ("energy", "Energy")):
        cards = [card for card in parsed.cards if card.card_type == kind]
        result += '<div class="decklist-column"><div class="decklist-column-heading">'
        result += f'{label} ({sum(card.quantity for card in cards)})</div>'
        for card in cards:
            result += (f'<div class="decklist-card" data-set="{card.set_code}" data-number="{card.collector_number}" data-lang="en">'
                       f'<span class="card-count">{card.quantity}</span><span class="card-name">{escape(card.name)}</span>'
                       '<span class="card-price">999999</span></div>')
        result += '</div>'
    return (result+'</div>').encode('utf-8')


def synthetic_event():
    return (b'<div class="infobox-heading">Synthetic Regional</div>'
            b'<div class="infobox-line">10th October 2026 \xe2\x80\xa2 6 Players</div>'
            b'<a href="/decks/?time=all&amp;format=SYN">Synthetic range</a>'
            b'<table><tr data-rank="1" data-name="DO_NOT_STORE" data-deck="Synthetic Alpha">'
            b'<td><a href="/decks/list/456">list</a></td></tr></table>')


def synthetic_index():
    return (b'<table><tr><td>10 Oct 26</td><td>XX</td><td><a href="/tournaments/123">Synthetic Regional</a></td>'
            b'<td><img alt="standard"></td><td>6</td><td>DO_NOT_STORE</td></tr></table>')


def synthetic_qualified():
    event = c.parse_event(synthetic_event(), "https://www.limitlesstcg.com/tournaments/123", as_of="2026-10-22")
    return c.qualify_standard(event, synthetic_index())


def test_parse_complete_list_uses_text_columns_not_prices():
    text = c.parse_list(synthetic_list())
    assert c.parse_deck_export(text).total_cards == 60
    assert "999999" not in text
    assert c.serialize_deck(c.parse_deck_export(text).cards) == text


@pytest.mark.parametrize("change", [
    lambda b: b.replace(b'data-lang="en"', b'data-lang="unknown"', 1),
    lambda b: b.replace(b'data-set=', b'unknown-set=', 1),
    lambda b: b.replace(b'Pok\xc3\xa9mon (', b'Unknown (', 1),
    lambda b: b.replace(b'class="card-count">4', b'class="card-count">3', 1),
    lambda b: b.replace(b'<div data-text-decklist>', b'<div>'),
    lambda b: b + b,
])
def test_incomplete_or_changed_list_refused(change):
    with pytest.raises(ValueError):
        c.parse_list(change(synthetic_list()))


def test_event_dates_placements_format_and_no_player_data():
    event = synthetic_qualified()
    assert event["date"] == "2026-10-10" and event["format"] == "standard"
    assert event["participant_count"] == 6 and event["published_result_rows"] == 1
    assert event["match_mode"] == "unknown"
    assert "DO_NOT_STORE" not in json.dumps(event)
    with pytest.raises(ValueError, match="FUTURE_EVENT"):
        c.parse_event(synthetic_event(), "https://www.limitlesstcg.com/tournaments/123", as_of="2026-10-09")
    with pytest.raises(ValueError, match="INDEX_MISMATCH"):
        c.qualify_standard(event, synthetic_index().replace(b'alt="standard"', b'alt="expanded"'))
    with pytest.raises(ValueError, match="DATE_MISMATCH"):
        c.qualify_standard(event, synthetic_index().replace(b'10 Oct', b'11 Oct'))


def test_statistics_explicit_subset_no_winrate():
    payload = b'<tr data-count="3"><td>1</td><td></td><td>Alpha</td><td>3</td><td>75%</td><td>99</td></tr>'
    result = c.parse_statistics(payload)
    assert result["denominator"] == 3
    assert result["match_winrates"] is None
    assert result["scope"] == "published_result_subset_not_all_entrants"


def test_public_sqlite_import_idempotence_offline_export_and_conflict(local_tmp, record_testsuite_property):
    target = c.create_workspace(local_tmp, "synthetic-competitive")
    db = target / "public.sqlite3"
    event = synthetic_qualified()
    text = c.parse_list(synthetic_list())
    item = {**event["placements"][0], "page_sha256": hashlib.sha256(synthetic_list()).hexdigest(),
            "fetched_at": "2026-10-22T20:00:00Z", "deck_text": text}
    for _ in range(2):
        report = c.store_event(local_tmp, db, event, [item])
        assert report == {"event_id": "123", "lists": 1, "integrity": "ok", "foreign_key_errors": 0}
    before = db.read_bytes()
    summary = c.competitive_summary(local_tmp, db)
    assert summary["sampled_lists"] == 1 and summary["match_winrates"] is None
    assert c.competitive_export(local_tmp, db, "123", 1) == text
    assert db.read_bytes() == before
    connection = c.connect_readonly(db)
    try:
        assert connection.execute('SELECT COUNT(*) FROM deck_versions').fetchone()[0] == 0
        assert "DO_NOT_STORE" not in json.dumps([tuple(r) for r in connection.execute('SELECT * FROM meta_competitive_events')])
    finally:
        connection.close()
    with pytest.raises(ValueError, match="EXISTING_LIST_CONFLICT"):
        c.store_event(local_tmp, db, event, [{**item, "page_sha256": "0"*64}])
    assert db.read_bytes() == before
    with pytest.raises(ValueError, match="PLACEMENT_MISMATCH"):
        c.store_event(local_tmp, db, event, [{**item, "placement": 2}])
    record_testsuite_property("public_competitive_reproduction", json.dumps({
        "scope": "SYNTHETIC_COMPETITIVE_PAGES_ONLY", "events": 1, "lists": 1,
        "total_cards": 60, "idempotent": True, "read_only_offline_export": True,
        "integrity": "ok", "foreign_key_errors": 0, "owner_database_opened": False,
        "real_public_cache_verified": False,
    },sort_keys=True))


def test_no_owner_database_fallback_or_outside_namespace(local_tmp, monkeypatch, capsys):
    from pokemind import cli
    def forbidden(*args, **kwargs):
        raise AssertionError("owner database resolver must not run")
    monkeypatch.setattr(cli, "_db_for", forbidden)
    for args in (["meta", "competitive-summary", "--json"],
                 ["meta", "competitive-export", "--event", "123", "--placement", "1", "--json"],
                 ["meta", "competitive-summary", "--db", str(local_tmp / "owner.sqlite3"), "--json"]):
        assert cli.main(args) == 2
        assert json.loads(capsys.readouterr().out)["ok"] is False


def test_offline_importer_and_cli_end_to_end(local_tmp, monkeypatch, capsys):
    import importlib.util
    from pokemind import cli
    spec = importlib.util.spec_from_file_location("import_competitive_pages", Path(__file__).resolve().parents[1] / "scripts/import_competitive_pages.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.import_cached(local_tmp, "synthetic-competitive", ["123"], as_of="2026-10-22")["maximum_lists"] == 16
    assert not (local_tmp / "data").exists()
    api, opener, _ = client(local_tmp, Response(synthetic_index()))
    stats = b'<tr data-count="1"><td>1</td><td></td><td>Synthetic Alpha</td><td>1</td><td>100%</td><td>9</td></tr>'
    for url, body in ((c.INDEX_URL, synthetic_index()),
                      ("https://www.limitlesstcg.com/tournaments/123", synthetic_event()),
                      ("https://www.limitlesstcg.com/tournaments/123/statistics", stats),
                      ("https://www.limitlesstcg.com/decks/list/456", synthetic_list())):
        opener.response = Response(body)
        api.get(url)
    api.close()
    def no_get(*args):
        raise AssertionError("offline path must never call GET")
    monkeypatch.setattr(c.BoundedPages, "get", no_get)
    for _ in range(2):
        result = module.import_cached(local_tmp, "synthetic-competitive", ["123"], as_of="2026-10-22", apply=True)
        assert result["sampled_lists"] == 1 and result["network_used"] is False
    monkeypatch.setattr(cli, "find_project_root", lambda: local_tmp)
    db = api.target / "public.sqlite3"
    assert cli.main(["meta", "competitive-summary", "--db", str(db), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["sampled_lists"] == 1
    assert cli.main(["meta", "competitive-export", "--db", str(db), "--event", "123", "--placement", "1", "--json"]) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["total_cards"] == 60 and c.parse_deck_export(exported["text"]).total_cards == 60
    assert exported["live_legality"] == "unknown"
