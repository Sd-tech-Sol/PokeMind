from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.meta import (
    LimitlessApiClient,
    MetaError,
    MetaNetworkFailure,
    ProviderRateLimitExhausted,
    RequestBudgetExhausted,
    _SafeRedirectHandler,
    meta_archetypes,
    meta_coverage,
    meta_matchups,
    meta_status,
    meta_tournaments,
    sync_meta,
)


class FakeMetaClient:
    def __init__(self, max_requests: int, routes: dict[str, object]) -> None:
        self.max_requests = max_requests
        self.requests_made = 0
        self.routes = routes
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.last_rate_limit = {"x-ratelimit-remaining": "synthetic"}

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def get_json(self, path: str, params: dict[str, object] | None = None):
        if self.remaining <= 0:
            raise AssertionError("Le code a dépassé le budget synthétique.")
        self.requests_made += 1
        self.calls.append((path, params))
        value = self.routes.get(path)
        if callable(value):
            value = value(path, params)
        if isinstance(value, Exception):
            raise value
        if value is None:
            raise AssertionError(f"Route synthétique absente: {path}")
        return value, f"https://play.limitlesstcg.com/api{path}"


def _games() -> list[dict]:
    return [{"id": "PTCG", "name": "Pokémon TCG", "formats": {"STANDARD": "Standard", "CUSTOM": "Custom"},
             "platforms": {"PTCGL": "Pokémon TCG Live", "TABLETOP": "In person"}, "metagame": True}]


def _brief(tid: str, *, format: str = "STANDARD") -> dict:
    return {"id": tid, "game": "PTCG", "format": format, "name": f"Synthetic {tid}",
            "date": "2026-10-01T18:00:00.000Z", "players": 4}


def _details(tid: str, *, format: str = "STANDARD", platform: str = "PTCGL",
             public: bool = True, online: bool = True, mode: str = "BO1",
             status: str | None = None) -> dict:
    result = {**_brief(tid, format=format), "organizer": {"id": 1, "name": "Ignored"},
              "platform": platform, "decklists": True, "isPublic": public, "isOnline": online,
              "phases": [{"phase": 1, "type": "SWISS", "rounds": 3, "mode": mode}],
              "bannedCards": [], "specialRules": []}
    if status:
        result["status"] = status
    return result


def _standing(player: str, archetype: str | None, placing: int, *, drop: int | None = None) -> dict:
    result = {"player": player, "name": f"PRIVATE-{player}", "country": "CA", "placing": placing,
              "record": {"wins": 1, "losses": 1, "ties": 0}, "drop": drop,
              "decklist": {"cards": ["MUST_NOT_PERSIST"]}}
    result["deck"] = ({"id": archetype, "name": f"Deck {archetype}"} if archetype else None)
    return result


def _routes_two() -> dict[str, object]:
    return {
        "/games": _games(),
        "/tournaments": [_brief("t1"), _brief("t1"), _brief("t2")],
        "/tournaments/t1/details": _details("t1", mode="BO1"),
        "/tournaments/t1/standings": [
            _standing("same-player", "deck-a", 1), _standing("b", "deck-b", 2),
            _standing("unknown", None, 3), _standing("drop", "deck-d", 4, drop=2),
        ],
        "/tournaments/t1/pairings": [
            {"phase": 1, "round": 1, "table": 1, "player1": "same-player", "player2": "b", "winner": "same-player"},
            # Même match inversé: doit remplacer, pas doubler.
            {"phase": 1, "round": 1, "table": 1, "player1": "b", "player2": "same-player", "winner": "same-player"},
            {"phase": 1, "round": 2, "table": 1, "player1": "unknown", "player2": "same-player", "winner": 0},
            {"phase": 1, "round": 2, "table": 2, "player1": "same-player", "player2": "", "winner": "same-player"},
            {"phase": 1, "round": 3, "table": 1, "player1": "same-player", "player2": "b", "winner": 0},
            {"phase": 1, "round": 3, "table": 2, "player1": "b", "player2": "drop", "winner": -1},
        ],
        "/tournaments/t2/details": _details("t2", mode="BO3"),
        "/tournaments/t2/standings": [_standing("same-player", "deck-a", 2), _standing("x", "deck-b", 1)],
        "/tournaments/t2/pairings": [
            {"phase": 1, "round": 1, "match": "T1-1", "player1": "same-player", "player2": "x", "winner": "x"}
        ],
    }


def _routes_for_ids(ids: list[str]) -> dict[str, object]:
    routes: dict[str, object] = {"/games": _games(), "/tournaments": [_brief(tid) for tid in ids]}
    for tid in ids:
        routes[f"/tournaments/{tid}/details"] = _details(tid)
        routes[f"/tournaments/{tid}/standings"] = [
            _standing(f"{tid}-a", "deck-a", 1), _standing(f"{tid}-b", "deck-b", 2)
        ]
        routes[f"/tournaments/{tid}/pairings"] = [
            {"phase": 1, "round": 1, "table": 1, "player1": f"{tid}-a",
             "player2": f"{tid}-b", "winner": f"{tid}-a"}
        ]
    return routes


def _seed_complete_tournaments(db_path: Path, ids: list[str]) -> None:
    connection = connect_writable(db_path)
    initialize_schema(connection)
    with connection:
        connection.executemany(
            """INSERT INTO meta_tournaments
               (tournament_id, name, date_utc, game, format, platform, is_online,
                is_public, provider_status, participant_count, decklists_enabled,
                special_rules_json, banned_cards_count, source_url, fetched_at,
                payload_sha256, snapshot_status)
               VALUES (?, ?, '2026-10-01T18:00:00Z', 'PTCG', 'STANDARD', 'PTCGL',
                       1, 1, 'COMPLETED', 0, 0, '[]', 0, ?,
                       '2026-10-01T19:00:00Z', ?, 'complete')""",
            [
                (
                    tid,
                    f"Synthetic {tid}",
                    f"https://play.limitlesstcg.com/api/tournaments/{tid}/details",
                    (tid.encode().hex() + "0" * 64)[:64],
                )
                for tid in ids
            ],
        )
    connection.close()


def _paged_routes(ids: list[str]) -> dict[str, object]:
    routes = _routes_for_ids(ids)

    def pages(path: str, params: dict[str, object] | None):
        assert params is not None
        page = int(params["page"])
        limit = int(params["limit"])
        start = (page - 1) * limit
        return [_brief(tid) for tid in ids[start:start + limit]]

    routes["/tournaments"] = pages
    return routes


def test_dry_run_has_no_network_or_write(local_tmp: Path) -> None:
    db_path = local_tmp / "missing.sqlite3"
    result = sync_meta(db_path, dry_run=True)
    assert result["network_used"] is False
    assert result["writes"] == 0
    assert result["would_migrate"] is True
    assert not db_path.exists()
    assert result["forbidden_endpoint"] == "/games/{id}/decks"


def test_schema_six_migration_backup_and_invariants(local_tmp: Path) -> None:
    db_path = local_tmp / "migration.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    with connection:
        connection.execute("PRAGMA user_version=6")
        connection.execute("INSERT INTO observed_decks VALUES ('principal', 'observé partiellement', 'x', 'x')")
        connection.execute("""INSERT INTO battle_logs
            (source_sha256, imported_at, parser_version, source_kind, outcome, valid,
             deck_id, recognized_events, warnings_json)
            VALUES ('h', 'x', 'x', 'file', 'W', 1, 'principal', 1, '[]')""")
    connection.close()
    connection = connect_writable(db_path)
    initialize_schema(connection)
    backup = Path(connection.execute("SELECT value FROM metadata WHERE key='last_schema_backup'").fetchone()[0])
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 1
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()
    assert backup.is_file()
    old = sqlite3.connect(backup)
    try:
        assert old.execute("PRAGMA user_version").fetchone()[0] == 6
    finally:
        old.close()


def test_schema_seven_failure_rolls_back_meta_ddl_and_keeps_version_six(local_tmp: Path) -> None:
    db_path = local_tmp / "rollback.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    with connection:
        for table in ("meta_matches", "meta_placements", "meta_phases", "meta_tournaments",
                      "meta_games", "meta_sync_state"):
            connection.execute(f"DROP TABLE IF EXISTS {table}")
        connection.execute("PRAGMA user_version=6")

    def deny_placements(action, arg1, arg2, database, source):
        if action == sqlite3.SQLITE_CREATE_TABLE and arg1 == "meta_placements":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(deny_placements)
    with pytest.raises(sqlite3.DatabaseError):
        initialize_schema(connection)
    connection.set_authorizer(None)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 6
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='meta_tournaments'"
    ).fetchone()[0] == 0
    connection.close()


def test_sync_privacy_dedup_filters_and_offline_stats(local_tmp: Path) -> None:
    db_path = local_tmp / "meta.sqlite3"
    client = FakeMetaClient(8, _routes_two())
    result = sync_meta(db_path, max_requests=8, max_tournaments=2, client=client)
    assert result["error"] is None
    assert result["requests_made"] == 8
    assert len(result["imported"]) == 2
    assert client.calls[1][1] == {"game": "PTCG", "format": "STANDARD", "limit": 6, "page": 1}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    # Les champs personnels et listes ne figurent ni dans le schéma ni dans les valeurs persistées.
    schema = " ".join(row[0] or "" for row in connection.execute(
        "SELECT sql FROM sqlite_master WHERE name LIKE 'meta_%'"
    ))
    assert "country" not in schema.lower() and "decklist_json" not in schema.lower()
    dump = " ".join(str(value) for row in connection.execute(
        "SELECT participant_ref, archetype_id, archetype_name FROM meta_placements"
    ) for value in row)
    assert "PRIVATE-" not in dump and "MUST_NOT_PERSIST" not in dump and "same-player" not in dump
    refs = [row[0] for row in connection.execute(
        "SELECT participant_ref FROM meta_placements WHERE archetype_id='deck-a' ORDER BY tournament_id"
    )]
    assert len(refs) == 2 and refs[0] != refs[1]
    assert connection.execute("SELECT COUNT(*) FROM meta_matches WHERE tournament_id='t1'").fetchone()[0] == 5
    assert connection.execute("SELECT COUNT(*) FROM meta_matches WHERE eligible=0").fetchone()[0] == 2
    endpoint_states = connection.execute(
        "SELECT scope, source_url, payload_sha256 FROM meta_sync_state WHERE scope LIKE 'tournament:t1:%'"
    ).fetchall()
    assert {row[0].rsplit(":", 1)[-1] for row in endpoint_states} == {"details", "standings", "pairings"}
    assert all(row[1].startswith("https://play.limitlesstcg.com/api/") and len(row[2]) == 64
               for row in endpoint_states)
    connection.close()

    tournaments = meta_tournaments(db_path, since="2026-09-01")
    assert tournaments["count"] == 2 and tournaments["filters"]["platform"] == "PTCGL"
    archetypes = meta_archetypes(db_path)
    assert archetypes["n_placements"] == 6 and archetypes["n_classified"] == 5
    matchups = meta_matchups(db_path, "deck-a", min_sample=1)
    assert [(row["mode"], row["wins"], row["losses"], row["n"])
            for row in matchups["matchups"] if row["opponent_archetype"] == "deck-b"] == [
                ("BO1", 1, 0, 2), ("BO3", 0, 1, 1)
            ]
    assert matchups["excluded"]["bye_or_automatic_loss"] == 1
    assert matchups["excluded"]["double_loss"] == 1
    coverage = meta_coverage(db_path, since="2026-09-01")
    assert coverage["tournaments"]["complete_snapshots"] == 2
    assert coverage["placements"] == {
        "classified": 5, "denominator": 6, "ratio": 0.833333,
    }
    assert coverage["matches"]["denominator"] == 6
    assert coverage["matches"]["classifiable"] == 3
    assert {row["mode"] for row in coverage["matches"]["by_phase_and_mode"]} == {
        "BO1", "BO3"
    }
    assert coverage["trainer_hill"]["status"] == "BLOCKED_WITH_REASON"
    assert "winrate" not in json.dumps(coverage).lower()


def test_small_sample_has_no_percentage(local_tmp: Path) -> None:
    db_path = local_tmp / "small.sqlite3"
    sync_meta(db_path, max_requests=8, max_tournaments=2, client=FakeMetaClient(8, _routes_two()))
    rows = meta_matchups(db_path, "deck-a", min_sample=5)["matchups"]
    assert rows and all(row["observed_win_fraction"] is None and row["wilson_95"] is None for row in rows)


def test_meta_coverage_separates_partial_context_and_zero_denominators(
    local_tmp: Path,
) -> None:
    db_path = local_tmp / "coverage-partial.sqlite3"
    _seed_complete_tournaments(db_path, ["complete", "partial"])
    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE meta_tournaments SET snapshot_status='partial' WHERE tournament_id='partial'"
    )
    connection.commit()
    connection.close()

    coverage = meta_coverage(
        db_path, format="standard", platform="PTCGL", online=True, since="2026-01-01"
    )

    assert coverage["tournaments"]["public_in_context"] == 2
    assert coverage["tournaments"]["complete_snapshots"] == 1
    assert coverage["tournaments"]["snapshot_statuses"] == {"complete": 1, "partial": 1}
    assert coverage["placements"]["denominator"] == 0
    assert coverage["placements"]["ratio"] is None
    assert coverage["matches"]["denominator"] == 0
    assert coverage["matches"]["eligible_ratio"] is None
    assert coverage["tournaments"]["provider_finalization_interpretation"] == "unknown"


def test_listing_pagination_skips_duplicates_within_budget(local_tmp: Path) -> None:
    routes = _routes_two()

    def pages(path: str, params: dict[str, object] | None):
        assert params is not None
        return ([_brief("t1")] * 6 if params["page"] == 1 else [_brief("t2")])

    routes["/tournaments"] = pages
    client = FakeMetaClient(9, routes)
    result = sync_meta(local_tmp / "pages.sqlite3", max_requests=9, max_tournaments=2, client=client)
    assert [item["tournament_id"] for item in result["imported"]] == ["t1", "t2"]
    assert [params["page"] for path, params in client.calls if path == "/tournaments"] == [1, 2]
    assert result["requests_made"] == 9


def test_discovery_progresses_across_sessions_on_same_full_first_page(local_tmp: Path) -> None:
    db_path = local_tmp / "resume.sqlite3"
    routes = _routes_for_ids([f"t{i}" for i in range(1, 7)])
    first = sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, routes))
    second = sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, routes))
    assert [row["tournament_id"] for row in first["imported"]] == ["t1"]
    assert [row["tournament_id"] for row in second["imported"]] == ["t2"]
    assert first["mode"] == second["mode"] == "discover"


def test_head_reanalysis_reaches_page_two_after_new_event_insertion(local_tmp: Path) -> None:
    db_path = local_tmp / "head-insertion.sqlite3"
    initial_ids = [f"t{i}" for i in range(1, 7)]
    initial = _routes_for_ids(initial_ids)
    seeded = sync_meta(
        db_path, max_requests=20, max_tournaments=6, client=FakeMetaClient(20, initial)
    )
    assert len(seeded["imported"]) == 6

    routes = _routes_for_ids(["new", *initial_ids, "t7"])

    def shifted_pages(path: str, params: dict[str, object] | None):
        assert params is not None
        if params["page"] == 1:
            return [_brief("new"), *[_brief(tid) for tid in initial_ids[:5]]]
        return [_brief("t6"), _brief("t7")]

    routes["/tournaments"] = shifted_pages
    head = sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, routes))
    resumed_client = FakeMetaClient(6, routes)
    resumed = sync_meta(db_path, max_requests=6, max_tournaments=1, client=resumed_client)
    assert [row["tournament_id"] for row in head["imported"]] == ["new"]
    assert [row["tournament_id"] for row in resumed["imported"]] == ["t7"]
    assert [params["page"] for path, params in resumed_client.calls if path == "/tournaments"] == [1, 2]


@pytest.mark.parametrize(
    "first_filter,second_filter,details",
    [
        (
            {"format": "standard", "platform": "PTCGL", "online": True},
            {"format": "standard", "platform": "PTCGL", "online": False},
            _details("switch", online=False),
        ),
        (
            {"format": "standard", "platform": "PTCGL", "online": False},
            {"format": "standard", "platform": "PTCGL", "online": True},
            _details("switch", online=True),
        ),
        (
            {"format": "standard", "platform": "PTCGL", "online": False},
            {"format": "standard", "platform": "TABLETOP", "online": False},
            _details("switch", platform="TABLETOP", online=False),
        ),
        (
            {"format": "standard", "platform": "PTCGL", "online": True},
            {"format": "custom", "platform": "PTCGL", "online": True},
            _details("switch", format="CUSTOM"),
        ),
    ],
)
def test_discovery_skip_is_scoped_to_requested_filters(
    local_tmp: Path,
    first_filter: dict[str, object],
    second_filter: dict[str, object],
    details: dict,
) -> None:
    db_path = local_tmp / "scoped-skip.sqlite3"
    routes = _routes_for_ids(["switch"])
    routes["/tournaments/switch/details"] = details

    first_client = FakeMetaClient(3, routes)
    first = sync_meta(db_path, max_requests=3, max_tournaments=1, client=first_client, **first_filter)
    assert first["skipped"] and first["imported"] == []
    assert "/tournaments/switch/standings" not in [path for path, _ in first_client.calls]

    second_client = FakeMetaClient(5, routes)
    second = sync_meta(db_path, max_requests=5, max_tournaments=1, client=second_client, **second_filter)
    assert [row["tournament_id"] for row in second["imported"]] == ["switch"]
    assert [path for path, _ in second_client.calls] == [
        "/games", "/tournaments", "/tournaments/switch/details",
        "/tournaments/switch/standings", "/tournaments/switch/pairings",
    ]


def test_private_skip_is_terminal_only_in_scope_and_refresh_rechecks_source_change(local_tmp: Path) -> None:
    db_path = local_tmp / "private-recheck.sqlite3"
    private_routes = _routes_for_ids(["changed"])
    private_routes["/tournaments/changed/details"] = _details("changed", public=False)
    first = sync_meta(
        db_path, max_requests=3, max_tournaments=1,
        client=FakeMetaClient(3, private_routes),
    )
    assert first["skipped"] == [{"tournament_id": "changed", "reason": "private_or_unlisted"}]

    public_routes = _routes_for_ids(["changed"])
    discover_client = FakeMetaClient(2, public_routes)
    unchanged = sync_meta(
        db_path, max_requests=2, max_tournaments=1, client=discover_client,
    )
    assert unchanged["imported"] == []
    assert [path for path, _ in discover_client.calls] == ["/games", "/tournaments"]

    refresh_client = FakeMetaClient(4, public_routes)
    refreshed = sync_meta(
        db_path, max_requests=4, max_tournaments=1, mode="refresh", client=refresh_client,
    )
    assert [row["tournament_id"] for row in refreshed["imported"]] == ["changed"]
    assert [path for path, _ in refresh_client.calls] == [
        "/games", "/tournaments/changed/details",
        "/tournaments/changed/standings", "/tournaments/changed/pairings",
    ]


def test_legacy_unscoped_skip_is_not_universal_terminal_evidence(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy-skip.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    with connection:
        connection.execute(
            """INSERT INTO meta_sync_state
               (scope, source_url, state, fetched_at, payload_sha256,
                requests_total, last_error, updated_at)
               VALUES ('tournament:legacy', ?, 'skipped', NULL, NULL, 1,
                       'online_mismatch', '2026-10-01T00:00:00Z')""",
            ("https://play.limitlesstcg.com/api/tournaments/legacy/details",),
        )
    connection.close()

    client = FakeMetaClient(5, _routes_for_ids(["legacy"]))
    result = sync_meta(db_path, max_requests=5, max_tournaments=1, client=client)
    assert [row["tournament_id"] for row in result["imported"]] == ["legacy"]
    assert "/tournaments/legacy/details" in [path for path, _ in client.calls]


def test_deep_discovery_checkpoint_progresses_across_low_budget_sessions(local_tmp: Path) -> None:
    db_path = local_tmp / "deep-resume.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    routes = _paged_routes([*known, "deep-new"])

    first_client = FakeMetaClient(8, routes)
    first = sync_meta(db_path, max_requests=8, max_tournaments=1, client=first_client)
    assert first["imported"] == []
    assert first["discovery"]["next_page"] == 7
    assert [params["page"] for path, params in first_client.calls if path == "/tournaments"] == [1, 2, 3, 4, 5, 6]

    second_client = FakeMetaClient(8, routes)
    second = sync_meta(db_path, max_requests=8, max_tournaments=1, client=second_client)
    assert [row["tournament_id"] for row in second["imported"]] == ["deep-new"]
    assert [params["page"] for path, params in second_client.calls if path == "/tournaments"] == [1, 6, 7]
    assert second["requests_made"] == 7


def test_deep_candidate_eventually_imports_with_five_get_budget(local_tmp: Path) -> None:
    db_path = local_tmp / "deep-five-get.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    routes = _paged_routes([*known, "deep-new"])

    results = []
    clients = []
    for _ in range(8):
        client = FakeMetaClient(5, routes)
        clients.append(client)
        result = sync_meta(db_path, max_requests=5, max_tournaments=1, client=client)
        results.append(result)
        if result["imported"]:
            break

    assert [row["tournament_id"] for row in results[-1]["imported"]] == ["deep-new"]
    assert len(results) >= 2
    assert all(result["requests_made"] <= 5 for result in results)
    assert [params["page"] for path, params in clients[-1].calls if path == "/tournaments"] == [7]


def test_head_insertion_is_found_without_losing_deep_checkpoint(local_tmp: Path) -> None:
    db_path = local_tmp / "head-and-deep.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    initial_routes = _paged_routes([*known, "deep-new"])
    first = sync_meta(
        db_path, max_requests=8, max_tournaments=1,
        client=FakeMetaClient(8, initial_routes),
    )
    assert first["discovery"]["next_page"] == 7

    shifted_routes = _paged_routes(["head-new", *known, "deep-new"])
    head_client = FakeMetaClient(5, shifted_routes)
    head = sync_meta(db_path, max_requests=5, max_tournaments=1, client=head_client)
    assert [row["tournament_id"] for row in head["imported"]] == ["head-new"]
    assert head["discovery"]["next_page"] == 7

    deep_client = FakeMetaClient(8, shifted_routes)
    deep = sync_meta(db_path, max_requests=8, max_tournaments=1, client=deep_client)
    assert [row["tournament_id"] for row in deep["imported"]] == ["deep-new"]
    assert [params["page"] for path, params in deep_client.calls if path == "/tournaments"] == [1, 6, 7]


def test_interrupted_snapshot_rereads_page_without_losing_candidate(local_tmp: Path) -> None:
    db_path = local_tmp / "interrupted-page.sqlite3"
    routes = _paged_routes(["pending"])
    interrupted_client = FakeMetaClient(4, routes)
    interrupted = sync_meta(
        db_path, max_requests=4, max_tournaments=1, client=interrupted_client,
    )
    assert interrupted["imported"] == []
    assert interrupted["stopped_reason"] == "budget_exhausted"
    assert interrupted["discovery"]["next_page"] == 1
    assert "/tournaments/pending/pairings" not in [path for path, _ in interrupted_client.calls]

    resumed_client = FakeMetaClient(5, routes)
    resumed = sync_meta(db_path, max_requests=5, max_tournaments=1, client=resumed_client)
    assert [row["tournament_id"] for row in resumed["imported"]] == ["pending"]
    assert [params["page"] for path, params in resumed_client.calls if path == "/tournaments"] == [1]


def test_rate_limit_does_not_reset_deep_checkpoint(local_tmp: Path) -> None:
    db_path = local_tmp / "rate-checkpoint.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    routes = _paged_routes([*known, "deep-new"])
    first = sync_meta(db_path, max_requests=8, max_tournaments=1, client=FakeMetaClient(8, routes))
    assert first["discovery"]["next_page"] == 7

    def limited_pages(path: str, params: dict[str, object] | None):
        assert params is not None
        if params["page"] == 6:
            return ProviderRateLimitExhausted("429 synthétique")
        return [_brief(tid) for tid in known[:6]]

    limited_routes = {"/games": _games(), "/tournaments": limited_pages}
    limited = sync_meta(
        db_path, max_requests=8, max_tournaments=1,
        client=FakeMetaClient(8, limited_routes),
    )
    assert limited["stopped_reason"] == "rate_limited"
    assert limited["discovery"]["next_page"] == 7


def test_partial_and_empty_tail_are_revisited_for_later_append(local_tmp: Path) -> None:
    db_path = local_tmp / "tail-revisit.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    routes = _paged_routes(known)
    first = sync_meta(db_path, max_requests=8, max_tournaments=1, client=FakeMetaClient(8, routes))
    assert first["discovery"]["next_page"] == 7

    empty_client = FakeMetaClient(5, routes)
    empty = sync_meta(db_path, max_requests=5, max_tournaments=1, client=empty_client)
    assert empty["stopped_reason"] == "listing_exhausted"
    assert empty["discovery"]["next_page"] == 7
    assert [params["page"] for path, params in empty_client.calls if path == "/tournaments"] == [1, 6, 7]

    appended_routes = _paged_routes([*known, "tail-new"])
    appended = sync_meta(
        db_path, max_requests=7, max_tournaments=1,
        client=FakeMetaClient(7, appended_routes),
    )
    assert [row["tournament_id"] for row in appended["imported"]] == ["tail-new"]


def test_duplicate_between_pages_does_not_hide_new_candidate(local_tmp: Path) -> None:
    db_path = local_tmp / "cross-page-duplicate.sqlite3"
    known = [f"known-{index}" for index in range(1, 7)]
    _seed_complete_tournaments(db_path, known)
    routes = _routes_for_ids([*known, "new"])

    def pages(path: str, params: dict[str, object] | None):
        assert params is not None
        if params["page"] == 1:
            return [_brief(tid) for tid in known]
        return [_brief(known[-1]), _brief("new")]

    routes["/tournaments"] = pages
    client = FakeMetaClient(6, routes)
    result = sync_meta(db_path, max_requests=6, max_tournaments=1, client=client)
    assert [row["tournament_id"] for row in result["imported"]] == ["new"]
    assert [params["page"] for path, params in client.calls if path == "/tournaments"] == [1, 2]


def test_refresh_on_other_filter_does_not_change_discovery_checkpoint(local_tmp: Path) -> None:
    db_path = local_tmp / "refresh-isolation.sqlite3"
    known = [f"known-{index:02d}" for index in range(1, 37)]
    _seed_complete_tournaments(db_path, known)
    routes = _paged_routes([*known, "deep-new"])
    first = sync_meta(db_path, max_requests=8, max_tournaments=1, client=FakeMetaClient(8, routes))
    assert first["discovery"]["next_page"] == 7

    offline_routes = _routes_for_ids(["offline"])
    offline_routes["/tournaments/offline/details"] = _details("offline", online=False, public=False)
    sync_meta(
        db_path, max_requests=3, max_tournaments=1, online=False,
        client=FakeMetaClient(3, offline_routes),
    )
    corrected_routes = _routes_for_ids(["offline"])
    corrected_routes["/tournaments/offline/details"] = _details("offline", online=False)
    refreshed = sync_meta(
        db_path, max_requests=4, max_tournaments=1, online=False, mode="refresh",
        client=FakeMetaClient(4, corrected_routes),
    )
    assert [row["tournament_id"] for row in refreshed["imported"]] == ["offline"]

    connection = sqlite3.connect(db_path)
    raw = connection.execute(
        "SELECT value FROM metadata WHERE key=?",
        ("meta_checkpoint:discovery:PTCG:STANDARD:PTCGL:1",),
    ).fetchone()[0]
    connection.close()
    assert json.loads(raw)["next_page"] == 7


def test_private_candidate_does_not_block_following_public_import(local_tmp: Path) -> None:
    routes = _routes_for_ids(["private", "public"])
    routes["/tournaments/private/details"] = _details("private", public=False)
    client = FakeMetaClient(6, routes)
    result = sync_meta(local_tmp / "skip-forward.sqlite3", max_requests=6, max_tournaments=1, client=client)
    assert [row["tournament_id"] for row in result["imported"]] == ["public"]
    paths = [path for path, _ in client.calls]
    assert "/tournaments/private/standings" not in paths
    assert "/tournaments/private/pairings" not in paths


def test_reprocessing_corrected_result_replaces_match(local_tmp: Path) -> None:
    db_path = local_tmp / "correction.sqlite3"
    routes = _routes_two()
    sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, routes))
    corrected = _routes_two()
    corrected["/tournaments"] = [_brief("t1")]
    corrected["/tournaments/t1/pairings"] = [
        {"phase": 1, "round": 1, "table": 1, "player1": "same-player", "player2": "b", "winner": "b"}
    ]
    sync_meta(
        db_path, max_requests=4, max_tournaments=1, mode="refresh",
        client=FakeMetaClient(4, corrected),
    )
    matchups = meta_matchups(db_path, "deck-a", min_sample=1)
    row = next(row for row in matchups["matchups"] if row["opponent_archetype"] == "deck-b")
    assert (row["wins"], row["losses"], row["n"]) == (0, 1, 1)


def test_refresh_private_marks_old_snapshot_unavailable_without_deleting_history(local_tmp: Path) -> None:
    db_path = local_tmp / "private-refresh.sqlite3"
    sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, _routes_two()))
    routes = {"/games": _games(), "/tournaments/t1/details": _details("t1", public=False)}
    client = FakeMetaClient(2, routes)
    result = sync_meta(
        db_path, max_requests=2, max_tournaments=1, mode="refresh", client=client
    )
    assert result["stopped_reason"] == "refresh_batch_complete"
    assert result["skipped"] == [{"tournament_id": "t1", "reason": "private_or_unlisted"}]
    assert "/tournaments/t1/standings" not in [path for path, _ in client.calls]
    connection = sqlite3.connect(db_path)
    assert connection.execute(
        "SELECT snapshot_status, is_public FROM meta_tournaments WHERE tournament_id='t1'"
    ).fetchone() == ("partial", 0)
    assert connection.execute(
        "SELECT COUNT(*) FROM meta_placements WHERE tournament_id='t1'"
    ).fetchone()[0] > 0
    connection.close()
    assert meta_tournaments(db_path)["count"] == 0


@pytest.mark.parametrize(
    "details,standings,reason",
    [
        (_details("x", public=False), [_standing("a", "deck-a", 1)], "private_or_unlisted"),
        ({**_details("x"), "game": "OTHER"}, [_standing("a", "deck-a", 1)], "game_not_ptcg"),
        (_details("x", format="CUSTOM"), [_standing("a", "deck-a", 1)], "format_mismatch_or_custom"),
        (_details("x", platform="TABLETOP", online=False), [_standing("a", "deck-a", 1)], "platform_mismatch"),
        (_details("x", online=False), [_standing("a", "deck-a", 1)], "online_mismatch"),
        (_details("x", status="CANCELLED"), [_standing("a", "deck-a", 1)], "cancelled"),
        (_details("x"), [], "incomplete_no_standings"),
    ],
)
def test_ineligible_tournament_is_not_persisted(local_tmp: Path, details: dict,
                                                 standings: list[dict], reason: str) -> None:
    routes = {"/games": _games(), "/tournaments": [_brief("x")],
              "/tournaments/x/details": details, "/tournaments/x/standings": standings,
              "/tournaments/x/pairings": []}
    db_path = local_tmp / f"{reason}.sqlite3"
    client = FakeMetaClient(5, routes)
    result = sync_meta(db_path, max_requests=5, max_tournaments=1, client=client)
    assert result["skipped"] == [{"tournament_id": "x", "reason": reason}]
    assert meta_status(db_path)["tournaments"] == 0
    if reason != "incomplete_no_standings":
        assert "/tournaments/x/standings" not in [path for path, _ in client.calls]
    assert "/tournaments/x/pairings" not in [path for path, _ in client.calls]


def test_budget_exhaustion_and_last_good_offline_fallback(local_tmp: Path) -> None:
    db_path = local_tmp / "fallback.sqlite3"
    routes = _routes_two()
    sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, routes))
    budget = sync_meta(db_path, max_requests=2, max_tournaments=1, client=FakeMetaClient(2, routes))
    assert budget["stopped_reason"] == "budget_exhausted"
    assert budget["requests_made"] == 2
    failing = FakeMetaClient(3, {"/games": MetaNetworkFailure("503 synthétique")})
    result = sync_meta(db_path, max_requests=3, max_tournaments=1, client=failing)
    assert result["error"] == "LIMITLESS_INVALID_INPUT_OR_STATE" and result["offline_available"] is True
    assert meta_tournaments(db_path)["count"] == 1
    assert meta_status(db_path)["last_error"]["message"] == "LIMITLESS_INVALID_INPUT_OR_STATE"


class _Headers(dict):
    def items(self):
        return super().items()


class _Response:
    def __init__(self, body: bytes, *, content_type: str = "application/json",
                 url: str = "https://play.limitlesstcg.com/api/games",
                 headers: dict[str, str] | None = None) -> None:
        self.body = io.BytesIO(body)
        self.url = url
        self.read_called = False
        values = {"Content-Type": content_type, "X-RateLimit-Remaining": "5"}
        if headers:
            values.update(headers)
        self.headers = _Headers(values)

    def geturl(self) -> str:
        return self.url

    def read(self, size: int) -> bytes:
        self.read_called = True
        return self.body.read(size)

    def close(self) -> None:
        pass


class _Opener:
    def __init__(self, values: list[object]) -> None:
        self.values = values
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def test_http_429_503_retries_count_against_budget_and_honor_retry_after() -> None:
    delays: list[float] = []
    errors = [
        HTTPError("https://play.limitlesstcg.com/api/games", 429, "rate", {"Retry-After": "0"}, None),
        HTTPError("https://play.limitlesstcg.com/api/games", 503, "down", {}, None),
        _Response(json.dumps(_games()).encode()),
    ]
    client = LimitlessApiClient(3, opener=_Opener(errors), interval=0, sleep=delays.append)
    payload, _ = client.get_json("/games")
    assert payload == _games() and client.requests_made == 3
    assert 1.0 in delays  # backoff 503; les intervalles inter-requêtes sont aussi comptés


def test_truncated_payload_and_protected_endpoint_are_rejected() -> None:
    client = LimitlessApiClient(1, opener=_Opener([_Response(b'{"broken"')]), interval=0)
    with pytest.raises(MetaError, match="tronquée"):
        client.get_json("/games")
    with pytest.raises(MetaError, match="interdit"):
        LimitlessApiClient(1).get_json("/games/PTCG/decks")


def test_success_header_with_zero_remaining_blocks_next_get_without_transmission() -> None:
    opener = _Opener([
        _Response(json.dumps(_games()).encode(), headers={
            "RateLimit": '"synthetic"; r=0; t=60',
            "RateLimit-Policy": '"synthetic"; q=1; w=60',
        })
    ])
    client = LimitlessApiClient(3, opener=opener, interval=0)
    payload, _ = client.get_json("/games")
    assert payload == _games() and client.provider_remaining == 0
    with pytest.raises(ProviderRateLimitExhausted, match="aucun GET additionnel"):
        client.get_json("/tournaments", {"game": "PTCG", "format": "STANDARD", "limit": 6, "page": 1})
    assert opener.calls == 1 and client.requests_made == 1


def test_sync_reports_rate_limited_and_preserves_offline_cache(local_tmp: Path) -> None:
    db_path = local_tmp / "rate.sqlite3"
    sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, _routes_two()))
    opener = _Opener([
        _Response(json.dumps(_games()).encode(), headers={"X-RateLimit-Remaining": "0"})
    ])
    client = LimitlessApiClient(3, opener=opener, interval=0)
    result = sync_meta(db_path, max_requests=3, max_tournaments=1, client=client)
    assert result["stopped_reason"] == "rate_limited"
    assert result["offline_available"] is True
    assert opener.calls == 1
    assert meta_tournaments(db_path)["count"] == 1


def test_refresh_with_only_games_budget_stops_cleanly_without_second_get(local_tmp: Path) -> None:
    db_path = local_tmp / "refresh-budget.sqlite3"
    sync_meta(db_path, max_requests=5, max_tournaments=1, client=FakeMetaClient(5, _routes_two()))
    opener = _Opener([_Response(json.dumps(_games()).encode())])
    client = LimitlessApiClient(1, opener=opener, interval=0)
    result = sync_meta(
        db_path, max_requests=1, max_tournaments=1, mode="refresh", client=client
    )
    assert result["stopped_reason"] == "budget_exhausted"
    assert result["error"] is None and opener.calls == 1


def test_redirect_and_final_url_use_same_public_endpoint_allowlist() -> None:
    protected = "https://play.limitlesstcg.com/api/games/PTCG/decks"
    handler = _SafeRedirectHandler()
    with pytest.raises(MetaNetworkFailure, match="Redirection Limitless refusée"):
        handler.redirect_request(Request("https://play.limitlesstcg.com/api/games"), None, 302, "Found", {}, protected)

    response = _Response(json.dumps(_games()).encode(), url=protected)
    client = LimitlessApiClient(1, opener=_Opener([response]), interval=0)
    with pytest.raises(MetaNetworkFailure, match="URL finale Limitless refusée"):
        client.get_json("/games")
    assert response.read_called is False

    with pytest.raises(MetaNetworkFailure, match="Redirection Limitless refusée"):
        handler.redirect_request(
            Request("https://play.limitlesstcg.com/api/games"), None, 302, "Found", {},
            "https://example.invalid/api/games",
        )


def test_safe_redirect_get_is_debited_before_transmission() -> None:
    safe_target = "https://play.limitlesstcg.com/api/tournaments/t1/details"
    source = Request("https://play.limitlesstcg.com/api/tournaments")

    exhausted = LimitlessApiClient(1, opener=_Opener([]), interval=0)
    exhausted.requests_made = 1  # le GET initial a consommé l'unique unité
    handler = _SafeRedirectHandler(exhausted._before_redirect)
    with pytest.raises(RequestBudgetExhausted, match="Budget de requêtes"):
        handler.redirect_request(source, None, 302, "Found", {}, safe_target)
    assert exhausted.requests_made == 1

    counted = LimitlessApiClient(2, opener=_Opener([]), interval=0)
    counted.requests_made = 1
    redirected = _SafeRedirectHandler(counted._before_redirect).redirect_request(
        source, None, 302, "Found", {}, safe_target
    )
    assert redirected is not None and redirected.full_url == safe_target
    assert counted.requests_made == 2

    provider_limited = LimitlessApiClient(2, opener=_Opener([]), interval=0)
    provider_limited.requests_made = 1
    with pytest.raises(ProviderRateLimitExhausted, match="quota restant de 0"):
        _SafeRedirectHandler(provider_limited._before_redirect).redirect_request(
            source, None, 302, "Found", {"RateLimit": '"synthetic"; r=0; t=60'}, safe_target
        )
    assert provider_limited.requests_made == 1


def test_redirect_budget_exhaustion_is_a_clean_sync_stop(local_tmp: Path) -> None:
    db_path = local_tmp / "redirect-budget.sqlite3"
    client = LimitlessApiClient(1, opener=_Opener([]), interval=0)

    class RedirectingOpener:
        def __init__(self) -> None:
            self.calls = 0
            self.handler = _SafeRedirectHandler(client._before_redirect)

        def open(self, request, timeout):
            self.calls += 1
            return self.handler.redirect_request(
                request, None, 302, "Found", {}, "https://play.limitlesstcg.com/api/games"
            )

    opener = RedirectingOpener()
    client._opener = opener
    result = sync_meta(db_path, max_requests=1, max_tournaments=1, client=client)
    assert result["stopped_reason"] == "budget_exhausted"
    assert result["error"] is None and result["requests_made"] == 1
    assert opener.calls == 1


def test_timeout_retries_are_bounded_and_content_length_is_checked_before_read() -> None:
    opener = _Opener([URLError("timeout synthétique")] * 3)
    client = LimitlessApiClient(3, opener=opener, interval=0, sleep=lambda _: None)
    with pytest.raises(MetaNetworkFailure, match="inaccessible"):
        client.get_json("/games")
    assert opener.calls == 3 and client.requests_made == 3

    oversized = _Response(b"{}", headers={"Content-Length": str(8 * 1024 * 1024 + 1)})
    client = LimitlessApiClient(1, opener=_Opener([oversized]), interval=0)
    with pytest.raises(MetaError, match="volumineuse"):
        client.get_json("/games")
    assert oversized.read_called is False


def test_malformed_rate_headers_do_not_invent_a_permanent_quota() -> None:
    opener = _Opener([
        _Response(json.dumps(_games()).encode(), headers={"RateLimit": "malformed", "X-RateLimit-Remaining": "?"}),
        _Response(b"[]", url="https://play.limitlesstcg.com/api/tournaments"),
    ])
    client = LimitlessApiClient(2, opener=opener, interval=0)
    client.get_json("/games")
    payload, _ = client.get_json("/tournaments")
    assert payload == [] and opener.calls == 2
