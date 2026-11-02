"""Read-only, explicitly selected battle analysis; developed on invented matches."""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing

from pokemind import battle_logs, competitive, lessons, opponent_observer as observer, version_evidence as versions
from pokemind.battle_sample import conservative_sample
from pokemind.database import connect_readonly
from pokemind.deck_library import reference_index
from pokemind.recovery import _redirected


def selected_database(root, db, *, confirm_owner_read):
    """No file metadata, default path or PUBLIC lookup before explicit opt-in."""
    if db is None or not confirm_owner_read:
        raise ValueError("MATCHUP_EXPLICIT_DATABASE_AND_OWNER_READ_OPT_IN_REQUIRED")
    candidate = db.absolute()
    allowed = root.absolute() / "data/local"
    if ".." in candidate.parts or not candidate.is_relative_to(allowed):
        raise ValueError("MATCHUP_SELECTED_DATABASE_MUST_STAY_IN_PROJECT_LOCAL")
    if any(_redirected(p) for p in (candidate, *candidate.parents)):
        raise ValueError("MATCHUP_DATABASE_REDIRECTED")
    if not candidate.is_file() or candidate.stat().st_nlink != 1:
        raise ValueError("MATCHUP_DATABASE_MISSING_OR_ALIASED_NO_CREATION")
    if any(side.exists() or _redirected(side) for side in
           (candidate.with_name(candidate.name + suffix) for suffix in ("-wal", "-shm", "-journal"))):
        raise ValueError("MATCHUP_DATABASE_SIDECAR_PRESENT_NO_READ")
    return candidate


def _parsed(connection, row):
    events = tuple(battle_logs.ParsedEvent(r["sequence"], r["turn_number"], r["actor"], r["event_type"],
                                         r["card_name"], r["evidence"], r["confidence"])
                   for r in connection.execute("SELECT * FROM battle_events WHERE battle_id=? ORDER BY sequence", (row["id"],)))
    return battle_logs.ParsedBattle(row["reference_player"], row["opponent_name"], row["winner"], row["outcome"],
                                   bool(row["valid"]), row["max_turn"], events, ())


def _outcome(row):
    if not row["reference_player"] or not row["opponent_name"] or not row["winner"]:
        return "unknown"
    if battle_logs._same_name(row["reference_player"], row["opponent_name"]):
        return "unknown"
    proven = ("W" if battle_logs._same_name(row["winner"], row["reference_player"]) else
              "L" if battle_logs._same_name(row["winner"], row["opponent_name"]) else "unknown")
    return {"W": "wins", "L": "losses"}.get(proven, "unknown") if row["outcome"] == proven else "unknown"


def _attested(connection, row, as_of):
    tables = versions._tables(connection)
    if "battle_version_attestations" not in tables:
        return {"status": "unattested", "version": None, "asserted_battle_date": None}
    history = connection.execute("SELECT * FROM battle_version_attestations WHERE battle_id=? ORDER BY confirmed_at,id", (row["id"],)).fetchall()
    state, attestation = versions._attestation_at_date(history, as_of)
    result = {"status": state or "unattested", "version": None, "asserted_battle_date": None,
              "basis": "owner_asserted_not_independently_verified"}
    if state != "owner_attested_active":
        return result
    version = connection.execute("SELECT deck_id,version_number FROM deck_versions WHERE id=?", (attestation["deck_version_id"],)).fetchone()
    if (not version or version["deck_id"] != row["deck_id"] or attestation["actor"] != "owner_explicit_confirmation"
            or attestation["provenance"] != "owner_asserted"):
        return {**result, "status": "ATTESTATION_DECK_OR_PROVENANCE_CONFLICT"}
    link = connection.execute("SELECT deck_version_id FROM battle_deck_versions WHERE battle_id=?", (row["id"],)).fetchone()
    if attestation["status"] == "active" and (not link or link[0] != attestation["deck_version_id"]):
        return {**result, "status": "ATTESTATION_LINK_CONFLICT"}
    version_row, cards = versions._version_rows(connection, row["deck_id"], version["version_number"])
    fact, _ = versions._version_fact(version_row, cards, as_of=as_of)
    if (fact["status"] != "valid" or fact["historical_applicability"] != "applicable"
            or any(versions._date_part(version_row[k]) > as_of for k in ("approved_at", "imported_at", "effective_from"))):
        return {**result, "status": "ATTESTED_VERSION_NOT_EXACT_DATED_60"}
    played_date = versions._date_part(attestation["asserted_battle_date"])
    if attestation["asserted_battle_date"] and (not played_date or played_date > as_of
            or played_date < versions._date_part(version_row["effective_from"])):
        return {**result, "status": "ATTESTED_BATTLE_DATE_CONFLICT"}
    return {**result, "version": version["version_number"], "attestation_id": attestation["id"],
            "confirmed_at": attestation["confirmed_at"], "asserted_battle_date": played_date}


def _schema(connection):
    if not {"battle_logs", "battle_events", "deck_versions", "deck_version_cards", "battle_deck_versions"}.issubset(versions._tables(connection)):
        raise ValueError("MATCHUP_SCHEMA_MISSING_NO_MIGRATION")


def _context(as_of, since=None, until=None):
    competitive._advisor_context(as_of)
    for value in (since, until):
        if value is not None:
            competitive._advisor_context(value)
    if (since and until and since > until) or (until and until > as_of):
        raise ValueError("MATCHUP_DATE_RANGE_INVALID")


def opponent_for_battle(root, db, *, battle_id, as_of, confirm_owner_read=False,
                        public_db=None, reference_db=None, exact_export=None, reviews=None):
    _context(as_of)
    if type(battle_id) is not int or battle_id < 1:
        raise ValueError("MATCHUP_BATTLE_ID_POSITIVE_REQUIRED")
    db = selected_database(root, db, confirm_owner_read=confirm_owner_read)
    if reference_db is not None and public_db is None:
        raise ValueError("MATCHUP_PUBLIC_LIST_DB_REQUIRED_WITH_REFERENCE")
    index = reference_index(root, public_db, as_of=as_of, reference_db=reference_db) if public_db else None
    with closing(connect_readonly(db)) as con:
        _schema(con)
        row = con.execute("SELECT * FROM battle_logs WHERE id=?", (battle_id,)).fetchone()
        if row is None or not versions._date_part(row["imported_at"]) or row["imported_at"][:10] > as_of:
            raise ValueError("MATCHUP_SELECTED_BATTLE_MISSING_OR_FUTURE")
        report = observer.observe(_parsed(con, row), index=index, exact_export=exact_export, reviews=reviews, as_of=as_of,
                                  source_parser_version=row["parser_version"])
        report.update(battle_id=battle_id, parser_version=row["parser_version"], outcome=_outcome(row),
                      player_version=_attested(con, row, as_of), scope="explicit_selected_battle_read_only")
    return report


def matchup_report(root, db, *, deck_id, as_of, confirm_owner_read=False, public_db=None,
                   reference_db=None, since=None, until=None, reviews=None):
    _context(as_of, since, until)
    if not isinstance(deck_id, str) or not battle_logs.DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("MATCHUP_EXPLICIT_DECK_ID_REQUIRED")
    db = selected_database(root, db, confirm_owner_read=confirm_owner_read)
    if reference_db is not None and public_db is None:
        raise ValueError("MATCHUP_PUBLIC_LIST_DB_REQUIRED_WITH_REFERENCE")
    index = reference_index(root, public_db, as_of=as_of, reference_db=reference_db) if public_db else None
    with closing(connect_readonly(db)) as con:
        _schema(con)
        rows = con.execute("SELECT * FROM battle_logs WHERE deck_id=? AND valid=1 ORDER BY imported_at,id", (deck_id,)).fetchall()
        available = [r for r in rows if versions._date_part(r["imported_at"]) and r["imported_at"][:10] <= as_of]
        excluded = {"future_or_invalid_import_date": len(rows) - len(available), "unknown_battle_date": 0, "outside_period": 0}
        eligible = []
        attestations = {r["id"]: _attested(con, r, as_of) for r in available}
        for row in available:
            played_date = attestations[row["id"]]["asserted_battle_date"]
            if (since or until) and not played_date:
                excluded["unknown_battle_date"] += 1
            elif (since and played_date < since) or (until and played_date > until):
                excluded["outside_period"] += 1
            else:
                eligible.append(row)
        sample = conservative_sample(con, (r["id"] for r in eligible))
        selected = [r for r in eligible if r["id"] in sample["battle_ids"]]
        groups = {}
        battles = []
        for row in selected:
            report = observer.observe(_parsed(con, row), index=index, as_of=as_of,
                                      source_parser_version=row["parser_version"],
                                      reviews=[r for r in reviews or [] if r.get("battle_id") == row["id"]])
            version = attestations[row["id"]]
            classification = report["classification"]
            outcome = _outcome(row)
            if len(report["raw_parser_events"]) != row["recognized_events"]:
                outcome = "unknown"
                version = {**version, "version": None, "status": "EVENT_COUNTER_CONFLICT"}
            key = (version["version"], classification["label"], classification["basis"])
            group = groups.setdefault(key, {"deck_id": deck_id, "version": key[0], "opponent_archetype": key[1],
                                           "classification_basis": key[2], "wins": 0, "losses": 0, "unknown": 0,
                                           "battle_ids": [], "cards_observed": set()})
            group[outcome] += 1
            group["battle_ids"].append(row["id"])
            group["cards_observed"].update(c["name"] for c in report["observed_partial"]["cards"])
            battles.append({"battle_id": row["id"], "outcome": outcome, "player_version": version,
                            "opponent": report, "imported_at": row["imported_at"], "first_or_second": "unknown"})
        for group in groups.values():
            group["n"] = group["wins"] + group["losses"]
            group["games"] = group["n"] + group["unknown"]
            group["cards_observed"] = sorted(group["cards_observed"])
            rate_allowed = group["n"] >= 5 and group["version"] is not None and not sample["probable_duplicates_excluded"]
            group["observed_win_ratio"] = group["wins"] / group["n"] if rate_allowed else None
            group["interpretation"] = "descriptive_not_predictive" if rate_allowed else "insufficient_or_provisional_sample"
            group["causal_loss_reason"] = "unknown"
    related_lessons = lessons.battle_lessons(db, deck_id, as_of=as_of)
    return {"model_version": "matchup-analytics-v1", "deck_id": deck_id, "as_of": as_of,
            "requested_period": {"since": since, "until": until, "basis": "owner_asserted_battle_date_only"},
            "sample_review": sample, "excluded": excluded, "valid_games": len(battles),
            "outcomes": {k: sum(b["outcome"] == k for b in battles) for k in ("wins", "losses", "unknown")},
            "groups": sorted(groups.values(), key=lambda g: (g["version"] or 0, g["opponent_archetype"] or "", g["classification_basis"])),
            "battles": battles, "related_lessons": related_lessons,
            "lessons_scope": "separate_self_event_review_as_of;not_added_to_matchup_denominators",
            "version_comparison": "descriptive_counts_only_no_improvement_or_causality_inferred",
            "public_tournament_results_mixed_with_battle_rates": False,
            "hypotheses_to_test": [{"kind": "hypothesis_to_test", "battle_ids": g["battle_ids"],
                "text": "Revoir les décisions visibles et l'installation dans ces défaites; aucune carte fautive ni remplacement démontré."}
                for g in groups.values() if g["losses"]],
            "read_only": True, "network_used": False, "database_mutated": False,
            "scope": "explicit_selected_deck_battles", "validation_scope_at_delivery": "synthetic_matches_only",
            "limits": ["Reference proxies are never exact opponent decks.", "Hidden information and causal loss reasons remain unknown.",
                       "Unknown/revoked/future/legacy version links are never assigned to the current version.",
                       "Small n and probable duplicates suppress win ratios; no claim of improvement.", "V1 NOT_RELEASE_READY"]}


def human_matchups(report):
    print(f"Matchups au {report['as_of']} : {report['valid_games']} parties valides retenues; {report['outcomes']}")
    for group in report["groups"]:
        ratio = group["observed_win_ratio"] if group["observed_win_ratio"] is not None else "unknown"
        print(f"Version {group['version'] or 'unknown'} / {group['opponent_archetype'] or 'unknown'} "
              f"({group['classification_basis']}) : W={group['wins']} L={group['losses']} unknown={group['unknown']}; "
              f"n décidé={group['n']}, parties={group['games']}; ratio={ratio}.")
    print("Effectifs prudents, sources/cartes/proxies et hypothèses : --json. Aucun deck adverse60 ou progrès causal inféré.")
