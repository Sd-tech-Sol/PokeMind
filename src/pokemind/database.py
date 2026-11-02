"""Schéma SQLite local, import idempotent et diagnostic."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pokemind.markdown import read_markdown
from pokemind.paths import seed_paths


SCHEMA_VERSION = 13


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect_writable(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = DELETE")
    return connection


def connect_readonly(path: Path) -> sqlite3.Connection:
    # URI delimiters in a literal filename must never change the selected DB
    # or hide mode=ro behind a fragment (which can otherwise create a file).
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA query_only = ON")
    return connection


def fts_checks(connection: sqlite3.Connection) -> dict[str, Any]:
    """Check FTS row identity and content, not just equal row counts, read-only."""
    tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    result = {}
    specifications = (
        ("sections", "sections_fts", "f.heading IS NOT s.heading OR f.content IS NOT s.content"),
        ("catalog_translations", "catalog_fts", "f.printing_id IS NOT s.printing_id OR f.language IS NOT s.language OR f.name IS NOT COALESCE(s.name,'') OR f.body IS NOT trim(COALESCE(s.description,'') || ' ' || COALESCE(s.effect,'') || ' ' || COALESCE(s.abilities_json,'') || ' ' || COALESCE(s.attacks_json,''))"),
    )
    for source, index, mismatch in specifications:
        if not {source, index}.issubset(tables):
            continue
        source_count = int(connection.execute(f"SELECT COUNT(*) FROM {source}").fetchone()[0])
        index_count = int(connection.execute(f"SELECT COUNT(*) FROM {index}").fetchone()[0])
        bad_content = int(connection.execute(f"SELECT COUNT(*) FROM {source} s LEFT JOIN {index} f ON f.rowid=s.id WHERE f.rowid IS NULL OR ({mismatch})").fetchone()[0])
        result[index] = {"status": "ok" if source_count == index_count and bad_content == 0 else "mismatch",
                         "source_rows": source_count, "indexed_rows": index_count, "content_mismatch_rows": bad_content}
    return result


def _backup_before_migration(connection: sqlite3.Connection, version: int) -> Path | None:
    """Crée une sauvegarde SQLite cohérente avant une migration réelle."""
    row = connection.execute("PRAGMA database_list").fetchone()
    if row is None or not row[2]:
        return None
    database_path = Path(str(row[2])).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = database_path.with_name(
        f"{database_path.name}.backup-v{version}-{stamp}.sqlite3"
    )
    suffix = 1
    while candidate.exists():
        candidate = database_path.with_name(
            f"{database_path.name}.backup-v{version}-{stamp}-{suffix}.sqlite3"
        )
        suffix += 1
    backup = sqlite3.connect(candidate)
    try:
        connection.backup(backup)
        if str(backup.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
            raise sqlite3.DatabaseError("La sauvegarde de migration est corrompue.")
    finally:
        backup.close()
    return candidate


def _migrate_catalog_schema(connection: sqlite3.Connection) -> str:
    """Ajoute le catalogue PM-0004 dans une transaction réversible."""
    statements = (
        """CREATE TABLE IF NOT EXISTS catalog_sets (
            tcgdex_id TEXT PRIMARY KEY,
            name_en TEXT,
            name_fr TEXT,
            series_id TEXT,
            release_date TEXT,
            card_count_total INTEGER,
            card_count_official INTEGER,
            tcg_online_code TEXT,
            abbreviation_official TEXT,
            abbreviation_localized TEXT,
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            source_url_en TEXT,
            source_url_fr TEXT,
            retrieved_at_en TEXT,
            retrieved_at_fr TEXT,
            detail_status_en TEXT NOT NULL DEFAULT 'not_fetched'
                CHECK(detail_status_en IN ('present', 'absent', 'not_fetched', 'network_error')),
            detail_status_fr TEXT NOT NULL DEFAULT 'not_fetched'
                CHECK(detail_status_fr IN ('present', 'absent', 'not_fetched', 'network_error')),
            content_sha256_en TEXT,
            content_sha256_fr TEXT,
            brief_sha256_en TEXT,
            brief_sha256_fr TEXT,
            detail_stale_en INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_en IN (0, 1)),
            detail_stale_fr INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_fr IN (0, 1)),
            last_error_en TEXT,
            last_error_fr TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS catalog_printings (
            tcgdex_id TEXT PRIMARY KEY,
            set_id TEXT REFERENCES catalog_sets(tcgdex_id),
            local_id TEXT,
            category TEXT,
            hp INTEGER,
            stage TEXT,
            regulation_mark TEXT,
            rarity TEXT,
            illustrator TEXT,
            types_json TEXT,
            variants_json TEXT,
            brief_sha256_en TEXT,
            brief_sha256_fr TEXT,
            detail_stale_en INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_en IN (0, 1)),
            detail_stale_fr INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_fr IN (0, 1)),
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            brief_source_url TEXT NOT NULL,
            brief_retrieved_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS catalog_translations (
            id INTEGER PRIMARY KEY,
            printing_id TEXT NOT NULL REFERENCES catalog_printings(tcgdex_id) ON DELETE CASCADE,
            language TEXT NOT NULL CHECK(language IN ('en', 'fr')),
            status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'not_fetched', 'network_error')),
            name TEXT,
            category TEXT,
            description TEXT,
            effect TEXT,
            trainer_type TEXT,
            energy_type TEXT,
            abilities_json TEXT,
            attacks_json TEXT,
            weaknesses_json TEXT,
            resistances_json TEXT,
            retreat INTEGER,
            source_url TEXT NOT NULL,
            retrieved_at TEXT,
            payload_sha256 TEXT,
            last_error TEXT,
            UNIQUE(printing_id, language)
        )""",
        """CREATE TABLE IF NOT EXISTS catalog_sync_state (
            scope TEXT PRIMARY KEY,
            next_page INTEGER NOT NULL DEFAULT 1 CHECK(next_page >= 1),
            completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
            requests_total INTEGER NOT NULL DEFAULT 0 CHECK(requests_total >= 0),
            end_candidate_page INTEGER,
            started_at TEXT,
            completed_at TEXT,
            last_success_at TEXT,
            last_failure_at TEXT,
            last_error TEXT,
            updated_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS catalog_refresh_state (
            scope TEXT PRIMARY KEY,
            next_page INTEGER NOT NULL DEFAULT 1 CHECK(next_page >= 1),
            in_progress INTEGER NOT NULL DEFAULT 0 CHECK(in_progress IN (0, 1)),
            end_candidate_page INTEGER,
            head_probe_done INTEGER NOT NULL DEFAULT 0 CHECK(head_probe_done IN (0, 1)),
            cycle_started_at TEXT,
            last_completed_at TEXT,
            requests_total INTEGER NOT NULL DEFAULT 0 CHECK(requests_total >= 0),
            pages_scanned_current INTEGER NOT NULL DEFAULT 0 CHECK(pages_scanned_current >= 0),
            items_seen_current INTEGER NOT NULL DEFAULT 0 CHECK(items_seen_current >= 0),
            new_items_current INTEGER NOT NULL DEFAULT 0 CHECK(new_items_current >= 0),
            changed_items_current INTEGER NOT NULL DEFAULT 0 CHECK(changed_items_current >= 0),
            last_success_at TEXT,
            last_failure_at TEXT,
            last_error TEXT,
            updated_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS catalog_printings_set_idx ON catalog_printings(set_id, local_id)",
        "CREATE INDEX IF NOT EXISTS catalog_translations_name_idx ON catalog_translations(language, name)",
        "CREATE INDEX IF NOT EXISTS catalog_sets_tcg_online_idx ON catalog_sets(tcg_online_code)",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        additive_columns = {
            "catalog_sets": (
                "brief_sha256_en TEXT",
                "brief_sha256_fr TEXT",
                "detail_stale_en INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_en IN (0, 1))",
                "detail_stale_fr INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_fr IN (0, 1))",
            ),
            "catalog_printings": (
                "brief_sha256_en TEXT",
                "brief_sha256_fr TEXT",
                "detail_stale_en INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_en IN (0, 1))",
                "detail_stale_fr INTEGER NOT NULL DEFAULT 0 CHECK(detail_stale_fr IN (0, 1))",
            ),
            "catalog_sync_state": (
                "end_candidate_page INTEGER",
                "started_at TEXT",
                "completed_at TEXT",
            ),
        }
        for table, definitions in additive_columns.items():
            existing = {
                str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for definition in definitions:
                column = definition.split()[0]
                if column not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS catalog_fts USING fts5("
                "printing_id UNINDEXED, language UNINDEXED, name, body, "
                "tokenize='unicode61 remove_diacritics 2')"
            )
            catalog_backend = "fts5"
        except sqlite3.OperationalError:
            catalog_backend = "like"
        if catalog_backend == "fts5":
            triggers = (
                """CREATE TRIGGER IF NOT EXISTS catalog_translations_ai
                AFTER INSERT ON catalog_translations BEGIN
                    INSERT INTO catalog_fts(rowid, printing_id, language, name, body)
                    VALUES (
                        new.id, new.printing_id, new.language, COALESCE(new.name, ''),
                        trim(COALESCE(new.description, '') || ' ' || COALESCE(new.effect, '') || ' ' ||
                             COALESCE(new.abilities_json, '') || ' ' || COALESCE(new.attacks_json, ''))
                    );
                END""",
                """CREATE TRIGGER IF NOT EXISTS catalog_translations_ad
                AFTER DELETE ON catalog_translations BEGIN
                    DELETE FROM catalog_fts WHERE rowid = old.id;
                END""",
                """CREATE TRIGGER IF NOT EXISTS catalog_translations_au
                AFTER UPDATE ON catalog_translations BEGIN
                    DELETE FROM catalog_fts WHERE rowid = old.id;
                    INSERT INTO catalog_fts(rowid, printing_id, language, name, body)
                    VALUES (
                        new.id, new.printing_id, new.language, COALESCE(new.name, ''),
                        trim(COALESCE(new.description, '') || ' ' || COALESCE(new.effect, '') || ' ' ||
                             COALESCE(new.abilities_json, '') || ' ' || COALESCE(new.attacks_json, ''))
                    );
                END""",
            )
            for trigger in triggers:
                connection.execute(trigger)
        connection.execute(
            """INSERT INTO metadata(key, value) VALUES('catalog_search_backend', ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (catalog_backend,),
        )
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 5:
            connection.execute("PRAGMA user_version = 5")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return catalog_backend


def _migrate_rules_schema(connection: sqlite3.Connection) -> None:
    """Ajoute le registre normatif PM-0005A sans toucher aux données privées."""
    statements = (
        """CREATE TABLE IF NOT EXISTS official_rule_sources (
            source_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            published_date TEXT,
            consulted_at TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            validation_status TEXT NOT NULL
                CHECK(validation_status IN ('verified', 'navigation_only', 'non_verified', 'conflict')),
            effective_from TEXT,
            effective_to TEXT,
            rights_note TEXT NOT NULL,
            notes TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS official_rule_assertions (
            assertion_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES official_rule_sources(source_id) ON DELETE RESTRICT,
            assertion_kind TEXT NOT NULL
                CHECK(assertion_kind IN ('rotation', 'restriction', 'restriction_coverage',
                     'reprint_equivalence', 'reprint_policy', 'release_window', 'promo', 'errata')),
            format TEXT CHECK(format IN ('standard', 'expanded') OR format IS NULL),
            platform TEXT CHECK(platform IN ('live', 'in_person') OR platform IS NULL),
            effective_from TEXT,
            effective_to TEXT,
            subject_id TEXT,
            payload_json TEXT NOT NULL,
            validation_status TEXT NOT NULL
                CHECK(validation_status IN ('verified', 'non_verified', 'conflict')),
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
            captured_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS official_assertions_scope_idx ON official_rule_assertions(format, platform, effective_from, effective_to)",
        "CREATE INDEX IF NOT EXISTS official_assertions_subject_idx ON official_rule_assertions(subject_id, assertion_kind)",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 6:
            connection.execute("PRAGMA user_version = 6")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_meta_schema(connection: sqlite3.Connection) -> None:
    """Ajoute la fondation Limitless PM-0005B sans données de joueur en clair."""
    statements = (
        """CREATE TABLE IF NOT EXISTS meta_games (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            metagame INTEGER NOT NULL CHECK(metagame IN (0, 1)),
            formats_json TEXT NOT NULL,
            platforms_json TEXT NOT NULL,
            source_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS meta_tournaments (
            tournament_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            date_utc TEXT NOT NULL,
            game TEXT NOT NULL CHECK(game = 'PTCG'),
            format TEXT NOT NULL,
            platform TEXT,
            is_online INTEGER NOT NULL CHECK(is_online IN (0, 1)),
            is_public INTEGER NOT NULL CHECK(is_public IN (0, 1)),
            provider_status TEXT,
            participant_count INTEGER NOT NULL CHECK(participant_count >= 0),
            decklists_enabled INTEGER NOT NULL CHECK(decklists_enabled IN (0, 1)),
            special_rules_json TEXT NOT NULL,
            banned_cards_count INTEGER NOT NULL DEFAULT 0 CHECK(banned_cards_count >= 0),
            source_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            snapshot_status TEXT NOT NULL CHECK(snapshot_status IN ('complete', 'partial'))
        )""",
        """CREATE TABLE IF NOT EXISTS meta_phases (
            tournament_id TEXT NOT NULL REFERENCES meta_tournaments(tournament_id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            phase_type TEXT NOT NULL,
            rounds INTEGER NOT NULL CHECK(rounds >= 0),
            mode TEXT NOT NULL CHECK(mode IN ('BO1', 'BO3', 'BO5', 'UNKNOWN')),
            PRIMARY KEY(tournament_id, phase)
        )""",
        """CREATE TABLE IF NOT EXISTS meta_placements (
            tournament_id TEXT NOT NULL REFERENCES meta_tournaments(tournament_id) ON DELETE CASCADE,
            participant_ref TEXT NOT NULL,
            placing INTEGER,
            wins INTEGER,
            losses INTEGER,
            ties INTEGER,
            dropped_round INTEGER,
            archetype_id TEXT,
            archetype_name TEXT,
            archetype_published INTEGER NOT NULL CHECK(archetype_published IN (0, 1)),
            PRIMARY KEY(tournament_id, participant_ref)
        )""",
        """CREATE TABLE IF NOT EXISTS meta_matches (
            tournament_id TEXT NOT NULL REFERENCES meta_tournaments(tournament_id) ON DELETE CASCADE,
            match_key TEXT NOT NULL,
            phase INTEGER NOT NULL,
            round INTEGER NOT NULL,
            table_number INTEGER,
            match_label TEXT,
            participant1_ref TEXT,
            participant2_ref TEXT,
            outcome TEXT NOT NULL CHECK(outcome IN ('p1', 'p2', 'tie', 'double_loss', 'unknown')),
            eligible INTEGER NOT NULL CHECK(eligible IN (0, 1)),
            exclusion_reason TEXT,
            PRIMARY KEY(tournament_id, match_key),
            FOREIGN KEY(tournament_id, phase)
                REFERENCES meta_phases(tournament_id, phase) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS meta_sync_state (
            scope TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('success', 'error', 'skipped')),
            fetched_at TEXT,
            payload_sha256 TEXT,
            requests_total INTEGER NOT NULL DEFAULT 0 CHECK(requests_total >= 0),
            last_error TEXT,
            updated_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS meta_tournaments_filter_idx ON meta_tournaments(game, format, platform, is_online, date_utc)",
        "CREATE INDEX IF NOT EXISTS meta_placements_archetype_idx ON meta_placements(archetype_id, tournament_id)",
        "CREATE INDEX IF NOT EXISTS meta_matches_eligible_idx ON meta_matches(tournament_id, eligible, phase)",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 7:
            connection.execute("PRAGMA user_version = 7")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_attestation_schema(connection: sqlite3.Connection) -> None:
    """Ajoute le journal PM-0006C sans fabriquer d'attestation historique."""
    statements = (
        """CREATE TABLE IF NOT EXISTS battle_version_attestations (
            id INTEGER PRIMARY KEY,
            battle_id INTEGER NOT NULL REFERENCES battle_logs(id) ON DELETE CASCADE,
            deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
            confirmed_at TEXT NOT NULL,
            actor TEXT NOT NULL CHECK(actor = 'owner_explicit_confirmation'),
            provenance TEXT NOT NULL CHECK(provenance = 'owner_asserted'),
            asserted_battle_date TEXT,
            battle_date_source TEXT NOT NULL
                CHECK(battle_date_source IN ('owner_declared', 'unknown')),
            battle_date_reliability TEXT NOT NULL
                CHECK(battle_date_reliability IN ('owner_asserted', 'unknown')),
            status TEXT NOT NULL CHECK(status IN ('active', 'revoked')),
            revoked_at TEXT,
            reason TEXT NOT NULL CHECK(reason = 'manual_single_pair_confirmation'),
            revocation_reason TEXT,
            CHECK(
                (status = 'active' AND revoked_at IS NULL AND revocation_reason IS NULL)
                OR
                (status = 'revoked' AND revoked_at IS NOT NULL
                    AND revocation_reason = 'owner_explicit_revocation')
            ),
            CHECK(
                (asserted_battle_date IS NULL AND battle_date_source = 'unknown'
                    AND battle_date_reliability = 'unknown')
                OR
                (asserted_battle_date IS NOT NULL AND battle_date_source = 'owner_declared'
                    AND battle_date_reliability = 'owner_asserted')
            )
        )""",
        """CREATE UNIQUE INDEX IF NOT EXISTS battle_version_attestations_one_active
           ON battle_version_attestations(battle_id) WHERE status = 'active'""",
        """CREATE INDEX IF NOT EXISTS battle_version_attestations_history
           ON battle_version_attestations(battle_id, confirmed_at, id)""",
        """CREATE INDEX IF NOT EXISTS battle_version_attestations_version
           ON battle_version_attestations(deck_version_id, status)""",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 8:
            connection.execute("PRAGMA user_version = 8")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_lot_a_schema(connection: sqlite3.Connection) -> None:
    """Ajoute les règles de construction datées du LOT A."""
    statements = (
        """CREATE TABLE IF NOT EXISTS official_deck_structure_rules (
            rule_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES official_rule_sources(source_id) ON DELETE RESTRICT,
            format TEXT CHECK(format IN ('standard', 'expanded') OR format IS NULL),
            platform TEXT CHECK(platform IN ('live', 'in_person') OR platform IS NULL),
            effective_from TEXT,
            effective_to TEXT,
            payload_json TEXT NOT NULL,
            validation_status TEXT NOT NULL
                CHECK(validation_status IN ('verified', 'non_verified', 'conflict')),
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
            captured_at TEXT NOT NULL
        )""",
        """CREATE INDEX IF NOT EXISTS official_deck_structure_scope_idx
           ON official_deck_structure_rules(format, platform, effective_from, effective_to)""",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 9:
            connection.execute("PRAGMA user_version = 9")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_lot_b_schema(connection: sqlite3.Connection) -> None:
    """Ajoute la mémoire personnelle volontaire du LOT B, sans données implicites."""
    statements = (
        """CREATE TABLE IF NOT EXISTS collection_snapshots (
            id INTEGER PRIMARY KEY,
            recorded_at TEXT NOT NULL,
            as_of TEXT NOT NULL,
            source_kind TEXT NOT NULL CHECK(source_kind IN ('owner_provided', 'owner_rollback')),
            source_name TEXT,
            content_sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active', 'superseded')),
            supersedes_id INTEGER REFERENCES collection_snapshots(id) ON DELETE RESTRICT,
            rollback_of_id INTEGER REFERENCES collection_snapshots(id) ON DELETE RESTRICT,
            entry_count INTEGER NOT NULL CHECK(entry_count >= 0),
            total_quantity INTEGER NOT NULL CHECK(total_quantity >= 0),
            resolved_count INTEGER NOT NULL CHECK(resolved_count >= 0),
            ambiguous_count INTEGER NOT NULL CHECK(ambiguous_count >= 0),
            unknown_count INTEGER NOT NULL CHECK(unknown_count >= 0)
        )""",
        """CREATE TABLE IF NOT EXISTS collection_items (
            id INTEGER PRIMARY KEY,
            snapshot_id INTEGER NOT NULL REFERENCES collection_snapshots(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            supplied_tcgdex_id TEXT,
            resolved_tcgdex_id TEXT,
            card_name TEXT NOT NULL,
            set_code TEXT NOT NULL,
            collector_number TEXT NOT NULL,
            variant TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity BETWEEN 0 AND 9999),
            ownership_status TEXT NOT NULL
                CHECK(ownership_status IN ('confirmed_owned', 'reported_missing', 'unknown')),
            resolution_status TEXT NOT NULL
                CHECK(resolution_status IN ('resolved', 'ambiguous', 'unknown')),
            resolution_reason TEXT NOT NULL,
            UNIQUE(snapshot_id, ordinal)
        )""",
        """CREATE TABLE IF NOT EXISTS credit_snapshots (
            id INTEGER PRIMARY KEY,
            recorded_at TEXT NOT NULL,
            as_of TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK(amount >= 0),
            source_kind TEXT NOT NULL CHECK(source_kind IN ('owner_provided', 'owner_rollback')),
            status TEXT NOT NULL CHECK(status IN ('active', 'superseded')),
            supersedes_id INTEGER REFERENCES credit_snapshots(id) ON DELETE RESTRICT,
            rollback_of_id INTEGER REFERENCES credit_snapshots(id) ON DELETE RESTRICT
        )""",
        """CREATE TABLE IF NOT EXISTS battle_lessons (
            id INTEGER PRIMARY KEY,
            battle_id INTEGER NOT NULL REFERENCES battle_logs(id) ON DELETE CASCADE,
            deck_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            lesson_kind TEXT NOT NULL CHECK(lesson_kind IN ('owner_note', 'validated_fact')),
            note_text TEXT NOT NULL,
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low', 'unknown')),
            provenance TEXT NOT NULL CHECK(provenance = 'owner_validated'),
            evidence_ref TEXT NOT NULL,
            public_source_url TEXT,
            public_source_date TEXT,
            dedup_key TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL CHECK(status IN ('active', 'superseded'))
        )""",
        """CREATE TABLE IF NOT EXISTS deck_candidates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            base_deck_id TEXT NOT NULL,
            base_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
            format TEXT NOT NULL CHECK(format IN ('standard', 'expanded')),
            platform TEXT NOT NULL CHECK(platform IN ('live', 'in_person')),
            as_of TEXT NOT NULL,
            source_kind TEXT NOT NULL CHECK(source_kind = 'owner_controlled_changes'),
            change_sha256 TEXT NOT NULL,
            list_sha256 TEXT NOT NULL,
            validation_status TEXT NOT NULL
                CHECK(validation_status IN ('READY_FOR_REVIEW', 'UNKNOWN_LEGALITY',
                     'REJECTED_INVALID_60', 'REJECTED_STRUCTURE')),
            validation_json TEXT NOT NULL,
            lifecycle_status TEXT NOT NULL CHECK(lifecycle_status IN ('active', 'exported')),
            exported_at TEXT,
            export_text_path TEXT,
            export_report_path TEXT,
            UNIQUE(base_version_id, change_sha256)
        )""",
        """CREATE TABLE IF NOT EXISTS deck_candidate_cards (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL REFERENCES deck_candidates(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            card_type TEXT NOT NULL CHECK(card_type IN ('pokemon', 'trainer', 'energy')),
            quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 60),
            card_name TEXT NOT NULL,
            set_code TEXT NOT NULL,
            collector_number TEXT NOT NULL,
            tcgdex_id TEXT,
            identity_status TEXT NOT NULL CHECK(identity_status IN ('resolved', 'ambiguous', 'unknown')),
            UNIQUE(candidate_id, ordinal)
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS collection_one_active ON collection_snapshots(status) WHERE status = 'active'",
        "CREATE INDEX IF NOT EXISTS collection_history_idx ON collection_snapshots(recorded_at, id)",
        "CREATE INDEX IF NOT EXISTS collection_items_identity_idx ON collection_items(snapshot_id, resolved_tcgdex_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS credits_one_active ON credit_snapshots(status) WHERE status = 'active'",
        "CREATE INDEX IF NOT EXISTS credits_history_idx ON credit_snapshots(recorded_at, id)",
        "CREATE INDEX IF NOT EXISTS battle_lessons_scope_idx ON battle_lessons(deck_id, battle_id, status)",
        "CREATE INDEX IF NOT EXISTS deck_candidates_base_idx ON deck_candidates(base_deck_id, created_at)",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_lot_c_schema(connection: sqlite3.Connection) -> None:
    """Ajoute les séances d'entraînement et leur mémoire textuelle, jamais les pixels."""
    existing = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='training_observations'"
    ).fetchone()
    legacy_unique = bool(
        existing
        and existing[0]
        and "UNIQUE(session_id, turn_number, state_sha256)" in str(existing[0])
    )
    if legacy_unique:
        # Le LOT C interdisait deux révisions au contenu identique. Le LOT D retire
        # seulement cette contrainte; l'unicité de l'état actif reste assurée par
        # l'index partiel ci-dessous. La sauvegarde globale a déjà été créée par
        # initialize_schema avant cette migration réelle.
        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                """CREATE TABLE training_observations_v12 (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES training_sessions(session_id) ON DELETE CASCADE,
                    turn_number INTEGER NOT NULL CHECK(turn_number >= 1),
                    recorded_at TEXT NOT NULL,
                    source_kind TEXT NOT NULL CHECK(source_kind IN ('owner_annotation', 'owner_correction')),
                    confidence TEXT NOT NULL CHECK(confidence IN ('certain', 'uncertain', 'unknown')),
                    state_json TEXT NOT NULL,
                    state_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active', 'superseded', 'revoked')),
                    revision_of_id INTEGER REFERENCES training_observations_v12(id) ON DELETE RESTRICT
                )"""
            )
            connection.execute(
                """INSERT INTO training_observations_v12
                   (id,session_id,turn_number,recorded_at,source_kind,confidence,
                    state_json,state_sha256,status,revision_of_id)
                   SELECT id,session_id,turn_number,recorded_at,source_kind,confidence,
                          state_json,state_sha256,status,revision_of_id
                   FROM training_observations"""
            )
            connection.execute("DROP TABLE training_observations")
            connection.execute(
                "ALTER TABLE training_observations_v12 RENAME TO training_observations"
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
    statements = (
        """CREATE TABLE IF NOT EXISTS training_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            closed_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('active', 'closed')),
            mode TEXT NOT NULL CHECK(mode = 'training'),
            format TEXT NOT NULL CHECK(format IN ('standard', 'expanded')),
            platform TEXT NOT NULL CHECK(platform = 'live'),
            context_date TEXT NOT NULL,
            image_storage TEXT NOT NULL CHECK(image_storage = 'none'),
            assistance_scope TEXT NOT NULL CHECK(assistance_scope = 'authorized_training_only')
        )""",
        """CREATE TABLE IF NOT EXISTS training_observations (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES training_sessions(session_id) ON DELETE CASCADE,
            turn_number INTEGER NOT NULL CHECK(turn_number >= 1),
            recorded_at TEXT NOT NULL,
            source_kind TEXT NOT NULL CHECK(source_kind IN ('owner_annotation', 'owner_correction')),
            confidence TEXT NOT NULL CHECK(confidence IN ('certain', 'uncertain', 'unknown')),
            state_json TEXT NOT NULL,
            state_sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active', 'superseded', 'revoked')),
            revision_of_id INTEGER REFERENCES training_observations(id) ON DELETE RESTRICT
        )""",
        "CREATE INDEX IF NOT EXISTS training_observation_session_idx ON training_observations(session_id, turn_number, id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS training_one_active_turn ON training_observations(session_id, turn_number) WHERE status = 'active'",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_lot_d_schema(connection: sqlite3.Connection) -> None:
    """Ajoute seulement l'état des actualisations de connaissances publiques."""
    statements = (
        """CREATE TABLE IF NOT EXISTS knowledge_update_cycles (
            cycle_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL CHECK(mode IN ('daily', 'deep')),
            scope_json TEXT NOT NULL,
            scheduled_local_date TEXT,
            started_at_utc TEXT NOT NULL,
            started_at_local TEXT NOT NULL,
            completed_at_utc TEXT,
            status TEXT NOT NULL CHECK(status IN ('planned', 'attempted', 'completed', 'partial', 'blocked')),
            timezone TEXT NOT NULL CHECK(timezone = 'America/Toronto'),
            request_budget INTEGER NOT NULL CHECK(request_budget >= 0),
            requests_attempted INTEGER NOT NULL DEFAULT 0 CHECK(requests_attempted >= 0),
            report_json TEXT NOT NULL,
            error_code TEXT,
            config_sha256 TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS knowledge_update_source_runs (
            id INTEGER PRIMARY KEY,
            cycle_id TEXT NOT NULL REFERENCES knowledge_update_cycles(cycle_id) ON DELETE CASCADE,
            source TEXT NOT NULL CHECK(source IN ('tcgdex', 'pokemon_official', 'limitless')),
            state TEXT NOT NULL CHECK(state IN ('planned', 'attempted', 'completed', 'partial', 'blocked')),
            started_at_utc TEXT,
            completed_at_utc TEXT,
            request_budget INTEGER NOT NULL CHECK(request_budget >= 0),
            requests_attempted INTEGER NOT NULL DEFAULT 0 CHECK(requests_attempted >= 0),
            new_count INTEGER NOT NULL DEFAULT 0 CHECK(new_count >= 0),
            changed_count INTEGER NOT NULL DEFAULT 0 CHECK(changed_count >= 0),
            missing_count INTEGER NOT NULL DEFAULT 0 CHECK(missing_count >= 0),
            unknown_count INTEGER NOT NULL DEFAULT 0 CHECK(unknown_count >= 0),
            source_url TEXT,
            captured_at TEXT,
            validation_status TEXT NOT NULL CHECK(validation_status IN ('verified', 'non_verified', 'conflict', 'not_applicable')),
            reason_code TEXT,
            detail_json TEXT NOT NULL,
            UNIQUE(cycle_id, source)
        )""",
        """CREATE TABLE IF NOT EXISTS public_source_observations (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            http_status INTEGER,
            content_type TEXT,
            content_length INTEGER,
            etag TEXT,
            last_modified TEXT,
            content_sha256 TEXT,
            truncated INTEGER NOT NULL CHECK(truncated IN (0, 1)),
            observation_state TEXT NOT NULL CHECK(observation_state IN ('new', 'unchanged', 'changed', 'missing', 'unknown')),
            validation_status TEXT NOT NULL CHECK(validation_status IN ('non_verified', 'conflict')),
            UNIQUE(source_id, observed_at)
        )""",
        """CREATE TABLE IF NOT EXISTS knowledge_update_alerts (
            id INTEGER PRIMARY KEY,
            cycle_id TEXT NOT NULL REFERENCES knowledge_update_cycles(cycle_id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('info', 'warning', 'critical')),
            code TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'acknowledged')),
            UNIQUE(cycle_id, source, code)
        )""",
        "CREATE INDEX IF NOT EXISTS knowledge_cycles_status_idx ON knowledge_update_cycles(mode, status, started_at_utc)",
        "CREATE INDEX IF NOT EXISTS knowledge_source_runs_idx ON knowledge_update_source_runs(source, state, completed_at_utc)",
        "CREATE INDEX IF NOT EXISTS public_source_observations_idx ON public_source_observations(source_id, observed_at)",
        "CREATE INDEX IF NOT EXISTS knowledge_alerts_status_idx ON knowledge_update_alerts(status, created_at)",
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_lot_f_schema(connection: sqlite3.Connection) -> None:
    """Allow observations issued by the internal calibrated local adapter."""
    existing = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='training_observations'"
    ).fetchone()
    if not existing or "local_vision" in str(existing[0]):
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
        return
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            """CREATE TABLE training_observations_v13 (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES training_sessions(session_id) ON DELETE CASCADE,
                turn_number INTEGER NOT NULL CHECK(turn_number >= 1),
                recorded_at TEXT NOT NULL,
                source_kind TEXT NOT NULL CHECK(source_kind IN ('owner_annotation', 'owner_correction', 'local_vision')),
                confidence TEXT NOT NULL CHECK(confidence IN ('certain', 'uncertain', 'unknown')),
                state_json TEXT NOT NULL,
                state_sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('active', 'superseded', 'revoked')),
                revision_of_id INTEGER REFERENCES training_observations_v13(id) ON DELETE RESTRICT
            )"""
        )
        connection.execute(
            """INSERT INTO training_observations_v13
               (id,session_id,turn_number,recorded_at,source_kind,confidence,
                state_json,state_sha256,status,revision_of_id)
               SELECT id,session_id,turn_number,recorded_at,source_kind,confidence,
                      state_json,state_sha256,status,revision_of_id
               FROM training_observations"""
        )
        connection.execute("DROP TABLE training_observations")
        connection.execute("ALTER TABLE training_observations_v13 RENAME TO training_observations")
        connection.execute(
            "CREATE INDEX training_observation_session_idx ON training_observations(session_id, turn_number, id)"
        )
        connection.execute(
            "CREATE UNIQUE INDEX training_one_active_turn ON training_observations(session_id, turn_number) WHERE status = 'active'"
        )
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def initialize_schema(connection: sqlite3.Connection) -> str:
    current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if current_version > SCHEMA_VERSION:
        raise sqlite3.DatabaseError(
            f"Version de schéma {current_version} plus récente que {SCHEMA_VERSION}"
        )
    backup_path = None
    if 0 < current_version < SCHEMA_VERSION:
        backup_path = _backup_before_migration(connection, current_version)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            document_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            source_date TEXT,
            content_sha256 TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            heading TEXT NOT NULL,
            heading_path TEXT NOT NULL,
            heading_level INTEGER NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            char_start INTEGER NOT NULL,
            char_end INTEGER NOT NULL,
            content TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            UNIQUE(document_id, ordinal)
        );

        CREATE TABLE IF NOT EXISTS observed_decks (
            deck_id TEXT PRIMARY KEY,
            status TEXT NOT NULL CHECK(status = 'observé partiellement'),
            created_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS battle_logs (
            id INTEGER PRIMARY KEY,
            source_sha256 TEXT NOT NULL UNIQUE,
            imported_at TEXT NOT NULL,
            parser_version TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_name TEXT,
            reference_player TEXT,
            opponent_name TEXT,
            outcome TEXT NOT NULL CHECK(outcome IN ('W', 'L', 'inconnue')),
            winner TEXT,
            valid INTEGER NOT NULL CHECK(valid IN (0, 1)),
            deck_id TEXT REFERENCES observed_decks(deck_id),
            max_turn INTEGER,
            recognized_events INTEGER NOT NULL,
            warnings_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS battle_events (
            id INTEGER PRIMARY KEY,
            battle_id INTEGER NOT NULL REFERENCES battle_logs(id) ON DELETE CASCADE,
            sequence INTEGER NOT NULL,
            turn_number INTEGER,
            actor TEXT,
            actor_role TEXT NOT NULL CHECK(actor_role IN ('self', 'opponent', 'unknown')),
            event_type TEXT NOT NULL,
            card_name TEXT,
            evidence TEXT NOT NULL,
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
            UNIQUE(battle_id, sequence)
        );

        CREATE TABLE IF NOT EXISTS card_observations (
            id INTEGER PRIMARY KEY,
            battle_id INTEGER NOT NULL REFERENCES battle_logs(id) ON DELETE CASCADE,
            event_id INTEGER REFERENCES battle_events(id) ON DELETE CASCADE,
            owner_role TEXT NOT NULL CHECK(owner_role IN ('self', 'opponent', 'unknown')),
            card_name TEXT NOT NULL,
            observation_type TEXT NOT NULL,
            turn_number INTEGER,
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low'))
        );

        CREATE TABLE IF NOT EXISTS deck_versions (
            id INTEGER PRIMARY KEY,
            deck_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            imported_at TEXT NOT NULL,
            approved_at TEXT NOT NULL,
            effective_from TEXT NOT NULL,
            parser_version TEXT NOT NULL,
            source_kind TEXT NOT NULL CHECK(source_kind IN ('clipboard', 'file', 'stdin')),
            source_name TEXT,
            source_encoding TEXT,
            export_sha256 TEXT NOT NULL,
            list_sha256 TEXT NOT NULL,
            total_cards INTEGER NOT NULL CHECK(total_cards = 60),
            entry_count INTEGER NOT NULL CHECK(entry_count > 0),
            exact_confirmed INTEGER NOT NULL CHECK(exact_confirmed = 1),
            sections_json TEXT NOT NULL,
            coverage_json TEXT NOT NULL,
            raw_stored INTEGER NOT NULL DEFAULT 0 CHECK(raw_stored = 0),
            UNIQUE(deck_id, version_number),
            UNIQUE(deck_id, list_sha256)
        );

        CREATE TABLE IF NOT EXISTS deck_version_cards (
            id INTEGER PRIMARY KEY,
            deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            source_line INTEGER NOT NULL,
            card_type TEXT NOT NULL CHECK(card_type IN ('pokemon', 'trainer', 'energy')),
            quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 60),
            card_name TEXT NOT NULL,
            set_code TEXT,
            collector_number TEXT,
            normalized_line TEXT NOT NULL,
            UNIQUE(deck_version_id, ordinal)
        );

        CREATE TABLE IF NOT EXISTS battle_deck_versions (
            battle_id INTEGER PRIMARY KEY REFERENCES battle_logs(id) ON DELETE CASCADE,
            deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
            effective_from TEXT NOT NULL,
            approved_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS battle_logs_deck_idx ON battle_logs(deck_id);
        CREATE INDEX IF NOT EXISTS battle_events_battle_idx ON battle_events(battle_id);
        CREATE INDEX IF NOT EXISTS card_observations_battle_idx ON card_observations(battle_id);
        CREATE INDEX IF NOT EXISTS card_observations_card_idx ON card_observations(card_name);
        CREATE INDEX IF NOT EXISTS deck_versions_deck_idx ON deck_versions(deck_id, version_number);
        CREATE INDEX IF NOT EXISTS deck_version_cards_version_idx ON deck_version_cards(deck_version_id);
        """
    )
    row = connection.execute(
        "SELECT value FROM metadata WHERE key = 'search_backend'"
    ).fetchone()
    backend = row[0] if row else None
    if backend is None:
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE sections_fts USING fts5("
                "heading, content, tokenize='unicode61 remove_diacritics 2')"
            )
            backend = "fts5"
        except sqlite3.OperationalError:
            backend = "like"
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES('search_backend', ?)", (backend,)
        )
    elif backend == "fts5":
        connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5("
            "heading, content, tokenize='unicode61 remove_diacritics 2')"
        )

    if backend == "fts5":
        connection.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS sections_ai AFTER INSERT ON sections BEGIN
                INSERT INTO sections_fts(rowid, heading, content)
                VALUES (new.id, new.heading, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS sections_ad AFTER DELETE ON sections BEGIN
                DELETE FROM sections_fts WHERE rowid = old.id;
            END;
            CREATE TRIGGER IF NOT EXISTS sections_au AFTER UPDATE ON sections BEGIN
                DELETE FROM sections_fts WHERE rowid = old.id;
                INSERT INTO sections_fts(rowid, heading, content)
                VALUES (new.id, new.heading, new.content);
            END;
            """
        )
    connection.commit()
    if current_version < 5:
        _migrate_catalog_schema(connection)
    else:
        _migrate_catalog_schema(connection)
    _migrate_rules_schema(connection)
    _migrate_meta_schema(connection)
    _migrate_attestation_schema(connection)
    _migrate_lot_a_schema(connection)
    _migrate_lot_b_schema(connection)
    _migrate_lot_c_schema(connection)
    _migrate_lot_d_schema(connection)
    _migrate_lot_f_schema(connection)
    if backup_path is not None:
        connection.execute(
            """INSERT INTO metadata(key, value) VALUES('last_schema_backup', ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (str(backup_path),),
        )
    connection.commit()
    return backend


def import_seed(root: Path, db_path: Path) -> dict[str, Any]:
    paths = seed_paths(root)
    connection = connect_writable(db_path)
    try:
        backend = initialize_schema(connection)
        result: dict[str, Any] = {
            "database": str(db_path),
            "search_backend": backend,
            "documents_inserted": 0,
            "documents_updated": 0,
            "documents_unchanged": 0,
            "sections_written": 0,
        }
        completed_at = utc_now()
        with connection:
            for path in paths:
                document = read_markdown(path)
                relative_path = path.relative_to(root).as_posix()
                document_key = path.name
                current = connection.execute(
                    "SELECT id, content_sha256 FROM documents WHERE document_key = ?",
                    (document_key,),
                ).fetchone()
                if current and current["content_sha256"] == document.content_sha256:
                    result["documents_unchanged"] += 1
                    continue
                if current:
                    document_id = int(current["id"])
                    connection.execute("DELETE FROM sections WHERE document_id = ?", (document_id,))
                    connection.execute(
                        """UPDATE documents
                           SET title = ?, path = ?, source_date = ?, content_sha256 = ?, imported_at = ?
                           WHERE id = ?""",
                        (
                            document.title,
                            relative_path,
                            document.source_date,
                            document.content_sha256,
                            completed_at,
                            document_id,
                        ),
                    )
                    result["documents_updated"] += 1
                else:
                    cursor = connection.execute(
                        """INSERT INTO documents
                           (document_key, title, path, source_date, content_sha256, imported_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            document_key,
                            document.title,
                            relative_path,
                            document.source_date,
                            document.content_sha256,
                            completed_at,
                        ),
                    )
                    document_id = int(cursor.lastrowid)
                    result["documents_inserted"] += 1
                rows = [
                    (
                        document_id,
                        section.ordinal,
                        section.heading,
                        section.heading_path,
                        section.heading_level,
                        section.start_line,
                        section.end_line,
                        section.char_start,
                        section.char_end,
                        section.content,
                        section.content_sha256,
                    )
                    for section in document.sections
                ]
                connection.executemany(
                    """INSERT INTO sections
                       (document_id, ordinal, heading, heading_path, heading_level,
                        start_line, end_line, char_start, char_end, content, content_sha256)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    rows,
                )
                result["sections_written"] += len(rows)
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('last_import_completed_at', ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (completed_at,),
            )
        counts = connection.execute(
            "SELECT (SELECT COUNT(*) FROM documents), (SELECT COUNT(*) FROM sections)"
        ).fetchone()
        result["documents_total"] = int(counts[0])
        result["sections_total"] = int(counts[1])
        result["last_import_completed_at"] = completed_at
        return result
    finally:
        connection.close()


def database_status(db_path: Path) -> dict[str, Any]:
    base: dict[str, Any] = {
        "database": str(db_path),
        "database_exists": db_path.is_file(),
        "schema_version": 0,
        "integrity": "absente",
        "documents": 0,
        "sections": 0,
        "battle_logs": 0,
        "valid_battles": 0,
        "exact_decks": 0,
        "deck_versions": 0,
        "catalog_sets": 0,
        "catalog_printings": 0,
        "catalog_translations": 0,
        "catalog_observed_complete": None,
        "official_rule_sources": 0,
        "official_rule_assertions": 0,
        "official_deck_structure_rules": 0,
        "meta_tournaments": 0,
        "meta_matches": 0,
        "collection_snapshots": 0,
        "credit_snapshots": 0,
        "deck_candidates": 0,
        "battle_lessons": 0,
        "last_import_completed_at": None,
        "search_backend": None,
        "external_freshness": "non implémenté",
        "external_sources": {
            "TCGdex": "catalogue absent ou non synchronisé",
            "Limitless": "schéma absent ou jamais synchronisé",
            "règles_officielles": "aucune actualisation réseau dans PM-0002",
        },
        "scheduler": "non installé",
    }
    if not db_path.is_file():
        return base
    try:
        connection = connect_readonly(db_path)
        try:
            base["schema_version"] = int(connection.execute("PRAGMA user_version").fetchone()[0])
            base["integrity"] = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            base["documents"] = int(connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
            base["sections"] = int(connection.execute("SELECT COUNT(*) FROM sections").fetchone()[0])
            if base["schema_version"] >= 2:
                base["battle_logs"] = int(connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0])
                base["valid_battles"] = int(
                    connection.execute("SELECT COUNT(*) FROM battle_logs WHERE valid = 1").fetchone()[0]
                )
            if base["schema_version"] >= 3:
                base["exact_decks"] = int(
                    connection.execute("SELECT COUNT(DISTINCT deck_id) FROM deck_versions").fetchone()[0]
                )
                base["deck_versions"] = int(
                    connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0]
                )
            metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
            if base["schema_version"] >= 4:
                base["catalog_sets"] = int(
                    connection.execute("SELECT COUNT(*) FROM catalog_sets").fetchone()[0]
                )
                base["catalog_printings"] = int(
                    connection.execute("SELECT COUNT(*) FROM catalog_printings").fetchone()[0]
                )
                base["catalog_translations"] = int(
                    connection.execute("SELECT COUNT(*) FROM catalog_translations").fetchone()[0]
                )
                last_catalog = metadata.get("catalog_last_success_at")
                base["external_freshness"] = last_catalog or "jamais synchronisé"
                base["external_sources"]["TCGdex"] = (
                    f"catalogue partiel; dernière réussite {last_catalog}"
                    if last_catalog else "catalogue initialisé, jamais synchronisé"
                )
                if base["schema_version"] >= SCHEMA_VERSION:
                    from pokemind.cards import cards_coverage
                    coverage = cards_coverage(db_path, _connection=connection)
                    observed_complete = coverage["complete"]
                    base["catalog_observed_complete"] = observed_complete
                    if observed_complete:
                        base["external_sources"]["TCGdex"] = (
                            f"catalogue observé complet; dernière réussite {last_catalog}; " +
                            ("instantané Git épinglé" if coverage.get("pinned_source") else "pagination non atomique")
                        )
            if base["schema_version"] >= 6:
                base["official_rule_sources"] = int(
                    connection.execute("SELECT COUNT(*) FROM official_rule_sources").fetchone()[0]
                )
                base["official_rule_assertions"] = int(
                    connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0]
                )
                last_rules = metadata.get("official_rules_loaded_at")
                base["external_sources"]["règles_officielles"] = (
                    f"registre local chargé {last_rules}"
                    if last_rules else "schéma initialisé, aucun registre chargé"
                )
            if base["schema_version"] >= 7:
                base["meta_tournaments"] = int(
                    connection.execute("SELECT COUNT(*) FROM meta_tournaments").fetchone()[0]
                )
                base["meta_matches"] = int(
                    connection.execute("SELECT COUNT(*) FROM meta_matches").fetchone()[0]
                )
                last_meta = metadata.get("meta_last_success_at")
                base["external_sources"]["Limitless"] = (
                    f"instantanés descriptifs; dernière réussite {last_meta}"
                    if last_meta else "schéma initialisé, jamais synchronisé"
                )
            if base["schema_version"] >= 9:
                base["official_deck_structure_rules"] = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM official_deck_structure_rules"
                    ).fetchone()[0]
                )
            if base["schema_version"] >= 10:
                base["collection_snapshots"] = int(
                    connection.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0]
                )
                base["credit_snapshots"] = int(
                    connection.execute("SELECT COUNT(*) FROM credit_snapshots").fetchone()[0]
                )
                base["deck_candidates"] = int(
                    connection.execute("SELECT COUNT(*) FROM deck_candidates").fetchone()[0]
                )
                base["battle_lessons"] = int(
                    connection.execute("SELECT COUNT(*) FROM battle_lessons").fetchone()[0]
                )
            freshness = [
                value for value in (
                    metadata.get("catalog_last_success_at"),
                    metadata.get("official_rules_loaded_at"),
                    metadata.get("meta_last_success_at"),
                ) if value
            ]
            base["external_freshness"] = max(freshness) if freshness else "jamais synchronisé"
            base["last_import_completed_at"] = metadata.get("last_import_completed_at")
            base["search_backend"] = metadata.get("search_backend")
        finally:
            connection.close()
    except sqlite3.DatabaseError:
        base["integrity"] = "erreur_caviardee"
        base["integrity_error_code"] = "LOCAL_DATABASE_ERROR"
    return base
