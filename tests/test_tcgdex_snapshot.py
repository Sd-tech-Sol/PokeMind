"""Synthetic literal snapshot integrity, translation boundaries and offline import."""
import hashlib
import json
import socket
from pathlib import Path

import pytest

from pokemind.cards import CatalogError, cards_coverage, show_card
from pokemind.database import connect_readonly, database_status
from pokemind.public_catalog_snapshot import import_snapshot
from pokemind.tcgdex_snapshot import Snapshot


COMMIT = "a" * 40


def sources():
    return {
        "LICENSE": "MIT License\nSynthetic test permission notice, not a real card corpus.",
        "meta/translations/fr.json": json.dumps({"types": {"Fire": "Feu"}, "category": {"Pokemon": "Pokémon"}}),
        "data/Test.ts": "const serie: Serie = {id:'test',name:{en:'Test',fr:'Essai'}}; export default serie",
        "data/Test/Synthetic.ts": "import serie from '../Test'; const set: Set = {id:'syn',name:{en:'Synthetic',fr:'Fictif'},serie:serie,cardCount:{official:3}}; export default set",
        "data/Test/Synthetic/1.ts": "import set from '../Synthetic'; const card: Card = {set:set,name:{en:'Synthetic Flame',fr:'Flamme fictive'},category:'Pokemon',hp:100,types:['Fire'],level:3,weight:'10 kg',attacks:[{name:{en:'Strike'},damage:10}]}; export default card",
        "data/Test/Synthetic/2.ts": "import set from '../Synthetic'; const card: Card = {set:set,name:{en:'Second'},category:'Trainer',effect:{en:'Synthetic effect'}}; export default card",
        "data/Test/Other/2.ts": "import set from '../Synthetic'; const card: Card = {set:set,name:{fr:'Deuxième'},category:'Trainer',effect:{fr:'Effet fictif'}}; export default card",
        "data/Test/Synthetic/3.ts": "import set from '../Synthetic'; const card: Card = {set:set,name:{de:'Nur Deutsch'},category:'Pokemon'}; export default card",
    }


def write_source(root, files=None):
    files = sources() if files is None else files
    path = root / "data/local/catalog-discovery-synthetic"
    path.mkdir(parents=True, exist_ok=True)
    entries, rows = [], []
    for name, text in files.items():
        body = text.encode("utf-8")
        sha = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
        entries.append({"path": name, "type": "blob", "mode": "100644", "sha": sha, "size": len(body)})
        rows.append({"path": name, "git_blob": sha, "text": text})
    tree = json.dumps({"truncated": False, "tree": entries}).encode()
    (path / "tree.json").write_bytes(tree)
    (path / "literal-source.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    (path / "PUBLIC_SOURCE_ONLY.json").write_text(json.dumps({"schema_version": 1,
        "kind": "tcgdex_pinned_public_dataset", "repository": "tcgdex/cards-database",
        "commit": COMMIT, "tree_sha256": hashlib.sha256(tree).hexdigest()}), encoding="utf-8")
    return path


def test_import_is_complete_offline_and_second_run_does_not_write(local_tmp, monkeypatch):
    source = write_source(local_tmp)
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden for offline snapshot")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    report = import_snapshot(local_tmp, source, "synthetic-snapshot", execute=True, create=True)
    assert report["status"] == "PINNED_CATALOG_COMPLETE"
    assert report["new_http_requests"] == 0 and report["source_card_objects"] == 4
    assert report["unique_printings"] == 3
    db = local_tmp / "data/local/public-campaigns/lot-i-synthetic-snapshot/public.sqlite3"
    before, mtime = db.read_bytes(), db.stat().st_mtime_ns
    coverage = cards_coverage(db)
    assert coverage["complete"] and coverage["requests_total"] == 0
    assert coverage["languages"]["fr"]["statuses"] == {"present": 2, "absent": 1, "not_fetched": 0, "network_error": 0}
    assert coverage["languages"]["fr"]["index"]["snapshot"]["provider_total_status"] == "pinned_source_tree_only"
    en, fr = show_card(db, "syn-1", "en"), show_card(db, "syn-1", "fr")
    assert en["types"] == ["Fire"] and fr["types"] == ["Feu"]
    assert fr["attacks"][0]["name"] is None  # no invented English fallback
    assert en["additional_descriptive_fields"]["level"] == 3
    assert en["provenance"]["transport"] == "pinned_git_literal_snapshot"
    assert show_card(db, "syn-2", "fr")["name"] == "Deuxième"
    assert "instantané Git" in database_status(db)["external_sources"]["TCGdex"]
    connection = connect_readonly(db)
    try:
        absent = connection.execute("SELECT name,status,source_url FROM catalog_translations WHERE printing_id='syn-3'").fetchall()
        assert len(absent) == 2 and all(row[0] is None and row[1] == "absent" for row in absent)
        assert all(COMMIT in row[2] for row in absent)
    finally:
        connection.close()
    again = import_snapshot(local_tmp, source, "synthetic-snapshot", execute=True)
    assert again["status"] == "CACHE_HIT_COMPLETE" and not again["database_modified"]
    assert db.read_bytes() == before and db.stat().st_mtime_ns == mtime


@pytest.mark.parametrize("fault", ["tree_hash", "blob", "missing", "duplicate", "origin", "truncated", "unsafe_path", "link_mode"])
def test_corrupt_or_unattested_source_rejected_before_database_creation(local_tmp, fault):
    files = sources()
    if fault == "unsafe_path":
        files["data/../escape.ts"] = files["data/Test.ts"]
    source = write_source(local_tmp, files)
    marker = json.loads((source / "PUBLIC_SOURCE_ONLY.json").read_text())
    if fault == "tree_hash":
        marker["tree_sha256"] = "0" * 64
    elif fault == "origin":
        marker["repository"] = "untrusted/other"
    elif fault in {"truncated", "link_mode"}:
        tree = json.loads((source / "tree.json").read_bytes())
        if fault == "truncated":
            tree["truncated"] = True
        else:
            tree["tree"][0]["mode"] = "120000"
        body = json.dumps(tree).encode()
        (source / "tree.json").write_bytes(body)
        marker["tree_sha256"] = hashlib.sha256(body).hexdigest()
    else:
        rows = (source / "literal-source.jsonl").read_text(encoding="utf-8").splitlines()
        if fault == "blob":
            row = json.loads(rows[-1]); row["text"] += " "; rows[-1] = json.dumps(row)
        elif fault == "missing":
            rows.pop()
        elif fault == "duplicate":
            rows.append(rows[-1])
        (source / "literal-source.jsonl").write_text("\n".join(rows), encoding="utf-8")
    (source / "PUBLIC_SOURCE_ONLY.json").write_text(json.dumps(marker), encoding="utf-8")
    with pytest.raises(CatalogError):
        import_snapshot(local_tmp, source, "rejected", execute=True, create=True)
    assert not (local_tmp / "data/local/public-campaigns/lot-i-rejected").exists()


def test_conflicting_locale_and_missing_import_rejected(local_tmp):
    files = sources()
    files["data/Test/Other/2.ts"] = files["data/Test/Other/2.ts"].replace("fr:'Deuxième'", "en:'Conflicting'")
    with pytest.raises(CatalogError, match="DUPLICATE_LOCALE"):
        Snapshot(local_tmp, write_source(local_tmp, files))
    files = sources()
    files["data/Test/Synthetic/1.ts"] = files["data/Test/Synthetic/1.ts"].replace("../Synthetic", "../Missing")
    with pytest.raises(CatalogError, match="REFERENCE"):
        Snapshot(local_tmp, write_source(local_tmp, files))


def test_missing_set_language_does_not_create_english_french_payload(local_tmp):
    files = sources()
    files["data/Test/Synthetic.ts"] = files["data/Test/Synthetic.ts"].replace(",fr:'Fictif'", "")
    snapshot = Snapshot(local_tmp, write_source(local_tmp, files))
    assert snapshot.available("cards", "syn-1", "en")
    assert not snapshot.available("cards", "syn-1", "fr")


def test_dry_run_does_not_read_or_create_source_or_workspace(local_tmp):
    report = import_snapshot(local_tmp, Path("missing"), "dry-run")
    assert report["status"] == "DRY_RUN" and not report["network_used"]
    assert not (local_tmp / "data").exists()
