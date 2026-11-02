"""Synthetic page rollback, observed membership, language absence and provenance."""
from contextlib import closing
import hashlib

import pytest

from pokemind import catalog_batch_store as store
from pokemind.cards import CatalogError, cards_coverage, show_card
from pokemind.database import connect_writable, initialize_schema
from pokemind.tcgdex_batch import ENDPOINT


def card(entity_id="syn-1", language="en"):
    return {"id": entity_id, "localId": entity_id.split("-")[-1],
            "name": "Synthetic Flame" if language == "en" else "Flamme fictive",
            "category": "Pokemon" if language == "en" else "Pokémon",
            "hp": 100, "stage": "Basic" if language == "en" else "De base",
            "types": ["Fire" if language == "en" else "Feu"], "rarity": "Common",
            "attacks": [{"name": "Synthetic Strike" if language == "en" else "Frappe fictive", "damage": "10"}],
            "set": {"id": "syn", "name": "Synthetic Set", "cardCount": {"total": 2, "official": 2}}}


def extension(language="en"):
    return {"id": "syn", "name": "Synthetic Set", "cardCount": {"total": 2, "official": 2},
            "tcgOnline": "SYN", "releaseDate": "2026-01-01", "serie": {"id": "synthetic", "name": "Synthetic"},
            "cards": [{key: value for key, value in card(entity_id, language).items() if key in {"id", "localId", "name"}}
                      for entity_id in (["syn-1", "syn-2"] if language == "en" else ["syn-1"])]}


def evidence(key="synthetic"):
    return {"source_url": ENDPOINT, "operation": "query", "query_sha256": hashlib.sha256(key.encode()).hexdigest()}


def database(path):
    connection = connect_writable(path)
    initialize_schema(connection)
    store.initialize_batch_tables(connection)
    return connection


def populate(connection):
    for kind in ("sets", "cards"):
        for language in ("en", "fr"):
            rows = ([extension(language)] if kind == "sets" else
                    [card(value, language) for value in (["syn-1", "syn-2"] if language == "en" else ["syn-1"])])
            assert not store.store_page(connection, kind, language, 1, rows, evidence(kind + language), request_attempts=1)
            assert store.store_page(connection, kind, language, 2, [], evidence(kind + language + "end"), request_attempts=1)


def test_complete_pages_need_explicit_missing_language_confirmation(local_tmp):
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        populate(connection)
        assert store.pending_language_ids(connection, "cards", "fr") == ["syn-2"]
        assert not cards_coverage(path, _connection=connection)["complete"]
        store.store_selection(connection, "cards", "fr", {"syn-2": None}, evidence("absent"))
        coverage = cards_coverage(path, _connection=connection)
        assert coverage["complete"] and coverage["current_indexes_complete"]
        assert coverage["languages"]["fr"]["statuses"]["absent"] == 1
        assert coverage["languages"]["fr"]["index"]["snapshot"]["denominator"] == 1
        row = connection.execute("SELECT name,status,source_url FROM catalog_translations WHERE printing_id='syn-2' AND language='fr'").fetchone()
        assert tuple(row) == (None, "absent", ENDPOINT)


def test_sql_failure_rolls_back_whole_page_including_earlier_helper_commits(local_tmp, monkeypatch):
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        original = store._upsert_card_detail
        def fail(connection, payload, *args):
            if payload["id"] == "syn-2":
                raise RuntimeError("synthetic SQL failure")
            return original(connection, payload, *args)
        monkeypatch.setattr(store, "_upsert_card_detail", fail)
        with pytest.raises(RuntimeError):
            store.store_page(connection, "cards", "en", 1, [card(), card("syn-2")], evidence(), request_attempts=1)
        for table in ("catalog_printings", "catalog_sets", "catalog_translations", "catalog_batch_queries", "catalog_detail_payloads", "catalog_sync_state"):
            assert connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM catalog_fts").fetchone()[0] == 0


def test_duplicate_or_wrong_selection_cannot_create_false_coverage(local_tmp):
    with closing(database(local_tmp / "synthetic.sqlite3")) as connection:
        with pytest.raises(CatalogError, match="DUPLICATE"):
            store.store_page(connection, "cards", "en", 1, [card(), card()], evidence(), request_attempts=1)
        with pytest.raises(CatalogError, match="ID_MISMATCH"):
            store.store_selection(connection, "cards", "fr", {"syn-2": card()}, evidence())
        assert connection.execute("SELECT COUNT(*) FROM catalog_printings").fetchone()[0] == 0


def test_head_drift_invalidates_an_otherwise_completed_scan(local_tmp):
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        populate(connection)
        changed = card()
        changed["name"] = "Changed synthetic name"
        with pytest.raises(CatalogError, match="HEAD_CHANGED"):
            store.verify_head(connection, "cards", "en", [changed, card("syn-2")])
        snapshot = cards_coverage(path, _connection=connection)["languages"]["en"]["index"]["snapshot"]
        assert not snapshot["complete"] and snapshot["last_error"] == "BATCH_HEAD_CHANGED"


def test_language_payload_cannot_survive_a_changed_primary_hash(local_tmp):
    with closing(database(local_tmp / "synthetic.sqlite3")) as connection:
        populate(connection)
        digest = connection.execute("SELECT payload_sha256 FROM catalog_translations WHERE printing_id='syn-1' AND language='en'").fetchone()[0]
        assert store.verified_payload(connection, "cards", "syn-1", "en", digest)["types"] == ["Fire"]
        assert store.verified_payload(connection, "cards", "syn-1", "en", "0" * 64) is None
        with connection:
            connection.execute("UPDATE catalog_detail_payloads SET payload_json='{}' WHERE kind='cards' AND entity_id='syn-1' AND language='en'")
        assert store.verified_payload(connection, "cards", "syn-1", "en", digest) is None


def test_show_uses_the_requested_language_for_shared_labels_without_writes(local_tmp):
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        populate(connection)
    before = path.read_bytes()
    assert show_card(path, "syn-1", "en")["types"] == ["Fire"]
    assert show_card(path, "syn-1", "fr")["types"] == ["Feu"]
    assert path.read_bytes() == before


def test_status_does_not_label_a_completed_observation_as_permanently_partial(local_tmp):
    from pokemind.database import database_status
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        populate(connection)
        store.store_selection(connection, "cards", "fr", {"syn-2": None}, evidence("absent"))
    before = path.read_bytes()
    result = database_status(path)
    assert result["catalog_observed_complete"] is True
    assert "observé complet" in result["external_sources"]["TCGdex"]
    assert "non atomique" in result["external_sources"]["TCGdex"]
    assert path.read_bytes() == before


def test_show_preserves_language_specific_release_date_and_missing_rarity(local_tmp):
    path = local_tmp / "synthetic.sqlite3"
    with closing(database(path)) as connection:
        for language, date in (("en", "2026-01-01"), ("fr", "2026-02-01")):
            payload = extension(language)
            payload["releaseDate"] = date
            store.store_page(connection, "sets", language, 1, [payload], evidence("set" + language), request_attempts=1)
            payload = card(language=language)
            if language == "en":
                payload.pop("rarity")
            store.store_page(connection, "cards", language, 1, [payload], evidence("card" + language), request_attempts=1)
    en, fr = show_card(path, "syn-1", "en"), show_card(path, "syn-1", "fr")
    assert en["set"]["release_date"] == "2026-01-01" and fr["set"]["release_date"] == "2026-02-01"
    assert en["rarity"] is None and "rarity" in en["missing_fields"]
    assert fr["rarity"] == "Common" and "rarity" not in fr["missing_fields"]
