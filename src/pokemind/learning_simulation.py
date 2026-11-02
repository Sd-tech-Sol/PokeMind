"""A fixed invented FR/EN experiment; never accepts an existing match/log path."""
from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from pokemind import attestations, battle_logs, deck_library, matchup_analytics
from pokemind import learning_loop as loop
from pokemind.counter_deck import counter_plan
from pokemind.decks import import_deck
from pokemind.demo import _deck
from pokemind.recovery import _redirected


def _fiction(number, card, *, french=False, outcome="L"):
    text = "Joueur de référence : FictionalSelf\n" if french else "Reference player: FictionalSelf\n"
    for turn in range(1, 9):
        actor = "FictionalSelf" if turn % 2 else "FictionalRival"
        name = "Synthetic Seed" if turn % 2 else card
        if french:
            text += f"Tour {turn} - Tour de {actor}\n{actor} a pioché une carte.\n{actor} a joué {name}.\n"
        else:
            text += f"Turn # {turn} - {actor}'s Turn\n{actor} drew a card.\n{actor} played {name}.\n"
    if outcome in {"W", "L"}:
        winner = "FictionalSelf" if outcome == "W" else "FictionalRival"
        text += f"{winner} a gagné.\n" if french else f"{winner} wins.\n"
    return text + f"INVENTED SCENARIO {number}\n"


def simulate(root, db, reference_db, *, as_of, target, base=None, use_set_aliases=False):
    # Complete PUBLIC validation before any temporary match database is created.
    plan = counter_plan(root, db, reference_db, as_of=as_of, target=target, base=base,
                        use_set_aliases=use_set_aliases)
    index = deck_library.reference_index(root, db, as_of=as_of, reference_db=reference_db)
    choices = [r for r in index["references"] if r["archetype"].casefold() == target.casefold()]
    other_names = {name for r in index["references"] if r not in choices for name in r["names"]}
    distinctive = sorted({name for r in choices for name in r["names"]} - other_names)
    card = distinctive[0] if distinctive else "Synthetic Unmatched Creature"
    # The same fixed scenario is generated every time, never a replay of a real log.
    local = root.absolute() / "data/local"
    if any(_redirected(p) for p in (local, *local.parents)):
        raise ValueError("LEARNING_SYNTHETIC_DIRECTORY_REDIRECTED")
    local.mkdir(parents=True, exist_ok=True)
    journal = []
    def add(record_id, kind, payload, refs, revises=None):
        nonlocal journal
        journal = loop.append_record(journal, record_id=record_id, kind=kind, recorded_at=as_of,
                                     payload=payload, refs=refs, revises=revises)
    with tempfile.TemporaryDirectory(prefix="synthetic-learning-", dir=local) as directory:
        match_db = Path(directory) / "invented.sqlite3"
        for second in (False, True):
            import_deck(match_db, _deck(second), deck_id="invented", source_kind="stdin")
        with closing(sqlite3.connect(match_db)) as con, con:
            con.execute("UPDATE deck_versions SET imported_at=?,approved_at=?,effective_from=?", (as_of,) * 3)
        def game(number, *, french=False, outcome="L", version=1, observed=card, parser=None):
            text = _fiction(number, observed, french=french, outcome=outcome)
            kwargs = {"parser_version": parser} if parser else {}
            result = battle_logs.import_battle_log(match_db, text, deck_id="invented", source_kind="stdin", **kwargs)
            battle_id = result["battle_id"]
            with closing(sqlite3.connect(match_db)) as con, con:
                con.execute("UPDATE battle_logs SET imported_at=? WHERE id=?",
                            (as_of + ("T09:00:00Z" if parser else "T12:00:00Z"), battle_id))
            if version:
                confirmation = attestations.confirm_battle_version(match_db, "invented", battle_id, version=version,
                    battle_date=as_of, apply=True, confirm_owner=True)
                if not confirmation["eligible"]:
                    raise ValueError("LEARNING_SYNTHETIC_ATTESTATION_FAILED")
                # Fixture timestamps only: artificial attestations, never owner claims.
                with closing(sqlite3.connect(match_db)) as con, con:
                    con.execute("UPDATE battle_version_attestations SET confirmed_at=? WHERE battle_id=?",
                                (as_of + "T12:00:00Z", battle_id))
            return result
        def report():
            return matchup_analytics.matchup_report(root, match_db, deck_id="invented", as_of=as_of,
                confirm_owner_read=True, public_db=db, reference_db=reference_db)
        first = game(1, french=True)
        game(2)
        game(3, outcome="unknown")
        initial = report()
        before = loop.statistics_snapshot(initial)
        add("public-source", "source_fact", {"provenance": plan["alternatives"][0]["source_list"],
            "meaning": "published_list_not_matchup_evidence"}, ["source:public-list"])
        add("loss-event", "observed_game_event", {"provenance": "fixed_invented_FR_EN_scenario",
            "battle_ref": first["battle_id"], "outcome": "losses", "observer": initial["battles"][0]["opponent"]},
            ["source:invented-game-1"])
        add("before", "derived_statistic", before, ["loss-event"])
        add("question", "hypothesis_to_test", {"text": "Tester installation et relais; cause de la défaite inconnue.",
            "target": target, "causal_effect": "unknown"}, ["public-source", "loss-event", "before"])
        add("protocol", "test_plan", plan["alternatives"][0]["test_plan"], ["question", "public-source"])
        game(4, outcome="W", version=2)
        game(5, french=True, version=2)
        game(6, observed="Synthetic Unmatched Creature", version=None)
        duplicate = game(2)  # exact import is idempotent
        game(7, parser="invented-legacy", version=None)  # same anchors as game2, retained originals
        final = report()
        after = loop.statistics_snapshot(final)
        delta = loop.compare_snapshots(before, after)
        add("new-games", "observed_game_event", {"provenance": "fixed_invented_FR_EN_scenario",
            "battle_refs": delta["new_battle_refs"], "facts": "one_v2_win_one_v2_loss_one_ambiguous_unattested"},
            ["source:invented-new-games"])
        add("after", "derived_statistic", after, ["before", "new-games"])
        add("review", "outcome_review", {"reason": "Les effectifs ont changé; petits n, doublon probable, adversaire hypothétique.",
            "delta": delta, "verdict": "inconclusive", "causal_effect": "unknown"},
            ["question", "after", "protocol"], revises="question")
        add("withdrawal", "withdrawn", {"reason": "Retirer toute conclusion prématurée de supériorité; conserver les faits."},
            ["review"], revises="review")
        add("reopened", "hypothesis_to_test", {"reason": "Question réouverte avec protocole plus précis et versions séparées.",
            "text": "Recueillir plusieurs parties attestées par version et relever les coûts/setup observables."},
            ["withdrawal", "after"], revises="withdrawal")
        add("causal-claim", "hypothesis_to_test", {"text": "Le changement de version pourrait causer une amélioration."}, ["after"])
        add("rejection", "rejected", {"reason": "Aucune expérience contrôlée ni effectif suffisant; causalité non démontrée."},
            ["causal-claim", "after"], revises="causal-claim")
    return {"status": "SYNTHETIC_LEARNING_CYCLE_PASSED", "scope": "INVENTED_MATCHES_ONLY",
        "as_of": as_of, "plan": plan, "before": before, "after": after, "delta": delta,
        "journal": journal, "current_view": loop.view(journal, as_of=as_of),
        "lessons": final["related_lessons"], "exact_duplicate_idempotent": duplicate["duplicate"],
        "fictional_deck_versions": 2, "versions_are_not_owner_decks_or_tested_public_alternatives": True,
        "future_import": loop.future_import_contract(), "temporary_workspace_removed": True,
        "owner_database_opened": False, "network_used": False, "release_status": "NOT_RELEASE_READY"}


def human_simulation(report):
    from pokemind.counter_deck import human_counter
    print("SIMULATION — parties FR/EN entièrement inventées; aucune performance réelle.")
    print("Défaite fictive → observation partielle/hypothèse → alternatives PUBLIC et protocole :")
    human_counter(report["plan"])
    for label in ("before", "after"):
        print(f"Évaluation {label} au {report[label]['as_of']}, versions synthétiques séparées :")
        for group in report[label]["groups"]:
            print(f"  v{group['version'] or 'unknown'} / {group['opponent_archetype'] or 'unknown'} "
                  f"({group['classification_basis']}) W={group['wins']} L={group['losses']} "
                  f"unknown={group['unknown']} n={group['n']}; ratio={group['observed_win_ratio']}")
    for row in report["journal"]:
        print(f"[{row['recorded_at']} / {row['kind']}] {row['id']} révise {row['revises'] or 'aucun'}; "
              + row["payload"].get("reason", row["payload"].get("text", "preuves conservées")))
    print("Révision inconclusive; retrait/réouverture et rejet de causalité conservés. Aucun progrès démontré.")
    print("Import réel futur : sélection et consentement par journal/deck/version; interface documentée, aucune exécution.")
