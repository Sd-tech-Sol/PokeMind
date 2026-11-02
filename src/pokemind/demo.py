"""Offline first-use rehearsal. Only fresh, disposable synthetic databases."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from pokemind.cards import ApiNotFound, sync_cards
from pokemind.ocr_benchmark import raster_text
from pokemind.recovery import _redirected


QUESTIONS = ("récompenses", "énergie", "banc", "retraite", "mulligan",
             "pioche", "rotation", "entraînement", "métagame", "attaque")


class DemoCatalogClient:
    """Public-shaped responses from the repository's synthetic fixture, no HTTP."""
    def __init__(self, root):
        self.fixture = json.loads((root / "tests/fixtures/cards/catalog_api.json").read_text(encoding="utf-8"))
        self.requests_made = 0
        self.max_requests = 24

    @property
    def remaining(self):
        return self.max_requests - self.requests_made

    def get_json(self, path, params=None):
        if self.remaining <= 0:
            raise ValueError("DEMO_FIXTURE_BUDGET_EXCEEDED")
        self.requests_made += 1
        lang, kind, *identity = path.strip("/").split("/")
        f = self.fixture
        if not identity:
            data = ([f["sets_" + lang][0]] if kind == "sets" else [c for c in f["cards_" + lang] if c["id"].startswith("syn1-")])
            if params["pagination:page"] > 1:
                data = []
        elif kind == "sets":
            data = f["set_syn1_" + lang]
        else:
            key = {"syn1-1": "pokemon_", "syn1-2": "trainer_", "syn1-3": "energy_"}[identity[0]] + lang
            if key not in f:
                raise ApiNotFound("DEMO_SYNTHETIC_TRANSLATION_ABSENT")
            data = f[key]
        return data, "https://example.invalid/synthetic" + path


def _deck(second=False):
    trainers = [f"4 Synthetic Support {i} SYN {i + 1}" for i in range(1, 14)]
    if second:
        trainers[0] = "3 Synthetic Support 1 SYN 2\n1 Synthetic Alternative SYN 90"
    return "Pokémon: 1\n4 Twin Name SYN 1\n\nTrainer: " + str(14 if second else 13) + "\n" + "\n".join(trainers) + "\n\nEnergy: 1\n4 Basic Energy SYN 99\n\nTotal Cards: 60\n"


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _rules_fixture(*, restricted=False, verified=True):
    """Fabricated rules for fabricated cards, never a real Pokémon assertion."""
    status = "verified" if verified else "non_verified"
    common = {"source_id": "synthetic-only", "format": "standard", "platform": "live",
              "effective_from": "2026-01-01", "effective_to": "2026-01-03",
              "validation_status": status, "confidence": "high"}
    assertions = [
        {**common, "assertion_id": "synthetic-rotation", "assertion_kind": "rotation",
         "payload": {"allowed_regulation_marks": ["J"]}},
        {**common, "assertion_id": "synthetic-coverage", "assertion_kind": "restriction_coverage",
         "payload": {"complete": True}},
    ]
    if restricted:
        assertions.append({**common, "assertion_id": "synthetic-restriction", "assertion_kind": "restriction",
                           "subject_id": "syn1-1", "payload": {}})
    return {"registry_version": "SYNTHETIC_ONLY_NOT_REAL_RULES", "consulted_at": "2026-01-01T00:00:00Z",
            "sources": [{"source_id": "synthetic-only", "source_type": "synthetic",
                         "url": "https://www.pokemon.com/synthetic-fixture-not-a-real-rule",
                         "title": "Fabricated demo rules; no actual normative claim", "language": "en",
                         "published_date": "2026-01-01", "validation_status": status,
                         "effective_from": "2026-01-01", "effective_to": "2026-01-03",
                         "rights_note": "Original synthetic fixture"}],
            "assertions": assertions, "deck_structure_rules": [
                {**common, "rule_id": "synthetic-structure", "payload": {
                    "required_total": 60, "same_name_limit": 4, "basic_energy_unlimited": True,
                    "requires_basic_pokemon": True, "copy_limit_exceptions_complete": True,
                    "special_rule_limits_complete": True}}]}


def run_demo(root: Path):
    # No caller-selected DB, clipboard, network, scheduler or existing directory.
    base = root / "data/local/demo-runs"
    if any(_redirected(p) for p in (base, *base.parents)):
        raise ValueError("DEMO_DIRECTORY_UNSAFE")
    base.mkdir(parents=True, exist_ok=True)
    _require(base.resolve().is_relative_to(root.resolve()), "DEMO_DIRECTORY_OUTSIDE_PROJECT")
    environment = os.environ.copy()
    environment.update(POKEMIND_ROOT=str(root), PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1")
    report = {"schema_version": 1, "status": "SYNTHETIC_REHEARSAL_PASSED",
              "owner_database_opened": False, "network_used": False,
              "real_ocr_executed": False, "scheduler_contacted": False, "steps": [], "checkpoints": []}
    with tempfile.TemporaryDirectory(prefix="i-demo-", dir=base) as directory:
        workspace = Path(directory)
        db = workspace / "synthetic.sqlite3"

        def run(*args):
            database_args = [] if args[:2] in {
                ("knowledge", "scheduler"), ("knowledge", "cadence"),
            } else ["--db", str(db)]
            try:
                completed = subprocess.run([sys.executable, "-m", "pokemind", *args, *database_args, "--json"],
                    cwd=root, env=environment, capture_output=True, encoding="utf-8", timeout=45,
                    check=False, creationflags=0x08000000 if os.name == "nt" else 0)
            except subprocess.SubprocessError as exc:
                raise ValueError("DEMO_CLI_PROCESS_FAILED") from exc
            _require(completed.returncode == 0, "DEMO_CLI_STEP_FAILED:" + args[0])
            report["steps"].append(" ".join(args[:2]) if len(args) > 1 and not Path(args[1]).is_absolute() else args[0])
            return json.loads(completed.stdout)

        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
        connection.close()
        report["runtime"] = {"python": platform_version(), "sqlite": sqlite3.sqlite_version, "fts5": True}
        report["checkpoints"].append("runtime_fts")
        seeded = run("import-seed")
        _require(seeded["documents_total"] == 4, "DEMO_SEED_INCOMPLETE")
        _require(run("import-seed")["documents_total"] == 4, "DEMO_SEED_REIMPORT_FAILED")
        report["checkpoints"].append("seed_idempotence")
        citations = []
        for question in QUESTIONS:
            result = run("search", question, "--limit", "1")
            _require(result["count"] == 1, "DEMO_CITATION_MISSING")
            row = result["results"][0]
            citations.append({k: row[k] for k in ("document", "path", "source_date", "start_line", "end_line", "citation")})
        report["library"] = {"documents": 4, "questions": len(citations), "citations": citations}
        report["checkpoints"].append("ten_cited_searches")
        client = DemoCatalogClient(root)
        # Explicit synthetic classifications for the isolated tri-state deck;
        # do not alter the shared catalogue fixture on disk.
        client.fixture["trainer_en"]["regulationMark"] = "J"
        client.fixture["energy_en"].update(energyType="Basic", regulationMark="J")
        sync_cards(db, max_requests=24, phase="balanced", client=client)
        report["cards"] = {lang: run("cards", "search", query, "--lang", lang)["count"]
                           for lang, query in (("en", "Twin Name"), ("fr", "Nom jumeau"))}
        _require(all(report["cards"].values()), "DEMO_CARD_SEARCH_MISSING")
        shown = {lang: run("cards", "show", "syn1-1", "--lang", lang) for lang in ("fr", "en")}
        _require(all(row["provenance"]["url"] for row in shown.values()), "DEMO_CARD_PROVENANCE_MISSING")
        report["card_details"] = {lang: {key: row[key] for key in ("name", "provenance")}
                                  for lang, row in shown.items()}
        report["catalogue_scope"] = "SYNTHETIC_FIXTURE_ONLY; Live/reprints/legality unknown"
        report["checkpoints"].append("bilingual_search_and_show")
        deck_file = workspace / "deck.txt"
        for second in (False, True):
            deck_file.write_text(_deck(second), encoding="utf-8")
            deck = run("deck", "import", str(deck_file), "--deck", "synthetic")
            _require(deck["total_cards"] == 60, "DEMO_DECK_SIZE_INVALID")
        run("deck", "compare", "synthetic", "--from-version", "1", "--to-version", "2")
        exported = run("deck", "export", "synthetic")
        _require(Path(exported["text_path"]).is_relative_to(workspace), "DEMO_EXPORT_OUTSIDE_WORKSPACE")
        reimport = run("deck", "import", exported["text_path"], "--deck", "roundtrip")
        _require(reimport["total_cards"] == 60, "DEMO_EXPORT_ROUNDTRIP_FAILED")
        today = datetime.now(timezone.utc).date().isoformat()
        rules = run("rules", "check-deck", "synthetic", "--format", "standard", "--platform", "live", "--as-of", today)
        report["deck"] = {"cards": 60, "versions": 2, "ptcgl_roundtrip": True, "rules": rules}
        report["deck"]["structure_status"] = rules["structure_validation"]["status"]
        report["checkpoints"].append("deck_versions_export_roundtrip")
        battle_ids = []
        for index in range(5):
            ending = (f"All Prize cards taken. {'SyntheticB' if index == 2 else 'SyntheticA'} wins.\n"
                      if index < 4 else "Synthetic log ends without a known outcome.\n")
            text = ("Setup\nReference player: SyntheticA\n"
                    f"SyntheticA played Synthetic Creature {index} to the Active Spot.\n"
                    "Turn # 1 - SyntheticA's Turn\nSyntheticA drew Synthetic Support.\n"
                    "Turn # 1 - SyntheticB's Turn\nSyntheticB played Synthetic Rival.\n" + ending)
            log = workspace / "battle.txt"
            log.write_text(text, encoding="utf-8")
            first = run("log", "import", str(log), "--deck", "synthetic")
            again = run("log", "import", str(log), "--deck", "synthetic")
            _require(first["battle_id"] == again["battle_id"], "DEMO_DEDUP_FAILED")
            battle_ids.append(first["battle_id"])
        _require(len(set(battle_ids)) == 5, "DEMO_DISTINCT_LOGS_MISSING")
        profile = run("profile", "summary", "--deck", "synthetic")
        review = run("profile", "review", "--deck", "synthetic")
        _require(profile["sample"]["valid_games"] == 5 and profile["assessment_ready"], "DEMO_PROFILE_SAMPLE_INVALID")
        _require(len(review["facts"]) == 5 and profile["limits"], "DEMO_PROFILE_LIMITS_MISSING")
        _require(profile["outcomes"]["unknown"] == 1 and profile["outcomes"]["ratio_denominator"] == 4,
                 "DEMO_AMBIGUOUS_OUTCOME_COUNTED")
        lessons = run("battle", "lessons", "--deck", "synthetic", "--as-of", today)
        _require(lessons["sample"]["valid_battles"] == 5, "DEMO_BATTLE_SAMPLE_INVALID")
        _require(lessons["version_evidence"]["owner_attested"] == 0, "DEMO_INFERRED_VERSION_LINK")
        report["checkpoints"].append("five_logs_dedup_conservative_profile")
        # Collection/credits validate against the local calendar, which may
        # still be yesterday relative to the UTC-dated evidence above.
        recommendation = run("recommend", "deck", "synthetic", "--as-of", date.today().isoformat())
        report["battles"] = {"n": 5, "reimports": 5, "deduplicated": True, "version_links_inferred": 0,
                             "unknown_outcomes": 1, "decided_denominator": 4,
                             "caution": "SYNTHETIC_SMALL_SAMPLE; no cause or card change proven",
                             "recommendation_status": recommendation["status"], "credits": "unknown", "collection": "unknown"}
        report["checkpoints"].append("conditional_recommendation")
        # A card observed in a log never selects a played version. Explicit
        # attestation, idempotent repeat and revocation affect one pair only.
        candidates = run("deck", "link-candidates", "--deck", "synthetic")
        _require(candidates["count"] == 5, "DEMO_FALSE_AUTOLINK")
        link_args = ("--deck", "synthetic", "--battle-id", str(battle_ids[0]), "--version", "2")
        before = db.read_bytes()
        preview = run("deck", "link-battle", *link_args, "--dry-run")
        _require(preview["eligible"] and db.read_bytes() == before, "DEMO_LINK_PREVIEW_MUTATED")
        run("deck", "link-battle", *link_args, "--apply", "--confirm-owner")
        run("deck", "link-battle", *link_args, "--apply", "--confirm-owner")
        evidence = run("deck", "version-evidence", "synthetic", "--as-of", today)
        _require(evidence["facts"]["battles"]["owner_attested_active"] == 1, "DEMO_LINK_IDEMPOTENCE_FAILED")
        unlink_args = ("--deck", "synthetic", "--battle-id", str(battle_ids[0]))
        before = db.read_bytes()
        run("deck", "unlink-battle", *unlink_args, "--dry-run")
        _require(db.read_bytes() == before, "DEMO_UNLINK_PREVIEW_MUTATED")
        run("deck", "unlink-battle", *unlink_args, "--apply", "--confirm-owner")
        evidence = run("deck", "version-evidence", "synthetic", "--as-of", today)
        _require(evidence["facts"]["battles"]["owner_attested_active"] == 0 and
                 evidence["facts"]["battles"]["owner_attested_revoked"] == 1, "DEMO_REVOKED_LINK_ATTRIBUTED")
        report["battle_links"] = {"automatic": 0, "confirmed": 1, "repeat_active_count": 1,
                                  "revoked": 1, "active_after_revocation": 0, "previews_read_only": True}
        report["checkpoints"].append("explicit_link_repeat_revoke")
        changes = workspace / "changes.json"
        changes.write_text(json.dumps({"schema_version": 1, "name": "Synthetic alternative",
            "base_deck": {"deck_id": "synthetic", "version": 2},
            "context": {"format": "standard", "platform": "live", "as_of": today},
            "source": {"kind": "owner_controlled_changes"}, "changes": [
                {"action": "remove", "name": "Synthetic Support 2", "set_code": "SYN", "collector_number": "3", "quantity": 1},
                {"action": "add", "type": "trainer", "name": "Synthetic Alternative", "set_code": "SYN", "collector_number": "90", "quantity": 1},
            ]}), encoding="utf-8")
        before = db.read_bytes()
        preview = run("deck", "candidate-create", "--changes", str(changes), "--dry-run")
        _require(db.read_bytes() == before and preview["status"] == "UNKNOWN_LEGALITY", "DEMO_CANDIDATE_PREVIEW_FAILED")
        candidate = run("deck", "candidate-create", "--changes", str(changes), "--apply", "--confirm-owner")
        identity = str(candidate["candidate_id"])
        shown_candidate = run("deck", "candidate-show", "--candidate", identity)
        _require(shown_candidate["distinct_from_played_version"], "DEMO_CANDIDATE_PLAYED_CONFUSION")
        export_preview = run("deck", "candidate-export", "--candidate", identity, "--dry-run")
        _require(not Path(export_preview["text_path"]).exists(), "DEMO_EXPORT_PREVIEW_WROTE")
        candidate_export = run("deck", "candidate-export", "--candidate", identity, "--apply", "--confirm-owner")
        _require(Path(candidate_export["text_path"]).is_relative_to(workspace), "DEMO_CANDIDATE_EXPORT_OUTSIDE_WORKSPACE")
        imported = run("deck", "import", candidate_export["text_path"], "--deck", "candidate-roundtrip")
        played = run("deck", "show", "synthetic")
        _require(imported["total_cards"] == 60 and played["version"] == 2, "DEMO_CANDIDATE_CHANGED_PLAYED_VERSION")
        report["candidate"] = {"cards": 60, "legality": "unknown", "played_version_unchanged": True,
                               "export_roundtrip": True, "collection": "unknown", "credits_spent": 0}
        report["checkpoints"].append("separate_candidate_roundtrip")
        # A separate, fully resolvable synthetic deck exercises all three
        # verdicts. Even the URLs and verified flags below are test data only.
        deck_file.write_text("Pokémon: 1\n4 Twin Name SYN 1\nTrainer: 1\n4 Coach Unit SYN 2\nEnergy: 1\n52 Test Energy SYN 3\nTotal Cards: 60\n", encoding="utf-8")
        run("deck", "import", str(deck_file), "--deck", "tri-state")
        registry = workspace / "synthetic-rules.json"
        verdicts = []
        for restricted, verified, expected in ((False, True, "legal"), (True, True, "not_legal"), (True, False, "unknown")):
            registry.write_text(json.dumps(_rules_fixture(restricted=restricted, verified=verified)), encoding="utf-8")
            run("rules", "load-official", "--registry", str(registry))
            result = run("rules", "check-deck", "tri-state", "--format", "standard", "--platform", "live", "--as-of", "2026-01-02")
            _require(result["status"] == expected, "DEMO_TRISTATE_FAILED:" + expected)
            verdicts.append(result["status"])
        expired = run("rules", "check-deck", "tri-state", "--format", "standard", "--platform", "live", "--as-of", "2026-01-04")
        _require(expired["status"] == "unknown", "DEMO_EXPIRED_RULE_BECAME_LEGAL")
        report["legality_fixture"] = {"scope": "FABRICATED_RULES_AND_CARDS_ONLY", "verdicts": verdicts,
                                      "unverified_source": "unknown", "expired_source": "unknown"}
        report["checkpoints"].append("synthetic_tristate_expiration")
        session = run("match", "start", "--as-of", today, "--apply", "--confirm-owner")["session_id"]
        image = workspace / "turn.png"
        image.write_bytes(raster_text("SYNTHETIC BOARD"))
        for turn in (1, 2, 3):
            annotation = workspace / "annotation.json"
            annotation.write_text(json.dumps({"turn": turn, "phase": "main", "turn_owner": "self",
                "unknown_fields": ["Synthetic board; active and hidden prizes unknown"],
                "available_actions": [{"description": "Confirmer les informations visibles avant de choisir", "contradicted": False}]}), encoding="utf-8")
            run("match", "observe", "--image", str(image), "--annotation", str(annotation),
                "--session", session, "--turn", str(turn), "--apply", "--confirm-owner")
            advice = run("match", "advise", "--session", session, "--turn", str(turn), "--as-of", today)
            _require(advice["verified_possible_count"] == 0, "DEMO_FALSE_VISUAL_CERTAINTY")
            _require(advice["limits"] and advice["hidden_information"] and advice["next_annotation_or_capture"],
                     "DEMO_VISUAL_UNCERTAINTY_MISSING")
        # Each call above, and this final memory read, is a fresh CLI process.
        memory = run("match", "show", "--session", session)
        _require(len(memory["observations"]) == 3 and memory["images_stored"] == 0, "DEMO_MEMORY_FAILED")
        original = next(r for r in memory["observations"] if r["turn"] == 2)
        annotation.write_text(json.dumps({"turn": 2, "unknown_fields": ["Correction synthétique; identité toujours inconnue"]}), encoding="utf-8")
        run("match", "correct", "--session", session, "--observation", str(original["observation_id"]),
            "--annotation", str(annotation), "--apply", "--confirm-owner")
        revised = run("match", "show", "--session", session)
        _require(len(revised["observations"]) == 4 and sum(r["status"] == "active" for r in revised["observations"]) == 3, "DEMO_CORRECTION_HISTORY_FAILED")
        conflict = run("match", "advise", "--session", session, "--turn", "2",
                       "--as-of", (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat())
        _require(conflict["status"] == "CONTEXT_CONFLICT", "DEMO_CONTEXT_STALE_NOT_REJECTED")
        report["coach"] = {"turns": 3, "fresh_process_resume": True, "pixels_stored": 0,
                           "correction_history_preserved": True, "conflicting_context_rejected": True,
                           "certainty": "owner_annotation_only; hidden information unknown"}
        run("match", "close", "--session", session, "--apply", "--confirm-owner")
        report["checkpoints"].append("visual_memory_correction_close")
        for mode in ("daily", "deep"):
            before = db.read_bytes()
            update = run("knowledge", "update", "--mode", mode, "--dry-run")
            _require(not update["network_used"] and db.read_bytes() == before, "DEMO_DRY_RUN_CHANGED_DATA")
        run("knowledge", "status")
        cadence = run("knowledge", "cadence", "--start-utc", "2026-10-31T00:00:00Z", "--daily-time", "01:30", "--deep-time", "05:00", "--days", "5")
        _require(not cadence["scheduler_contacted"], "DEMO_SCHEDULER_CONTACTED")
        for action in ("install", "status", "uninstall"):
            scheduler = run("knowledge", "scheduler", "--action", action, "--daily-time", "08:15", "--deep-time", "19:30", "--windows-timezone", "Eastern Standard Time", "--dry-run")
            _require(not scheduler["scheduler_contacted"] and not scheduler["system_changed"], "DEMO_SCHEDULER_CHANGED")
        report["cadence"] = {"daily_tue_fri": "simulated_only", "timezone": "America/Toronto; Eastern Standard Time", "install_status_uninstall": "dry_run_only"}
        report["checkpoints"].append("updates_cadence_scheduler_dry_run")
        readiness = run("v1", "readiness")
        _require(readiness["status"] == "NOT_RELEASE_READY", "DEMO_FALSE_RELEASE")
        report["release_status"] = readiness["status"]
        report["checkpoints"].append("readiness_stays_not_release_ready")
        report["blockers"] = readiness["blockers"]
        # Demonstrate instructions can be recovered independently of chat memory.
        report["resume_instructions"] = {name: (root / name).is_file() for name in ("AGENTS.md", ".orchestrator/HANDOFF.md")}
        report["cli_processes"] = len(report["steps"])
        # No paths, logs, board source or DB bytes are included in the report.
        report["deck"].pop("rules")
        report["deck"]["legality"] = rules.get("verdict", rules.get("status", "unknown"))
    report["temporary_workspace_removed"] = True
    return report


def platform_version():
    return ".".join(str(n) for n in sys.version_info[:3])
