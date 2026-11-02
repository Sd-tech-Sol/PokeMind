from __future__ import annotations

import io
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from pokemind.cards import (
    ApiNotFound,
    CatalogApiClient,
    CatalogError,
    NetworkFailure,
    RequestBudgetExhausted,
    _SafeRedirectHandler,
    card_reprints,
    cards_coverage,
    resolve_deck_cards,
    search_cards,
    show_card,
    sync_cards,
)
import pokemind.cards as cards_module
from pokemind.database import SCHEMA_VERSION, connect_writable, database_status, initialize_schema
from pokemind.decks import import_deck


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "cards" / "catalog_api.json").read_text(encoding="utf-8")
)


class FakeCatalogClient:
    def __init__(self, max_requests: int, routes: dict[str, object]) -> None:
        self.max_requests = max_requests
        self.requests_made = 0
        self.routes = routes
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def get_json(self, path: str, params: dict[str, object] | None = None):
        if self.remaining <= 0:
            raise AssertionError("Le code a dépassé le budget injecté.")
        self.requests_made += 1
        self.calls.append((path, params))
        value = self.routes.get(path)
        if value == "NOT_FOUND":
            raise ApiNotFound("absent synthétique")
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value(path, params)
        if value is None:
            raise AssertionError(f"Route synthétique absente: {path}")
        return value, f"https://api.tcgdex.net/v2{path}"


def _old_set(language: str) -> dict[str, object]:
    return {
        "id": "old1",
        "name": "Synthetic Archive" if language == "en" else "Archives synthétiques",
        "releaseDate": "1999-01-01",
        "serie": {"id": "synthetic-old"},
        "tcgOnline": "OLD",
        "cardCount": {"total": 1, "official": 1},
        "cards": [{"id": "old1-1", "localId": "1", "name": "Twin Name"}],
    }


def _routes() -> dict[str, object]:
    return {
        "/en/sets": FIXTURE["sets_en"],
        "/fr/sets": FIXTURE["sets_fr"],
        "/en/cards": FIXTURE["cards_en"],
        "/fr/cards": FIXTURE["cards_fr"],
        "/en/sets/old1": _old_set("en"),
        "/fr/sets/old1": _old_set("fr"),
        "/en/sets/syn1": FIXTURE["set_syn1_en"],
        "/fr/sets/syn1": FIXTURE["set_syn1_fr"],
        "/en/cards/old1-1": FIXTURE["old_en"],
        "/fr/cards/old1-1": "NOT_FOUND",
        "/en/cards/syn1-1": FIXTURE["pokemon_en"],
        "/fr/cards/syn1-1": FIXTURE["pokemon_fr"],
        "/en/cards/syn1-2": FIXTURE["trainer_en"],
        "/fr/cards/syn1-2": "NOT_FOUND",
        "/en/cards/syn1-3": FIXTURE["energy_en"],
        "/fr/cards/syn1-3": "NOT_FOUND",
    }


def _make_v3_database(path: Path) -> None:
    connection = connect_writable(path)
    initialize_schema(connection)
    with connection:
        connection.executescript(
            """
            DROP TRIGGER IF EXISTS catalog_translations_ai;
            DROP TRIGGER IF EXISTS catalog_translations_ad;
            DROP TRIGGER IF EXISTS catalog_translations_au;
            DROP TABLE IF EXISTS catalog_fts;
            DROP TABLE IF EXISTS catalog_refresh_state;
            DROP TABLE IF EXISTS catalog_sync_state;
            DROP TABLE IF EXISTS catalog_translations;
            DROP TABLE IF EXISTS catalog_printings;
            DROP TABLE IF EXISTS catalog_sets;
            DELETE FROM metadata WHERE key LIKE 'catalog_%';
            PRAGMA user_version = 3;
            INSERT INTO observed_decks(deck_id, status, created_at, last_seen_at)
            VALUES ('principal', 'observé partiellement', '2026-01-01Z', '2026-01-01Z');
            """
        )
        for index in range(5):
            connection.execute(
                """INSERT INTO battle_logs
                   (source_sha256, imported_at, parser_version, source_kind, outcome,
                    valid, deck_id, recognized_events, warnings_json)
                   VALUES (?, '2026-01-01Z', 'synthetic', 'file', 'W', 1,
                           'principal', 1, '[]')""",
                (f"synthetic-{index}",),
            )
        cursor = connection.execute(
            """INSERT INTO deck_versions
               (deck_id, version_number, imported_at, approved_at, effective_from,
                parser_version, source_kind, export_sha256, list_sha256,
                total_cards, entry_count, exact_confirmed, sections_json,
                coverage_json, raw_stored)
               VALUES ('principal', 1, '2026-01-01Z', '2026-01-01Z', '2026-01-01Z',
                       'synthetic', 'stdin', 'a', 'b', 60, 1, 1, '{}', '{}', 0)"""
        )
        connection.execute(
            """INSERT INTO deck_version_cards
               (deck_version_id, ordinal, source_line, card_type, quantity,
                card_name, set_code, collector_number, normalized_line)
               VALUES (?, 1, 1, 'energy', 60, 'Synthetic Energy', 'SYN', '1',
                       '60 Synthetic Energy SYN 1')""",
            (cursor.lastrowid,),
        )
    connection.close()


def test_dry_run_uses_no_network_and_writes_nothing(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"
    result = sync_cards(db_path, dry_run=True, languages="fr", max_requests=3)
    assert result["network_used"] is False
    assert result["writes"] == 0
    assert result["would_migrate"] is True
    assert not db_path.exists()


def test_schema_three_migration_backs_up_and_preserves_private_counts(local_tmp: Path) -> None:
    db_path = local_tmp / "migration.sqlite3"
    _make_v3_database(db_path)
    connection = connect_writable(db_path)
    initialize_schema(connection)
    backup = Path(connection.execute(
        "SELECT value FROM metadata WHERE key='last_schema_backup'"
    ).fetchone()[0])
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 5
    assert connection.execute("SELECT SUM(quantity) FROM deck_version_cards").fetchone()[0] == 60
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()
    assert backup.is_file()
    backup_connection = sqlite3.connect(backup)
    assert backup_connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert backup_connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 5
    backup_connection.close()


def test_migration_failure_rolls_back_catalog_ddl(local_tmp: Path) -> None:
    db_path = local_tmp / "rollback.sqlite3"
    _make_v3_database(db_path)
    connection = connect_writable(db_path)

    def deny_translation_table(
        action: int, arg1: str | None, arg2: str | None, database: str | None, source: str | None
    ) -> int:
        if action == sqlite3.SQLITE_CREATE_TABLE and arg1 == "catalog_translations":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(deny_translation_table)
    with pytest.raises(sqlite3.DatabaseError):
        initialize_schema(connection)
    connection.set_authorizer(None)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'catalog_%'"
    ).fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 5
    connection.close()


def test_bounded_sync_resume_idempotence_search_and_coverage(local_tmp: Path) -> None:
    db_path = local_tmp / "catalog.sqlite3"
    first = sync_cards(
        db_path, languages="en,fr", max_requests=8,
        client=FakeCatalogClient(8, _routes()),
    )
    assert first["requests_made"] == 8
    assert first["coverage"]["unique_printings"] == 4
    assert first["coverage"]["languages"]["fr"]["statuses"]["absent"] == 1

    second = sync_cards(
        db_path, languages="en,fr", max_requests=8, phase="details",
        client=FakeCatalogClient(8, _routes()),
    )
    assert second["details"] == {
        "sets_present": 2,
        "sets_absent": 0,
        "cards_present": 4,
        "cards_absent": 2,
    }
    assert show_card(db_path, "syn1-1", "fr")["attacks"][0]["name"] == "Frappe mesurée"
    trainer = show_card(db_path, "syn1-2", "en")
    assert trainer["trainer_type"] == "Supporter"
    assert "DROP TABLE" in trainer["effect"]
    assert show_card(db_path, "syn1-3", "en")["energy_type"] == "Special"
    assert show_card(db_path, "old1-1", "fr")["status"] == "absent"
    twins = search_cards(db_path, "Twin Name", language="en")
    assert {row["tcgdex_id"] for row in twins} == {"syn1-1", "old1-1"}
    assert cards_coverage(db_path)["complete"] is False
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM catalog_fts").fetchone()[0] == 8
    assert connection.execute("SELECT COUNT(*) FROM catalog_translations").fetchone()[0] == 8
    connection.close()

    before = database_status(db_path)
    third_client = FakeCatalogClient(4, _routes())
    third = sync_cards(
        db_path, languages="en,fr", max_requests=4, phase="details", client=third_client
    )
    after = database_status(db_path)
    assert third["requests_made"] == 0
    assert third["stopped_reason"] == "nothing_pending"
    assert before["catalog_printings"] == after["catalog_printings"] == 4
    assert before["catalog_translations"] == after["catalog_translations"] == 8


def test_pagination_empty_page_and_resume_without_duplicates(local_tmp: Path) -> None:
    db_path = local_tmp / "pagination.sqlite3"
    page = [
        {"id": f"set{index:03d}", "name": f"Set {index}", "cardCount": {"total": 1, "official": 1}}
        for index in range(100)
    ]
    first_client = FakeCatalogClient(1, {"/en/sets": page})
    first = sync_cards(db_path, languages="en", max_requests=1, client=first_client)
    assert first_client.calls[0][1] == {
        "pagination:page": 1,
        "pagination:itemsPerPage": 100,
    }
    assert first["coverage"]["sets_discovered"] == 100
    assert first["pages"][0]["completed"] is False

    second_client = FakeCatalogClient(1, {"/en/sets": []})
    second = sync_cards(db_path, languages="en", max_requests=1, client=second_client)
    assert second_client.calls[0][1]["pagination:page"] == 2
    assert second["pages"][0]["items"] == 0
    assert second["coverage"]["sets_discovered"] == 100


def test_malformed_page_rolls_back_and_network_error_is_visible(local_tmp: Path) -> None:
    malformed_db = local_tmp / "malformed.sqlite3"
    malformed = [
        {"id": "safe", "name": "Safe", "cardCount": {"total": 1, "official": 1}},
        {"id": "bad", "cardCount": []},
    ]
    result = sync_cards(
        malformed_db,
        languages="en",
        max_requests=1,
        client=FakeCatalogClient(1, {"/en/sets": malformed}),
    )
    assert result["error"]
    assert cards_coverage(malformed_db)["sets_discovered"] == 0

    network_db = local_tmp / "network.sqlite3"
    discovery = {
        "/en/sets": [],
        "/en/cards": [{"id": "ghost-9", "localId": "9", "name": "Unknown Set Unit"}],
    }
    sync_cards(
        network_db,
        languages="en",
        max_requests=2,
        client=FakeCatalogClient(2, discovery),
    )
    routes = {"/en/cards/ghost-9": NetworkFailure("timeout synthétique")}
    failed = sync_cards(
        network_db,
        languages="en",
        max_requests=1,
        phase="details",
        client=FakeCatalogClient(1, routes),
    )
    assert failed["stopped_reason"] == "source_error"
    assert failed["coverage"]["last_failure_at"] is not None
    assert failed["coverage"]["unique_printings"] == 1
    assert failed["coverage"]["languages"]["en"]["statuses"]["network_error"] == 1


class FakeResponse:
    def __init__(self, payload: object, url: str = "https://api.tcgdex.net/v2/en/cards") -> None:
        self.raw = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json", "Content-Length": str(len(self.raw))}
        self.url = url

    def geturl(self) -> str:
        return self.url

    def read(self, amount: int) -> bytes:
        return self.raw[:amount]

    def close(self) -> None:
        return None


class SequenceOpener:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)

    def open(self, request: object, timeout: float):
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def test_http_client_retries_429_counts_attempts_and_handles_timeout() -> None:
    url = "https://api.tcgdex.net/v2/en/cards"
    too_many = HTTPError(url, 429, "too many", {"Retry-After": "0"}, io.BytesIO(b"{}"))
    opener = SequenceOpener([too_many, FakeResponse([])])
    client = CatalogApiClient(2, opener=opener, interval=0, sleep=lambda _: None)
    payload, _ = client.get_json("/en/cards")
    assert payload == []
    assert client.requests_made == 2

    offline = CatalogApiClient(
        3,
        opener=SequenceOpener([URLError("timeout")] * 3),
        interval=0,
        sleep=lambda _: None,
    )
    with pytest.raises(NetworkFailure):
        offline.get_json("/en/cards")
    assert offline.requests_made == 3


def test_tcgdex_redirects_share_allowlist_and_each_get_is_debited() -> None:
    source = Request("https://api.tcgdex.net/v2/en/cards")
    safe_target = "https://api.tcgdex.net/v2/fr/cards/synthetic-1"

    exhausted = CatalogApiClient(1, opener=SequenceOpener([]), interval=0)
    exhausted.requests_made = 1
    with pytest.raises(RequestBudgetExhausted, match="Budget de requêtes"):
        _SafeRedirectHandler(exhausted._reserve_get).redirect_request(
            source, None, 302, "Found", {}, safe_target
        )
    assert exhausted.requests_made == 1

    counted = CatalogApiClient(2, opener=SequenceOpener([]), interval=0)
    counted.requests_made = 1
    redirected = _SafeRedirectHandler(counted._reserve_get).redirect_request(
        source, None, 302, "Found", {}, safe_target
    )
    assert redirected is not None and redirected.full_url == safe_target
    assert counted.requests_made == 2

    for blocked in (
        "https://example.invalid/v2/en/cards",
        "http://api.tcgdex.net/v2/en/cards",
        "https://api.tcgdex.net/v2/en/cards/safe/extra",
        "https://api.tcgdex.net/private",
        "https://user:secret@api.tcgdex.net/v2/en/cards",
        "https://api.tcgdex.net/v2/en/cards/safe?unexpected=1",
    ):
        with pytest.raises(NetworkFailure, match="Redirection TCGdex refusée"):
            _SafeRedirectHandler().redirect_request(source, None, 302, "Found", {}, blocked)


def test_tcgdex_final_url_is_validated_before_payload_read() -> None:
    response = FakeResponse([])
    response.url = "https://api.tcgdex.net/v2/en/cards/safe/extra"
    client = CatalogApiClient(1, opener=SequenceOpener([response]), interval=0)
    with pytest.raises(NetworkFailure, match="URL finale TCGdex refusée"):
        client.get_json("/en/cards")
    assert client.requests_made == 1


def test_tcgdex_redirect_budget_exhaustion_stops_before_following_get() -> None:
    client = CatalogApiClient(1, opener=SequenceOpener([]), interval=0)

    class RedirectingOpener:
        calls = 0

        def open(self, request: object, timeout: float):
            self.calls += 1
            return _SafeRedirectHandler(client._reserve_get).redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://api.tcgdex.net/v2/en/cards",
            )

    opener = RedirectingOpener()
    client._opener = opener
    with pytest.raises(RequestBudgetExhausted):
        client.get_json("/en/cards")
    assert client.requests_made == 1 and opener.calls == 1


def test_tcgdex_provider_question_mark_identifier_is_encoded_as_one_path_segment() -> None:
    url = cards_module._safe_api_url("/en/cards/exu-%3F")
    assert url == "https://api.tcgdex.net/v2/en/cards/exu-%3F"
    with pytest.raises(cards_module.CatalogError):
        cards_module._safe_api_url("/en/cards/exu-?/unexpected")


def test_unknown_set_is_inserted_as_stub_and_distinct_identity_is_kept(local_tmp: Path) -> None:
    db_path = local_tmp / "unknown-set.sqlite3"
    routes = {
        "/en/sets": [],
        "/en/cards": [{"id": "ghost-9", "localId": "9", "name": "Unknown Set Unit"}],
        "/en/cards/ghost-9": FIXTURE["unknown_set_card"],
    }
    first = sync_cards(db_path, languages="en", max_requests=2, client=FakeCatalogClient(2, routes))
    assert first["coverage"]["unique_printings"] == 1
    second = sync_cards(
        db_path, languages="en", max_requests=1, phase="details",
        client=FakeCatalogClient(1, routes),
    )
    shown = show_card(db_path, "ghost-9", "en")
    assert second["details"]["cards_present"] == 1
    assert shown["set"]["id"] == "ghost"
    assert shown["status"] == "present"


def test_read_only_deck_resolver_requires_tcg_online_number_and_name(local_tmp: Path) -> None:
    db_path = local_tmp / "resolver.sqlite3"
    deck_text = (ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt").read_text(encoding="utf-8")
    import_deck(db_path, deck_text, deck_id="principal", source_kind="stdin")
    connection = connect_writable(db_path)
    now = "2026-01-01T00:00:00Z"
    with connection:
        connection.execute(
            """INSERT INTO catalog_sets
               (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at)
               VALUES ('resolver', 'Resolver Set', 'SYN', ?, ?)""",
            (now, now),
        )
        for tcgdex_id, local_id, name in (
            ("resolver-1", "001", "Creature Alpha"),
            ("resolver-2", "002", "Creature Beta"),
        ):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id, set_id, local_id, discovered_at, updated_at,
                    brief_source_url, brief_retrieved_at)
                   VALUES (?, 'resolver', ?, ?, ?, 'https://api.tcgdex.net/v2/en/cards', ?)""",
                (tcgdex_id, local_id, now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id, language, status, name, source_url, retrieved_at)
                   VALUES (?, 'en', 'present', ?, 'https://api.tcgdex.net/v2/en/cards', ?)""",
                (tcgdex_id, name, now),
            )
    before = connection.total_changes
    connection.close()
    result = resolve_deck_cards(db_path, "principal")
    assert result["read_only"] is True
    assert result["counts"]["resolved"] == 2
    assert result["counts"]["unresolved"] > 0
    check = sqlite3.connect(db_path)
    assert check.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0] == 1
    assert check.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 0
    check.close()


def test_cards_cli_dry_run_and_offline_queries(local_tmp: Path) -> None:
    db_path = local_tmp / "cli.sqlite3"
    command = [
        sys.executable, "-m", "pokemind", "cards", "sync", "--dry-run",
        "--db", str(db_path), "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["network_used"] is False
    assert not db_path.exists()


def _page_route(items: list[dict[str, object]]):
    def route(path: str, params: dict[str, object] | None):
        assert params is not None
        return items if params["pagination:page"] == 1 else []

    return route


def test_manual_refresh_detects_new_french_name_preserves_details_and_resumes(
    local_tmp: Path,
) -> None:
    db_path = local_tmp / "refresh.sqlite3"
    initial_set = {"id": "syn1", "name": "Aube", "cardCount": {"total": 1, "official": 1}}
    initial_card = {"id": "syn1-1", "localId": "1", "name": "Nom initial"}
    initial_routes = {
        "/fr/sets": _page_route([initial_set]),
        "/fr/cards": _page_route([initial_card]),
    }
    discovered = sync_cards(
        db_path,
        languages="fr",
        phase="index",
        max_requests=4,
        client=FakeCatalogClient(4, initial_routes),
    )
    assert discovered["coverage"]["discovery"]["complete"] is False
    assert all(scope["completed"] for scope in discovered["coverage"]["discovery"]["scopes"])

    set_detail = {
        "id": "syn1",
        "name": "Aube",
        "cardCount": {"total": 1, "official": 1},
    }
    card_detail = dict(FIXTURE["pokemon_fr"])
    card_detail["name"] = "Nom initial"
    detailed = sync_cards(
        db_path,
        languages="fr",
        phase="details",
        max_requests=2,
        client=FakeCatalogClient(
            2,
            {"/fr/sets/syn1": set_detail, "/fr/cards/syn1-1": card_detail},
        ),
    )
    assert detailed["details"]["cards_present"] == 1

    refreshed_set = {"id": "syn1", "name": "Aube revue", "cardCount": {"total": 2, "official": 2}}
    refreshed_cards = [
        {"id": "syn1-1", "localId": "1", "name": "Nouveau nom français"},
        {"id": "syn1-2", "localId": "2", "name": "Nouvelle carte"},
    ]
    refresh_routes = {
        "/fr/sets": _page_route([refreshed_set]),
        "/fr/cards": _page_route(refreshed_cards),
    }
    partial = sync_cards(
        db_path,
        languages="fr",
        phase="index",
        refresh_index=True,
        max_requests=2,
        client=FakeCatalogClient(2, refresh_routes),
    )
    assert partial["coverage"]["refresh"]["in_progress"] is True
    assert partial["coverage"]["unique_printings"] == 2
    preserved = show_card(db_path, "syn1-1", "fr")
    assert preserved["name"] == "Nouveau nom français"
    assert preserved["attacks"][0]["name"] == "Frappe mesurée"
    assert preserved["possibly_stale"] is True
    assert partial["coverage"]["languages"]["fr"]["statuses"] == {
        "present": 1,
        "absent": 0,
        "not_fetched": 1,
        "network_error": 0,
    }

    resumed = sync_cards(
        db_path,
        languages="fr",
        phase="index",
        refresh_index=True,
        max_requests=4,
        client=FakeCatalogClient(4, refresh_routes),
    )
    fr_refresh = {
        row["scope"]: row for row in resumed["coverage"]["refresh"]["scopes"]
    }
    assert fr_refresh["sets:fr"]["in_progress"] == 0
    assert fr_refresh["cards:fr"]["in_progress"] == 0
    assert fr_refresh["cards:fr"]["last_completed_at"] is not None

    idempotent = sync_cards(
        db_path,
        languages="fr",
        phase="index",
        refresh_index=True,
        max_requests=6,
        client=FakeCatalogClient(6, refresh_routes),
    )
    final_scopes = {
        row["scope"]: row for row in idempotent["coverage"]["refresh"]["scopes"]
    }
    assert final_scopes["cards:fr"]["new_items_current"] == 0
    assert final_scopes["cards:fr"]["changed_items_current"] == 0


def test_refresh_head_probe_catches_insertion_that_shifted_pages(local_tmp: Path) -> None:
    db_path = local_tmp / "shift.sqlite3"
    original = [
        {"id": f"set-{index:03d}", "name": f"Set {index}", "cardCount": {"total": 1, "official": 1}}
        for index in range(100)
    ]

    def initial_sets(path: str, params: dict[str, object] | None):
        assert params is not None
        return original if params["pagination:page"] == 1 else []

    empty = _page_route([])
    sync_cards(
        db_path,
        languages="en",
        phase="index",
        max_requests=5,
        client=FakeCatalogClient(5, {"/en/sets": initial_sets, "/en/cards": empty}),
    )
    first_refresh = FakeCatalogClient(
        1, {"/en/sets": initial_sets, "/en/cards": empty}
    )
    sync_cards(
        db_path,
        languages="en",
        phase="index",
        refresh_index=True,
        max_requests=1,
        client=first_refresh,
    )

    shifted_page = [
        {"id": "set-000a", "name": "Inserted", "cardCount": {"total": 1, "official": 1}},
        *original[:99],
    ]

    def shifted_sets(path: str, params: dict[str, object] | None):
        assert params is not None
        return shifted_page if params["pagination:page"] == 1 else [original[-1]]

    resumed = sync_cards(
        db_path,
        languages="en",
        phase="index",
        refresh_index=True,
        max_requests=2,
        client=FakeCatalogClient(2, {"/en/sets": shifted_sets, "/en/cards": empty}),
    )
    assert resumed["coverage"]["sets_discovered"] == 101
    assert any(page["probe"] for page in resumed["pages"] if page["scope"] == "sets:en")


def test_recheck_absent_is_explicit_and_does_not_loop(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"
    routes = {
        "/en/sets": _page_route([]),
        "/en/cards": _page_route([{"id": "gone-1", "localId": "1", "name": "Gone"}]),
    }
    sync_cards(
        db_path,
        languages="en",
        phase="index",
        max_requests=4,
        client=FakeCatalogClient(4, routes),
    )
    first = sync_cards(
        db_path,
        languages="en",
        phase="details",
        max_requests=1,
        client=FakeCatalogClient(1, {"/en/cards/gone-1": "NOT_FOUND"}),
    )
    assert first["coverage"]["languages"]["en"]["statuses"]["absent"] == 1
    no_retry = sync_cards(
        db_path,
        languages="en",
        phase="details",
        max_requests=1,
        client=FakeCatalogClient(1, {}),
    )
    assert no_retry["requests_made"] == 0
    retried = sync_cards(
        db_path,
        languages="en",
        phase="details",
        recheck_absent=True,
        max_requests=3,
        client=FakeCatalogClient(3, {"/en/cards/gone-1": "NOT_FOUND"}),
    )
    assert retried["requests_made"] == 1
    assert retried["details"]["cards_absent"] == 1


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize("kind", ["sets", "cards"])
def test_refresh_preserves_verified_absence_until_explicit_recheck(
    local_tmp: Path, language: str, kind: str
) -> None:
    db_path = local_tmp / f"absent-refresh-{kind}-{language}.sqlite3"
    set_id = f"missing-set-{language}"
    card_id = f"{set_id}-1"

    def index_routes(name: str) -> dict[str, object]:
        set_items = (
            [{"id": set_id, "name": name, "cardCount": {"total": 1, "official": 1}}]
            if kind == "sets" else []
        )
        card_items = (
            [{"id": card_id, "localId": "1", "name": name}]
            if kind == "cards" else []
        )
        return {
            f"/{language}/sets": _page_route(set_items),
            f"/{language}/cards": _page_route(card_items),
        }

    detail_path = (
        f"/{language}/sets/{set_id}" if kind == "sets"
        else f"/{language}/cards/{card_id}"
    )
    sync_cards(
        db_path,
        languages=language,
        phase="index",
        max_requests=4,
        client=FakeCatalogClient(4, index_routes("Initial brief")),
    )
    missing = sync_cards(
        db_path,
        languages=language,
        phase="details",
        max_requests=1,
        client=FakeCatalogClient(1, {detail_path: "NOT_FOUND"}),
    )
    status_key = "sets_absent" if kind == "sets" else "cards_absent"
    assert missing["details"][status_key] == 1

    for brief_name in ("Initial brief", "Changed brief"):
        sync_cards(
            db_path,
            languages=language,
            phase="index",
            refresh_index=True,
            max_requests=4,
            client=FakeCatalogClient(4, index_routes(brief_name)),
        )
        coverage = cards_coverage(db_path)["languages"][language]
        statuses = coverage["sets"]["statuses"] if kind == "sets" else coverage["statuses"]
        assert statuses["absent"] == 1
        skipped = sync_cards(
            db_path,
            languages=language,
            phase="details",
            max_requests=1,
            client=FakeCatalogClient(1, {}),
        )
        assert skipped["requests_made"] == 0

    still_missing = sync_cards(
        db_path,
        languages=language,
        phase="details",
        recheck_absent=True,
        max_requests=1,
        client=FakeCatalogClient(1, {detail_path: "NOT_FOUND"}),
    )
    assert still_missing["requests_made"] == 1
    assert still_missing["details"][status_key] == 1

    if kind == "sets":
        restored_detail = {
            "id": set_id,
            "name": "Restored detail",
            "cardCount": {"total": 1, "official": 1},
        }
    else:
        restored_detail = dict(FIXTURE[f"pokemon_{language}"])
        restored_detail.update({
            "id": card_id,
            "localId": "1",
            "name": "Restored detail",
            "set": {
                "id": set_id,
                "name": "Synthetic set",
                "cardCount": {"total": 1, "official": 1},
            },
        })
    restored = sync_cards(
        db_path,
        languages=language,
        phase="details",
        recheck_absent=True,
        max_requests=1,
        client=FakeCatalogClient(1, {detail_path: restored_detail}),
    )
    present_key = "sets_present" if kind == "sets" else "cards_present"
    assert restored["details"][present_key] == 1
    restored_coverage = cards_coverage(db_path)["languages"][language]
    restored_statuses = (
        restored_coverage["sets"]["statuses"]
        if kind == "sets" else restored_coverage["statuses"]
    )
    assert restored_statuses["absent"] == 0
    assert restored_statuses["present"] == 1
    stale_count = (
        restored_coverage["sets"]["possibly_stale_details"]
        if kind == "sets" else restored_coverage["possibly_stale_details"]
    )
    assert stale_count == 0
    connection = sqlite3.connect(db_path)
    if kind == "sets":
        error_column = "last_error_en" if language == "en" else "last_error_fr"
        last_error = connection.execute(
            f"SELECT {error_column} FROM catalog_sets WHERE tcgdex_id=?", (set_id,)
        ).fetchone()[0]
    else:
        last_error = connection.execute(
            "SELECT last_error FROM catalog_translations WHERE printing_id=? AND language=?",
            (card_id, language),
        ).fetchone()[0]
    connection.close()
    assert last_error is None

    sync_cards(
        db_path,
        languages=language,
        phase="index",
        refresh_index=True,
        max_requests=4,
        client=FakeCatalogClient(4, index_routes("Changed again")),
    )
    refresh_detail_routes = {detail_path: restored_detail}
    expected_requests = 1
    if kind == "cards":
        refresh_detail_routes[f"/{language}/sets/{set_id}"] = {
            "id": set_id,
            "name": "Synthetic set",
            "cardCount": {"total": 1, "official": 1},
        }
        expected_requests = 2
    refreshed = sync_cards(
        db_path,
        languages=language,
        phase="details",
        max_requests=expected_requests,
        client=FakeCatalogClient(expected_requests, refresh_detail_routes),
    )
    assert refreshed["requests_made"] == expected_requests
    assert refreshed["details"][present_key] == 1
    final_coverage = cards_coverage(db_path)["languages"][language]
    assert (
        final_coverage["sets"]["possibly_stale_details"]
        if kind == "sets" else final_coverage["possibly_stale_details"]
    ) == 0


def test_schema_four_migration_is_additive_and_backup_can_be_restored(local_tmp: Path) -> None:
    db_path = local_tmp / "schema4.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE catalog_sets (
            tcgdex_id TEXT PRIMARY KEY, name_en TEXT, name_fr TEXT, series_id TEXT,
            release_date TEXT, card_count_total INTEGER, card_count_official INTEGER,
            tcg_online_code TEXT, abbreviation_official TEXT, abbreviation_localized TEXT,
            discovered_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            source_url_en TEXT, source_url_fr TEXT, retrieved_at_en TEXT, retrieved_at_fr TEXT,
            detail_status_en TEXT NOT NULL DEFAULT 'not_fetched',
            detail_status_fr TEXT NOT NULL DEFAULT 'not_fetched',
            content_sha256_en TEXT, content_sha256_fr TEXT,
            last_error_en TEXT, last_error_fr TEXT
        );
        CREATE TABLE catalog_printings (
            tcgdex_id TEXT PRIMARY KEY, set_id TEXT, local_id TEXT, category TEXT, hp INTEGER,
            stage TEXT, regulation_mark TEXT, rarity TEXT, illustrator TEXT,
            types_json TEXT, variants_json TEXT, discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, brief_source_url TEXT NOT NULL,
            brief_retrieved_at TEXT NOT NULL
        );
        CREATE TABLE catalog_translations (
            id INTEGER PRIMARY KEY, printing_id TEXT NOT NULL, language TEXT NOT NULL,
            status TEXT NOT NULL, name TEXT, category TEXT, description TEXT, effect TEXT,
            trainer_type TEXT, energy_type TEXT, abilities_json TEXT, attacks_json TEXT,
            weaknesses_json TEXT, resistances_json TEXT, retreat INTEGER,
            source_url TEXT NOT NULL, retrieved_at TEXT, payload_sha256 TEXT,
            last_error TEXT, UNIQUE(printing_id, language)
        );
        CREATE TABLE catalog_sync_state (
            scope TEXT PRIMARY KEY, next_page INTEGER NOT NULL DEFAULT 1,
            completed INTEGER NOT NULL DEFAULT 0, requests_total INTEGER NOT NULL DEFAULT 0,
            last_success_at TEXT, last_failure_at TEXT, last_error TEXT, updated_at TEXT NOT NULL
        );
        INSERT INTO catalog_sets
            (tcgdex_id, name_en, discovered_at, updated_at)
            VALUES ('kept', 'Kept', '2026-01-01Z', '2026-01-01Z');
        PRAGMA user_version = 4;
        """
    )
    connection.commit()
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    backup_path = Path(connection.execute(
        "SELECT value FROM metadata WHERE key='last_schema_backup'"
    ).fetchone()[0])
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT name_en FROM catalog_sets WHERE tcgdex_id='kept'").fetchone()[0] == "Kept"
    assert {row[1] for row in connection.execute("PRAGMA table_info(catalog_sets)")} >= {
        "brief_sha256_en", "detail_stale_en"
    }
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='catalog_refresh_state'"
    ).fetchone()[0] == 1
    connection.close()

    restored_path = local_tmp / "restored.sqlite3"
    backup_connection = sqlite3.connect(backup_path)
    restored_connection = sqlite3.connect(restored_path)
    backup_connection.backup(restored_connection)
    assert restored_connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert restored_connection.execute("PRAGMA user_version").fetchone()[0] == 4
    assert restored_connection.execute(
        "SELECT name_en FROM catalog_sets WHERE tcgdex_id='kept'"
    ).fetchone()[0] == "Kept"
    backup_connection.close()
    restored_connection.close()


def test_local_deck_priority_sends_only_public_tcgdex_identity(local_tmp: Path) -> None:
    db_path = local_tmp / "priority.sqlite3"
    deck_text = (ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt").read_text(encoding="utf-8")
    import_deck(db_path, deck_text, deck_id="principal", source_kind="stdin")
    connection = connect_writable(db_path)
    now = "2026-01-01T00:00:00Z"
    with connection:
        connection.execute(
            """INSERT INTO catalog_sets
               (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at, detail_status_en)
               VALUES ('resolver', 'Resolver', 'SYN', ?, ?, 'present')""",
            (now, now),
        )
        for tcgdex_id, local_id, name in (
            ("aaa-1", "999", "Not Priority"),
            ("zzz-1", "001", "Creature Alpha"),
        ):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id, set_id, local_id, discovered_at, updated_at,
                    brief_source_url, brief_retrieved_at)
                   VALUES (?, 'resolver', ?, ?, ?, 'https://api.tcgdex.net/v2/en/cards', ?)""",
                (tcgdex_id, local_id, now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id, language, status, name, source_url)
                   VALUES (?, 'en', 'not_fetched', ?, 'https://api.tcgdex.net/v2/en/cards')""",
                (tcgdex_id, name),
            )
    connection.close()
    detail = dict(FIXTURE["pokemon_en"])
    detail.update({"id": "zzz-1", "localId": "001", "name": "Creature Alpha"})
    detail["set"] = {"id": "resolver", "name": "Resolver", "cardCount": {"total": 2, "official": 2}}
    client = FakeCatalogClient(1, {"/en/cards/zzz-1": detail})
    result = sync_cards(
        db_path,
        languages="en",
        phase="details",
        prioritize_deck="principal",
        max_requests=1,
        client=client,
    )
    assert result["local_priority_candidates"] == 1
    assert client.calls[0][0] == "/en/cards/zzz-1"
    serialized_calls = json.dumps(client.calls)
    assert "principal" not in serialized_calls
    assert "Creature Alpha" not in serialized_calls


def test_corrupt_refresh_page_preserves_last_safe_index(local_tmp: Path) -> None:
    db_path = local_tmp / "safe-refresh.sqlite3"
    safe_set = {"id": "safe", "name": "Safe", "cardCount": {"total": 1, "official": 1}}
    sync_cards(
        db_path,
        languages="en",
        phase="index",
        max_requests=4,
        client=FakeCatalogClient(
            4, {"/en/sets": _page_route([safe_set]), "/en/cards": _page_route([])}
        ),
    )
    corrupt = [
        {"id": "safe", "name": "Unsafe replacement", "cardCount": {"total": 2, "official": 2}},
        {"id": "broken", "cardCount": []},
    ]
    failed = sync_cards(
        db_path,
        languages="en",
        phase="index",
        refresh_index=True,
        max_requests=1,
        client=FakeCatalogClient(1, {"/en/sets": corrupt}),
    )
    assert failed["error"] is not None
    connection = sqlite3.connect(db_path)
    assert connection.execute(
        "SELECT name_en FROM catalog_sets WHERE tcgdex_id='safe'"
    ).fetchone()[0] == "Safe"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()


def test_card_sheet_exposes_cross_language_aliases_and_missing_fields(local_tmp: Path) -> None:
    db_path = local_tmp / "aliases.sqlite3"
    sync_cards(
        db_path, languages="en,fr", max_requests=8,
        client=FakeCatalogClient(8, _routes()),
    )
    sync_cards(
        db_path, languages="en,fr", phase="details", max_requests=8,
        client=FakeCatalogClient(8, _routes()),
    )
    sheet = show_card(db_path, "syn1-1", "fr")
    assert sheet["printing_identity"]["stable_public_id"] == "syn1-1"
    assert sheet["aliases_by_language"] == {"en": "Twin Name", "fr": "Nom jumeau"}
    assert sheet["set"]["release_date"] == "2026-01-01"
    assert sheet["translations"]["en"]["provenance"]["url"].startswith(
        "https://api.tcgdex.net/"
    )
    assert "regulation_mark" not in sheet["missing_fields"]
    bilingual = search_cards(db_path, "Twin Name", language="all")
    assert "en" in {row["language"] for row in bilingual}
    assert {row["language"] for row in bilingual} <= {"en", "fr"}


def test_reprints_never_inferred_from_a_shared_name(local_tmp: Path) -> None:
    db_path = local_tmp / "reprints.sqlite3"
    sync_cards(
        db_path, languages="en", max_requests=4,
        client=FakeCatalogClient(4, _routes()),
    )
    unknown = card_reprints(db_path, "syn1-1", as_of="2026-10-13")
    assert unknown["status"] == "unknown"
    assert unknown["verified_reprints"] == []
    connection = connect_writable(db_path)
    with connection:
        connection.execute(
            """INSERT INTO official_rule_sources
               (source_id, source_type, url, title, language, consulted_at, captured_at,
                content_sha256, validation_status, rights_note)
               VALUES ('synthetic-reprint-source', 'official_test',
                       'https://www.pokemon.com/us/test', 'Synthetic official source', 'en',
                       '2026-10-13T00:00:00Z', '2026-10-13T00:00:00Z', 'abc',
                       'verified', 'Synthetic fixture only')"""
        )
        connection.execute(
            """INSERT INTO official_rule_assertions
               (assertion_id, source_id, assertion_kind, format, platform,
                effective_from, subject_id, payload_json, validation_status,
                confidence, captured_at)
               VALUES ('synthetic-reprint', 'synthetic-reprint-source',
                       'reprint_equivalence', 'standard', 'live', '2026-01-01',
                       'old1-1', '{"current_printing_id":"syn1-1"}',
                       'verified', 'high', '2026-10-13T00:00:00Z')"""
        )
    connection.close()
    verified = card_reprints(db_path, "syn1-1", as_of="2026-10-13")
    assert verified["status"] == "verified"
    assert verified["verified_reprints"][0]["from_printing_id"] == "old1-1"


def test_unicode_nfc_identity_resolution_is_deterministic(local_tmp: Path) -> None:
    db_path = local_tmp / "unicode.sqlite3"
    deck_text = (ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt").read_text(
        encoding="utf-8"
    ).replace("Creature Alpha", "Créature Alpha")
    import_deck(db_path, deck_text, deck_id="principal", source_kind="stdin")
    connection = connect_writable(db_path)
    decomposed = "Cre\u0301ature Alpha"
    now = "2026-10-13T00:00:00Z"
    with connection:
        connection.execute(
            """INSERT INTO catalog_sets
               (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at,
                detail_status_en)
               VALUES ('unicode-set', 'Unicode', 'SYN', ?, ?, 'present')""",
            (now, now),
        )
        connection.execute(
            """INSERT INTO catalog_printings
               (tcgdex_id, set_id, local_id, discovered_at, updated_at,
                brief_source_url, brief_retrieved_at)
               VALUES ('unicode-1', 'unicode-set', '001', ?, ?,
                       'https://api.tcgdex.net/v2/en/cards', ?)""",
            (now, now, now),
        )
        connection.execute(
            """INSERT INTO catalog_translations
               (printing_id, language, status, name, source_url)
               VALUES ('unicode-1', 'en', 'present', ?,
                       'https://api.tcgdex.net/v2/en/cards/unicode-1')""",
            (decomposed,),
        )
    connection.close()
    result = resolve_deck_cards(db_path, "principal")
    assert result["entries"][0]["status"] == "resolved"
    assert result["entries"][0]["tcgdex_ids"] == ["unicode-1"]


def test_standard_context_precedes_back_catalog_without_private_values(local_tmp: Path) -> None:
    db_path = local_tmp / "standard-priority.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    now = "2026-10-13T00:00:00Z"
    with connection:
        connection.execute(
            """INSERT INTO official_rule_sources
               (source_id, source_type, url, title, language, consulted_at, captured_at,
                content_sha256, validation_status, rights_note)
               VALUES ('rotation-source', 'official_test', 'https://www.pokemon.com/us/test',
                       'Rotation', 'en', ?, ?, 'abc', 'verified', 'Synthetic fixture only')""",
            (now, now),
        )
        connection.execute(
            """INSERT INTO official_rule_assertions
               (assertion_id, source_id, assertion_kind, format, platform,
                effective_from, subject_id, payload_json, validation_status,
                confidence, captured_at)
               VALUES ('rotation', 'rotation-source', 'rotation', 'standard', 'live',
                       '2026-01-01', NULL, '{"allowed_regulation_marks":["H"]}',
                       'verified', 'high', ?)""",
            (now,),
        )
        connection.execute(
            """INSERT INTO catalog_sets
               (tcgdex_id, name_en, discovered_at, updated_at, detail_status_en)
               VALUES ('syn1', 'Synthetic', ?, ?, 'present')""",
            (now, now),
        )
        for tcgdex_id, mark in (("a-back", "G"), ("z-standard", "H")):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id, set_id, local_id, regulation_mark, discovered_at,
                    updated_at, brief_source_url, brief_retrieved_at)
                   VALUES (?, 'syn1', '1', ?, ?, ?,
                           'https://api.tcgdex.net/v2/en/cards', ?)""",
                (tcgdex_id, mark, now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id, language, status, name, source_url)
                   VALUES (?, 'en', 'not_fetched', ?,
                           'https://api.tcgdex.net/v2/en/cards')""",
                (tcgdex_id, tcgdex_id),
            )
    connection.close()
    detail = dict(FIXTURE["pokemon_en"])
    detail.update({"id": "z-standard", "localId": "1", "name": "z-standard"})
    client = FakeCatalogClient(1, {"/en/cards/z-standard": detail})
    result = sync_cards(
        db_path, languages="en", phase="details", max_requests=1, client=client
    )
    assert result["standard_priority_candidates"] == 1
    assert client.calls[0][0] == "/en/cards/z-standard"


def test_binder_browse_pages_named_printings_newest_set_first(local_tmp: Path) -> None:
    from pokemind.cards import browse_cards
    db_path = local_tmp / "catalog.sqlite3"
    for phase in ("discovery", "details"):
        sync_cards(db_path, languages="en,fr", max_requests=8, client=FakeCatalogClient(8, _routes()),
                   **({} if phase == "discovery" else {"phase": "details"}))
    english = browse_cards(db_path, language="en", offset=0, limit=10)
    ids = [card["tcgdex_id"] for card in english["cards"]]
    assert english["total"] == len(ids) and {"syn1-1", "syn1-2", "syn1-3"} <= set(ids)
    assert all(card["language"] == "en" and card["name"] for card in english["cards"])
    syn = [i for i in ids if i.startswith("syn1-")]
    assert syn == ["syn1-1", "syn1-2", "syn1-3"]
    first, second = (browse_cards(db_path, language="en", offset=o, limit=2) for o in (0, 2))
    assert [c["tcgdex_id"] for c in first["cards"] + second["cards"]] == ids[:4]
    french = browse_cards(db_path, language="fr", limit=10)
    assert [c["tcgdex_id"] for c in french["cards"]] == ["syn1-1"]   # absent French texts are not shown
    with pytest.raises(CatalogError):
        browse_cards(db_path, language="en", offset=-1)

