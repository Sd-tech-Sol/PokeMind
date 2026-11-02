-- Invented empty schema fixture from tracked database.py at 019ee5348dd9771f9dd30d92dfb079e8c6d65c61
-- CREATE only; no user records or downgrade.
CREATE TABLE IF NOT EXISTS catalog_printings (
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
        );

CREATE TABLE IF NOT EXISTS catalog_refresh_state (
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
        );

CREATE TABLE IF NOT EXISTS catalog_sets (
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
        );

CREATE TABLE IF NOT EXISTS catalog_sync_state (
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
        );

CREATE TABLE IF NOT EXISTS catalog_translations (
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
        );

CREATE TABLE IF NOT EXISTS meta_games (
            game_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            metagame INTEGER NOT NULL CHECK(metagame IN (0, 1)),
            formats_json TEXT NOT NULL,
            platforms_json TEXT NOT NULL,
            source_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL
        );

CREATE TABLE IF NOT EXISTS meta_matches (
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
        );

CREATE TABLE IF NOT EXISTS meta_phases (
            tournament_id TEXT NOT NULL REFERENCES meta_tournaments(tournament_id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            phase_type TEXT NOT NULL,
            rounds INTEGER NOT NULL CHECK(rounds >= 0),
            mode TEXT NOT NULL CHECK(mode IN ('BO1', 'BO3', 'BO5', 'UNKNOWN')),
            PRIMARY KEY(tournament_id, phase)
        );

CREATE TABLE IF NOT EXISTS meta_placements (
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
        );

CREATE TABLE IF NOT EXISTS meta_sync_state (
            scope TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('success', 'error', 'skipped')),
            fetched_at TEXT,
            payload_sha256 TEXT,
            requests_total INTEGER NOT NULL DEFAULT 0 CHECK(requests_total >= 0),
            last_error TEXT,
            updated_at TEXT NOT NULL
        );

CREATE TABLE IF NOT EXISTS meta_tournaments (
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
        );

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

CREATE TABLE IF NOT EXISTS official_rule_assertions (
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
        );

CREATE TABLE IF NOT EXISTS official_rule_sources (
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
        );

CREATE VIRTUAL TABLE IF NOT EXISTS catalog_fts USING fts5(printing_id UNINDEXED, language UNINDEXED, name, body, tokenize='unicode61 remove_diacritics 2');

CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(heading, content, tokenize='unicode61 remove_diacritics 2');

CREATE INDEX IF NOT EXISTS catalog_printings_set_idx ON catalog_printings(set_id, local_id);

CREATE INDEX IF NOT EXISTS catalog_sets_tcg_online_idx ON catalog_sets(tcg_online_code);

CREATE INDEX IF NOT EXISTS catalog_translations_name_idx ON catalog_translations(language, name);

CREATE INDEX IF NOT EXISTS meta_matches_eligible_idx ON meta_matches(tournament_id, eligible, phase);

CREATE INDEX IF NOT EXISTS meta_placements_archetype_idx ON meta_placements(archetype_id, tournament_id);

CREATE INDEX IF NOT EXISTS meta_tournaments_filter_idx ON meta_tournaments(game, format, platform, is_online, date_utc);

CREATE INDEX IF NOT EXISTS official_assertions_scope_idx ON official_rule_assertions(format, platform, effective_from, effective_to);

CREATE INDEX IF NOT EXISTS official_assertions_subject_idx ON official_rule_assertions(subject_id, assertion_kind);

CREATE TRIGGER IF NOT EXISTS catalog_translations_ad
                AFTER DELETE ON catalog_translations BEGIN
                    DELETE FROM catalog_fts WHERE rowid = old.id;
                END;

CREATE TRIGGER IF NOT EXISTS catalog_translations_ai
                AFTER INSERT ON catalog_translations BEGIN
                    INSERT INTO catalog_fts(rowid, printing_id, language, name, body)
                    VALUES (
                        new.id, new.printing_id, new.language, COALESCE(new.name, ''),
                        trim(COALESCE(new.description, '') || ' ' || COALESCE(new.effect, '') || ' ' ||
                             COALESCE(new.abilities_json, '') || ' ' || COALESCE(new.attacks_json, ''))
                    );
                END;

CREATE TRIGGER IF NOT EXISTS catalog_translations_au
                AFTER UPDATE ON catalog_translations BEGIN
                    DELETE FROM catalog_fts WHERE rowid = old.id;
                    INSERT INTO catalog_fts(rowid, printing_id, language, name, body)
                    VALUES (
                        new.id, new.printing_id, new.language, COALESCE(new.name, ''),
                        trim(COALESCE(new.description, '') || ' ' || COALESCE(new.effect, '') || ' ' ||
                             COALESCE(new.abilities_json, '') || ' ' || COALESCE(new.attacks_json, ''))
                    );
                END;

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
PRAGMA user_version=7;
