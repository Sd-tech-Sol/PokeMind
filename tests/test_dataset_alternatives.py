"""Offline boundaries of the retained REST path; no dataset importer is claimed.

All records below are synthetic. Downloaded review samples are never fixtures.
"""
import copy
from contextlib import closing
import socket
import sqlite3

import pytest

from pokemind import public_campaign as campaign
from pokemind.cards import cards_coverage, show_card
from test_cards import FakeCatalogClient, _routes
from test_public_card_selection import _db, _run


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Dataset review regression must remain offline")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.mark.parametrize("foreign", [
    [{"id": "syn1-1", "name": "Synthetic external card", "number": "1"}],
    "id,name,number\nsyn1-1,Synthetic external card,1\n",
    {"id": "syn1-1", "name": "Synthetic external card", "number": "1"},
    {"id": "syn1-1", "name": "Synthetic external card", "number": "1", "license": "MIT"},
])
def test_external_shapes_cannot_enter_rest_catalogue(local_tmp, monkeypatch, foreign):
    routes = copy.deepcopy(_routes())
    routes["/en/cards/syn1-1"] = foreign
    result, client = _run(local_tmp, monkeypatch, ids=["syn1-1"], create=True, routes=routes)
    assert result["tcgdex"]["stopped_reason"] == "source_error"
    assert client.calls == [("/en/cards/syn1-1", None)]
    assert cards_coverage(_db(local_tmp))["unique_printings"] == 0
    with closing(sqlite3.connect(_db(local_tmp))) as connection:
        assert connection.execute("SELECT COUNT(*) FROM catalog_translations").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0] == 0
    # An MIT label cannot turn an unrelated shape into a TCGdex detail. This
    # boundary does not implement or certify a dataset licence validator.


@pytest.mark.parametrize("wrong_url", [
    "https://raw.githubusercontent.com/synthetic/dataset/pinned/cards.json",
    "https://api.tcgdex.net/v2/fr/cards/syn1-3",
])
def test_foreign_or_wrong_language_provenance_cannot_commit(local_tmp, monkeypatch, wrong_url):
    _run(local_tmp, monkeypatch, ids=["syn1-1"], create=True)
    before = show_card(_db(local_tmp), "syn1-1", "en")

    class MisattributedClient(FakeCatalogClient):
        def get_json(self, path, params=None):
            payload, _ = super().get_json(path, params)
            return payload, wrong_url

    monkeypatch.setattr(campaign, "CatalogApiClient",
                        lambda budget, **kwargs: MisattributedClient(budget, _routes()))
    result = campaign.run_campaign(local_tmp, "synthetic-selection", execute=True,
        phase="details", tcgdex_budget=4, meta_budget=0, official_budget=0,
        card_ids=["syn1-3"])
    assert result["get_attempts"] == 1
    assert result["tcgdex"]["stopped_reason"] == "source_error"
    assert cards_coverage(_db(local_tmp))["unique_printings"] == 1
    assert show_card(_db(local_tmp), "syn1-1", "en") == before
    with closing(sqlite3.connect(_db(local_tmp))) as connection:
        assert connection.execute("SELECT COUNT(*) FROM catalog_printings WHERE tcgdex_id='syn1-3'").fetchone()[0] == 0


def test_missing_english_is_not_invented_from_french(local_tmp, monkeypatch):
    routes = copy.deepcopy(_routes())
    routes["/en/cards/syn1-1"] = "NOT_FOUND"
    result, _ = _run(local_tmp, monkeypatch, ids=["syn1-1"], create=True, routes=routes)
    assert result["tcgdex"]["selection_resolved"]
    english = show_card(_db(local_tmp), "syn1-1", "en")
    french = show_card(_db(local_tmp), "syn1-1", "fr")
    assert english["status"] == "absent" and english["name"] is None
    assert english["effect"] is None and french["status"] == "present"
    assert english["provenance"]["url"].endswith("/en/cards/syn1-1")
    assert french["provenance"]["url"].endswith("/fr/cards/syn1-1")
    again, client = _run(local_tmp, monkeypatch, ids=["syn1-1"], routes=routes)
    assert again["get_attempts"] == 0 and not client.calls
