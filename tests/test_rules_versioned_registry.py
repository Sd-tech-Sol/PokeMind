"""Reproduce the committed rules in fresh SQLite, never in the owner's catalog."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pokemind.rules import check_card, load_official_registry
from pokemind.cards import _canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = (
    "knowledge/curated/official_rules_2026.json",
    "knowledge/curated/official_rules_20261022.json",
)
TABLES = (
    ("official_rule_sources", "source_id"),
    ("official_rule_assertions", "assertion_id"),
    ("official_deck_structure_rules", "rule_id"),
)


def _rows(db):
    with closing(sqlite3.connect(db)) as connection:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY {key}").fetchall()
            for table, key in TABLES
        }


def test_committed_registry_import_and_verdicts_in_fresh_sqlite(
    local_tmp, monkeypatch, record_testsuite_property,
):
    db = local_tmp / "synthetic-rules.sqlite3"
    assert not db.exists()
    real_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        name = os.fsdecode(database)
        if name.startswith("file:"):
            uri = urlsplit(name)
            assert not uri.netloc
            name = unquote(uri.path)
            if os.name == "nt" and len(name) > 3 and name[0] == "/" and name[2] == ":":
                name = name[1:]
        assert Path(name).resolve() == db.resolve(), "Only this fresh fixture DB may open"
        return real_connect(database, *args, **kwargs)

    def denied(*args, **kwargs):
        raise AssertionError("Network and external processes are forbidden in registry reproduction")

    monkeypatch.setattr(sqlite3, "connect", guarded_connect)
    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(subprocess, "Popen", denied)
    registries = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in REGISTRIES]
    legacy, review = registries
    assert len(review["sources"]) == 4 and len(review["assertions"]) == 16
    assert not {a["assertion_id"] for a in legacy["assertions"]} & {
        a["assertion_id"] for a in review["assertions"]
    }
    for name in REGISTRIES:
        load_official_registry(db, ROOT / name)

    with closing(sqlite3.connect(db)) as connection:
        connection.row_factory = sqlite3.Row
        counts = {
            key: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for key, (table, _) in zip(("sources", "assertions", "structure_rules"), TABLES)
        }
        assert counts == {"sources": 15, "assertions": 22, "structure_rules": 1}
        for registry in registries:
            for assertion in registry["assertions"]:
                row = dict(connection.execute(
                    "SELECT * FROM official_rule_assertions WHERE assertion_id=?",
                    (assertion["assertion_id"],),
                ).fetchone())
                assert json.loads(row.pop("payload_json")) == assertion["payload"]
                assert row.pop("captured_at") == registry["consulted_at"]
                assert row == {key: assertion.get(key) for key in row}
        expected_sources = {
            source["source_id"]: source for registry in registries for source in registry["sources"]
        }
        for source_id, source in expected_sources.items():
            row = connection.execute(
                "SELECT * FROM official_rule_sources WHERE source_id=?", (source_id,),
            ).fetchone()
            for key in ("url", "title", "language", "validation_status", "effective_from", "effective_to"):
                assert row[key] == source.get(key)
        for registry in registries:
            for rule in registry.get("deck_structure_rules", []):
                row = dict(connection.execute(
                    "SELECT * FROM official_deck_structure_rules WHERE rule_id=?", (rule["rule_id"],),
                ).fetchone())
                assert json.loads(row.pop("payload_json")) == rule["payload"]
                assert row.pop("captured_at") == registry["consulted_at"]
                assert row == {key: rule.get(key) for key in row}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    normative_rows = _rows(db)
    load_official_registry(db, ROOT / REGISTRIES[1])
    assert _rows(db) == normative_rows  # metadata timestamp is deliberately excluded

    absent = check_card(db, "sm1-129", format="standard", platform="in_person", as_of="2026-10-22")
    assert absent["status"] == "unknown" and absent["reason_codes"] == ["PRINTING_NOT_FOUND_LOCAL"]

    # These are controlled inputs, NOT observations of real TCGdex printings.
    printings = (("sm1-129", None), ("swsh2-154", "D"), ("me01-125", "I"),
                 ("me01-114", "I"), ("sm5-114", None), ("sv07-086", "H"))
    with closing(sqlite3.connect(db)) as connection, connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            """INSERT INTO catalog_sets(tcgdex_id, name_en, discovered_at, updated_at)
               VALUES ('synthetic-set', 'Synthetic fixture, not a catalog observation', ?, ?)""",
            ("2026-10-22T00:00:00Z",) * 2,
        )
        connection.executemany(
            """INSERT INTO catalog_printings(tcgdex_id, set_id, regulation_mark,
               discovered_at, updated_at, brief_source_url, brief_retrieved_at)
               VALUES (?, 'synthetic-set', ?, '2026-10-22T00:00:00Z',
               '2026-10-22T00:00:00Z', 'https://example.invalid/synthetic-printings',
               '2026-10-22T00:00:00Z')""", printings,
        )
    cases = (
        ("sm1-129", "standard", "in_person", "2026-10-22", "legal", "FUNCTIONAL_REPRINT_VERIFIED"),
        ("swsh2-154", "standard", "in_person", "2026-10-22", "legal", "FUNCTIONAL_REPRINT_VERIFIED"),
        ("me01-125", "standard", "in_person", "2026-10-22", "legal", "MARK_ELIGIBLE"),
        ("me01-114", "standard", "in_person", "2026-10-22", "legal", "MARK_ELIGIBLE"),
        ("sm5-114", "expanded", "in_person", "2026-10-22", "not_legal", "EXPLICIT_OFFICIAL_RESTRICTION"),
        ("sv07-086", "standard", "in_person", "2026-10-22", "unknown", "OFFICIAL_RELEASE_DATE_NOT_VERIFIED"),
        ("me01-125", "standard", "live", "2026-10-22", "unknown", "RESTRICTIONS_NOT_FULLY_VERIFIED"),
        ("me01-125", "standard", "in_person", "2026-10-23", "unknown", "NO_UNIQUE_ACTIVE_ROTATION"),
    )
    before = (hashlib.sha256(db.read_bytes()).digest(), db.stat().st_mtime_ns)
    verdicts = []
    for card, fmt, platform, day, expected, reason in cases:
        result = check_card(db, card, format=fmt, platform=platform, as_of=day)
        assert result["status"] == expected and reason in result["reason_codes"]
        for field in ("ownership", "craftability", "live_printing_support"):
            assert result[field] == "unknown"
        verdicts.append({key: result[key] for key in ("tcgdex_id", "format", "platform", "as_of", "status", "reason_codes")})
    assert (hashlib.sha256(db.read_bytes()).digest(), db.stat().st_mtime_ns) == before

    record_testsuite_property("public_rules_reproduction", json.dumps({
        "scope": "VERSIONED_REGISTRIES_WITH_SYNTHETIC_PRINTINGS",
        "registry_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in REGISTRIES},
        "registry_canonical_sha256": {name: _canonical_sha256(json.loads((ROOT / name).read_bytes().decode("utf-8"))) for name in REGISTRIES},
        "review_sources": 4, "review_assertions": 16, "sqlite_totals": counts,
        "sql_assertions_match_registries": True,
        "normative_reload_rows_identical": True,
        "integrity": "ok", "foreign_key_errors": 0,
        "read_only_verdicts": True, "without_catalog": absent["status"],
        "synthetic_printings": len(printings), "verdicts": verdicts,
        "local_database_verified": False, "source_documents_revalidated": False,
        "competitive_data_acquired": False,
    }, sort_keys=True))


def test_historical_cross_os_hashes_are_exactly_lf_vs_crlf():
    historical = {
        "official_rules_2026.json": (
            "5ccd9a85a123438c51fc01085564b6b8af7f610c4359ec981b3aa0c5fa7f9c90",
            "37b367c87ecaf31d319acf776a613bf0e6a3492a3e9f0375220eb2bf69121e6e"),
        "official_rules_20261022.json": (
            "1c60e2ba9e7c94442016c49101be0dd02c477b1a4a9cf0c3d17265142158dfdd",
            "25378df16831837b45f0125aa3267e0b5c77d5e375f463b35095be5c02a81b11"),
    }
    for path in REGISTRIES:
        raw = (ROOT / path).read_bytes()
        lf = raw.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        assert (hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest()) == historical[Path(path).name]
        parsed = json.loads(lf.decode("utf-8"))
        assert _canonical_sha256(parsed) == _canonical_sha256(json.loads(crlf.decode("utf-8")))
        # Formatting/key order are irrelevant; a semantic change is not.
        reordered = json.dumps(parsed, ensure_ascii=True, sort_keys=False, indent=3)
        assert _canonical_sha256(parsed) == _canonical_sha256(json.loads(reordered))
        assert _canonical_sha256(parsed) != _canonical_sha256({**parsed, "consulted_at": "changed"})
