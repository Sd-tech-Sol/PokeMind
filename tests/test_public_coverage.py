"""Public-only campaign regressions; all HTTP and card data are synthetic."""
import io
import json
import socket
from urllib.error import HTTPError

import pytest

from pokemind import public_campaign as campaign
from pokemind.cards import CatalogApiClient
from pokemind.meta import LimitlessApiClient
from pokemind.updates import OfficialSourceClient
from pokemind.cli import main
from pokemind.cards import sync_cards
from test_cards import FakeCatalogClient, _routes
from test_rules import _ready_db, _coverage, _replace_structure_rule, _insert_deck_version


class DeniedOpener:
    def __init__(self, status):
        self.status = status
        self.calls = 0

    def open(self, request, **kwargs):
        self.calls += 1
        raise HTTPError(request.full_url, self.status, "synthetic denial", {}, io.BytesIO())


@pytest.mark.parametrize("provider,factory,budgets", [
    ("tcgdex", CatalogApiClient, (3, 0, 0)),
    ("limitless", LimitlessApiClient, (0, 3, 0)),
    ("official", OfficialSourceClient, (0, 0, 2)),
])
@pytest.mark.parametrize("status", [403, 429])
def test_campaign_stops_provider_on_first_denial(local_tmp, monkeypatch, provider, factory, budgets, status):
    opener = DeniedOpener(status)
    clients = []

    def build(max_requests, **kwargs):
        client = factory(max_requests, **kwargs, opener=opener, sleep=lambda _: None)
        clients.append(client)
        return client

    monkeypatch.setattr(campaign, factory.__name__, build)
    result = campaign.run_campaign(local_tmp, "synthetic-denial", create=True, execute=True,
        tcgdex_budget=budgets[0], meta_budget=budgets[1], official_budget=budgets[2], official_scope="modern")
    assert opener.calls == result["get_attempts"] == 1
    assert result[provider]["blocked_reason"] == f"PUBLIC_SOURCE_HTTP_{status}_BLOCKED"
    # Even another direct call on the same client cannot send a new GET.
    client = clients[0]
    with pytest.raises(ValueError):
        client.probe(campaign.MODERN_URLS[0]) if provider == "official" else client.get_json("/en/sets" if provider == "tcgdex" else "/games")
    assert opener.calls == 1


@pytest.mark.parametrize("provider,factory,budgets", [
    ("tcgdex", CatalogApiClient, (3, 0, 0)),
    ("limitless", LimitlessApiClient, (0, 3, 0)),
    ("official", OfficialSourceClient, (0, 0, 2)),
])
def test_campaign_stops_on_html_challenge_without_promoting_evidence(local_tmp, monkeypatch, provider, factory, budgets):
    responses = []

    class ChallengeOpener:
        def open(self, request, **kwargs):
            response = io.BytesIO(b"<html>verify you are human</html>")
            response.geturl = lambda: request.full_url
            response.headers = {"Content-Type": "text/html"}
            responses.append(response)
            return response

    def build(max_requests, **kwargs):
        return factory(max_requests, **kwargs, opener=ChallengeOpener(), sleep=lambda _: None)

    monkeypatch.setattr(campaign, factory.__name__, build)
    result = campaign.run_campaign(local_tmp, "synthetic-challenge", create=True, execute=True,
        tcgdex_budget=budgets[0], meta_budget=budgets[1], official_budget=budgets[2], official_scope="modern")
    assert result["get_attempts"] == len(responses) == 1
    assert all(response.closed for response in responses)
    assert result[provider]["blocked_reason"] in {"PUBLIC_SOURCE_NON_JSON_BLOCKED", "PUBLIC_SOURCE_CHALLENGE_BLOCKED"}
    assert result["normative_assertions_added"] == 0


def test_cli_fr_en_and_dated_deck_tristate_are_offline(local_tmp, capsys, monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("CLI demonstration must stay offline")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    catalog = local_tmp / "synthetic-catalog.sqlite3"
    for phase in ("index", "details"):
        sync_cards(catalog, max_requests=24, phase=phase, client=FakeCatalogClient(24, _routes()))
    for lang in ("fr", "en"):
        assert main(["cards", "show", "syn1-1", "--lang", lang, "--db", str(catalog), "--json"]) == 0
        card = json.loads(capsys.readouterr().out)
        assert card["language"] == lang and card["status"] == "present"
        assert card["provenance"]["url"].startswith("https://api.tcgdex.net/")
        assert "légalité" in card["limits"][0]

    rules = _ready_db(local_tmp / "synthetic-rules.sqlite3")
    _coverage(rules)
    _replace_structure_rule(rules)
    for name, count in (("valid", 4), ("five-copies", 5)):
        _insert_deck_version(rules, name, 1, exact_confirmed=1, total_cards=60,
            cards=[("pokemon", count, "Shared Name", "SYN", "1"),
                   ("energy", 60 - count, "Basic Energy", "SYN", "6")])
    for deck, date, expected in (("valid", "2026-05-01", "legal"),
                                 ("five-copies", "2026-05-01", "not_legal"),
                                 ("valid", "2026-10-18", "unknown")):
        assert main(["rules", "check-deck", deck, "--format", "standard", "--platform", "live",
                     "--as-of", date, "--db", str(rules), "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == expected
