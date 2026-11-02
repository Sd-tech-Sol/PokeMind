"""PUBLIC-only supplements: no native mutation, false printing claim or stale text."""
from contextlib import closing
import json

import pytest

from pokemind.cards import CatalogError, _canonical_sha256, search_cards, show_card
from pokemind import catalog_batch_store as batch
from pokemind.database import connect_readonly, connect_writable, fts_checks
from pokemind.french_text_store import import_fields
from test_catalog_batch_store import card, database, populate, evidence


def public_cache(root):
    directory = root / "data/local/public-campaigns/lot-i-fr-synthetic"
    directory.mkdir(parents=True)
    (directory / "PUBLIC_ONLY.json").write_text(json.dumps({"kind": "pokemind_public_only_lot_i",
        "campaign": "fr-synthetic", "schema_version": 1}), encoding="utf-8")
    db = directory / "public.sqlite3"
    with closing(database(db)) as connection:
        populate(connection)
        batch.store_selection(connection, "cards", "fr", {"syn-2": None}, evidence("absence"))
    return db


def record(db, field="name", value="Deuxième fictif", entity="syn-2"):
    with closing(connect_readonly(db)) as connection:
        payloads = {r["language"]: json.loads(r["payload_json"]) or {} for r in connection.execute(
            "SELECT language,payload_json FROM catalog_detail_payloads WHERE kind='cards' AND entity_id=?", (entity,))}
    return {"printing_id": entity, "field": field, "value": value,
        "source_title": "Carte fictive (Série fictive 2)", "revid": 1234,
        "timestamp": "2026-01-01T00:00:00Z", "response_sha256": "a" * 64,
        "en_payload_sha256": _canonical_sha256(payloads["en"]), "fr_payload_sha256": _canonical_sha256(payloads["fr"]),
        "text_kind": "published_community_translation", "official_text_verified": False,
        "wiki_parameter": "nom-trad"}


def originals(db):
    with closing(connect_readonly(db)) as connection:
        return {table: [tuple(r) for r in connection.execute("SELECT * FROM " + table)] for table in
                ("catalog_translations", "catalog_printings", "catalog_detail_payloads", "catalog_sets", "catalog_sync_state")}


def test_french_show_and_search_use_attributed_fields_without_native_changes(local_tmp):
    db = public_cache(local_tmp)
    before = originals(db)
    rows = [record(db), record(db, "attacks.0.name", "Frappe de démonstration")]
    assert import_fields(local_tmp, db, rows)["status"] == "DRY_RUN"
    assert import_fields(local_tmp, db, rows, execute=True)["fields"] == 2
    assert originals(db) == before
    image = db.read_bytes()
    result = show_card(db, "syn-2", "fr")
    assert result["name"] == "Deuxième fictif" and result["status"] == "absent"
    assert result["attacks"][0]["name"] == "Frappe de démonstration"
    assert "effect" not in result["attacks"][0]  # no English fallback
    proof = result["french_text_supplements"]
    assert not proof["official_french_printing_proven"]
    assert proof["fields"][0]["license"] == "CC-BY-NC-SA-3.0-FR"
    found = search_cards(db, "Deuxième", language="fr")
    assert found[0]["tcgdex_id"] == "syn-2" and found[0]["text_source"] == "attributed_french_supplement"
    assert "french_text_supplements" not in show_card(db, "syn-2", "en")
    assert db.read_bytes() == image
    with closing(connect_readonly(db)) as connection:
        assert fts_checks(connection)["catalog_fts"]["status"] == "ok"


def test_second_identical_import_is_byte_and_mtime_idempotent(local_tmp):
    db = public_cache(local_tmp); row = record(db)
    import_fields(local_tmp, db, [row], execute=True)
    before, stamp = db.read_bytes(), db.stat().st_mtime_ns
    import_fields(local_tmp, db, [row], execute=True)
    assert db.read_bytes() == before and db.stat().st_mtime_ns == stamp


@pytest.mark.parametrize("fault", ["native", "hash", "field", "official", "duplicate", "revision"])
def test_invalid_field_cannot_create_tables_or_modify_database(local_tmp, fault):
    db = public_cache(local_tmp); row = record(db)
    if fault == "native": row = record(db, entity="syn-1")
    if fault == "hash": row["en_payload_sha256"] = "0" * 64
    if fault == "field": row["field"] = "attacks.99.effect"
    if fault == "official": row["official_text_verified"] = True
    if fault == "revision": row["revid"] = "https://untrusted.invalid"
    before = db.read_bytes()
    with pytest.raises(CatalogError):
        import_fields(local_tmp, db, [row, row] if fault == "duplicate" else [row], execute=True)
    assert db.read_bytes() == before


def test_changed_primary_payload_hides_the_old_supplement_from_show_and_search(local_tmp):
    db = public_cache(local_tmp)
    import_fields(local_tmp, db, [record(db)], execute=True)
    with closing(connect_writable(db)) as connection, connection:
        connection.execute("UPDATE catalog_translations SET payload_sha256=? WHERE printing_id='syn-2' AND language='en'", ("0" * 64,))
    assert "french_text_supplements" not in show_card(db, "syn-2", "fr")
    assert not search_cards(db, "Deuxième", language="fr")


def test_tampered_fts_cannot_return_unverified_snippets(local_tmp):
    db = public_cache(local_tmp)
    import_fields(local_tmp, db, [record(db)], execute=True)
    with closing(connect_writable(db)) as connection, connection:
        connection.execute("UPDATE catalog_french_text_fts SET body='UnverifiedSnippet'")
    assert not search_cards(db, "UnverifiedSnippet", language="fr")


def test_an_owner_or_unmarked_database_cannot_be_enriched(local_tmp):
    db = public_cache(local_tmp)
    (db.parent / "PUBLIC_ONLY.json").unlink()
    with pytest.raises(ValueError, match="UNATTESTED"):
        import_fields(local_tmp, db, [], execute=True)


def parallel_records(db, *, target_text="Synthetic English flavor.", target_dex=1):
    with closing(connect_writable(db)) as connection:
        batch.store_selection(connection, "cards", "en", {
            "syn-1": {**card(), "description": "Synthetic English flavor.", "dexId": [1]},
            "syn-2": {**card("syn-2"), "description": target_text, "dexId": [target_dex]},
        }, evidence("parallel"))
    source = record(db, "description", "Une description française fictive.", "syn-1")
    target = {**record(db, "description", source["value"]),
        "text_kind": "published_parallel_description", "related_printing_id": "syn-1",
        "related_en_payload_sha256": source["en_payload_sha256"],
        "related_fr_payload_sha256": source["fr_payload_sha256"],
        "match_basis": "identical_English_description_and_dexId"}
    return source, target


def test_related_description_is_attributed_and_hidden_if_related_original_changes(local_tmp):
    db = public_cache(local_tmp)
    source, target = parallel_records(db)
    before = originals(db)
    import_fields(local_tmp, db, [source, target], execute=True)
    shown = show_card(db, "syn-2", "fr")
    assert shown["description"] == source["value"]
    proof = shown["french_text_supplements"]["fields"][0]
    assert proof["text_kind"] == "published_parallel_description"
    assert proof["related_printing_id"] == "syn-1"
    assert proof["revision"] == source["revid"] and not proof["french_printing_proven"]
    assert originals(db) == before
    with closing(connect_writable(db)) as connection, connection:
        connection.execute("UPDATE catalog_translations SET payload_sha256=? WHERE printing_id='syn-1' AND language='en'", ("0" * 64,))
    assert "french_text_supplements" not in show_card(db, "syn-2", "fr")
    assert not search_cards(db, "description", language="fr")


@pytest.mark.parametrize("fault", ["text", "species", "effect", "hash", "empty"])
def test_parallel_description_requires_exact_paragraph_and_species(local_tmp, fault):
    db = public_cache(local_tmp)
    source, target = parallel_records(db,
        target_text="Different paragraph." if fault == "text" else (" " if fault == "empty" else "Synthetic English flavor."),
        target_dex=2 if fault == "species" else 1)
    if fault == "effect":
        target["field"] = "attacks.0.name"
    if fault == "hash":
        target["related_en_payload_sha256"] = "0" * 64
    before = db.read_bytes()
    with pytest.raises(CatalogError, match="PARALLEL_MATCH_REJECTED"):
        import_fields(local_tmp, db, [source, target], execute=True)
    assert db.read_bytes() == before
