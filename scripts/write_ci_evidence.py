"""Publish aggregate synthetic QA evidence in the current GitHub job summary."""

from __future__ import annotations

import os
import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

from pokemind.cards import _canonical_sha256


def selected_review_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "owner_selected_match_review_reproduction"]
    expected = {
        "scope": "SYNTHETIC_OWNER_SELECTED_MATCH_REVIEW_ONLY", "distinct_consents": 3,
        "exact_exports60": 4, "import_does_not_attest": True, "dry_run_unchanged": True,
        "idempotent_resume": True, "versions_and_revocations": True,
        "hidden_cards_excluded": True, "network_forbidden": True,
        "real_personal_records_opened": False, "no_causal_improvement": True,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate selected review evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(type(report.get(k)) is not type(v) or report[k] != v for k, v in expected.items()):
        raise ValueError("invalid selected review evidence")
    return expected


def counter_learning_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_counter_learning_reproduction"]
    expected = {
        "scope": "SYNTHETIC_COUNTER_DECK_LEARNING_ONLY", "published_options": 4, "cards_per_export": 60,
        "retained_games": 6, "duplicate_excluded": 1, "fictional_versions": 2,
        "before_v1_losses": 2, "before_v1_unknown": 1, "after_v2_wins": 1, "after_v2_losses": 1,
        "ambiguous_unattested_games": 1, "append_only_idempotent_reversible": True,
        "proxy_not_exact": True, "no_causal_improvement": True, "cache_unchanged": True,
        "network_forbidden": True, "real_personal_records_opened": False, "real_public_cache_verified": False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate counter/learning evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(type(report.get(k)) is not type(v) or report[k] != v for k, v in expected.items()):
        raise ValueError("invalid counter/learning evidence")
    return expected


def library_matchup_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_deck_library_matchup_reproduction"]
    expected = {
        'scope': 'SYNTHETIC_DECK_LIBRARY_MATCHUP_ONLY', 'public_compositions': 4, 'public_placements': 6,
        'exports60': 4, 'valid_games': 5, 'v1_hypothesized_losses': 2, 'v1_decided_n': 2,
        'v1_unknown_outcomes': 1, 'v2_hypothesized_wins': 1, 'unattested_games': 1,
        'hidden_draw_excluded': True, 'proxy_is_not_exact_deck': True,
        'duplicates_and_versions_checked': True, 'no_invented_mee_equivalence': True,
        'read_only_unchanged': True, 'network_forbidden': True,
        'real_personal_records_opened': False, 'real_public_cache_verified': False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate library/matchup evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("invalid library/matchup evidence")
    return expected


def knowledge_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_deck_knowledge_reproduction"]
    expected = {
        "scope": "SYNTHETIC_PUBLIC_DECK_KNOWLEDGE_ONLY", "guides": 4, "cards_per_export": 60,
        "sourced_alias_bridge": True, "ambiguous_alias_unknown": True, "no_name_guessing": True,
        "facts_and_hypotheses_separate": True, "unknown_live_and_matchups": True,
        "read_only_cache_unchanged": True, "network_forbidden": True,
        "owner_database_opened": False, "real_public_cache_verified": False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate deck knowledge evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("invalid deck knowledge evidence")
    return expected


def preflight_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_deck_preflight_reproduction"]
    expected = {
        "scope": "SYNTHETIC_PUBLIC_DECK_PREFLIGHT_ONLY", "options": 4, "cards_per_deck": 60,
        "in_person_legal_decks": 4, "live_unknown_decks": 4, "reprint_and_errata_checked": True,
        "separate_public_dbs": True, "read_only_cache_unchanged": True, "network_forbidden": True,
        "owner_database_opened": False, "real_public_cache_verified": False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate public deck preflight evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("invalid public deck preflight evidence")
    return expected


def advisor_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_competitive_advisor_reproduction"]
    expected = {
        'scope': 'SYNTHETIC_OFFLINE_PUBLIC_ADVISOR_ONLY', 'placements': 6, 'distinct_compositions': 4,
        'shortlist_options': 4, 'comparison_shared': 59, 'comparison_removed': 1, 'comparison_added': 1,
        'read_only_cache_unchanged': True, 'network_forbidden': True, 'unknowns_preserved': True,
        'real_public_cache_verified': False, 'owner_database_opened': False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate offline advisor evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("invalid offline advisor evidence")
    return expected


def competitive_reproduction(suites):
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_competitive_reproduction"]
    expected = {
        "scope": "SYNTHETIC_COMPETITIVE_PAGES_ONLY", "events": 1, "lists": 1,
        "total_cards": 60, "idempotent": True, "read_only_offline_export": True,
        "integrity": "ok", "foreign_key_errors": 0, "owner_database_opened": False,
        "real_public_cache_verified": False,
    }
    if len(properties) != 1:
        raise ValueError("missing or duplicate competitive evidence")
    report = json.loads(properties[0])
    if not isinstance(report, dict) or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("invalid competitive evidence scope")
    return expected


def rules_reproduction(suites):
    """Require executed registry evidence, never infer it from a green test count."""
    properties = [node.get("value", "") for suite in suites
                  for node in suite.findall("properties/property")
                  if node.get("name") == "public_rules_reproduction"]
    if len(properties) != 1:
        raise ValueError("missing or duplicate registry evidence")
    report = json.loads(properties[0])
    expected = {
        "scope": "VERSIONED_REGISTRIES_WITH_SYNTHETIC_PRINTINGS",
        "review_sources": 4, "review_assertions": 16,
        "sqlite_totals": {"sources": 15, "assertions": 22, "structure_rules": 1},
        "sql_assertions_match_registries": True, "normative_reload_rows_identical": True,
        "integrity": "ok", "foreign_key_errors": 0, "read_only_verdicts": True,
        "without_catalog": "unknown", "synthetic_printings": 6,
        "local_database_verified": False, "source_documents_revalidated": False,
        "competitive_data_acquired": False,
    }
    if not isinstance(report, dict) or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("invalid evidence scope or checks")
    root = Path(__file__).resolve().parents[1]
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
        "knowledge/curated/official_rules_2026.json",
        "knowledge/curated/official_rules_20261022.json",
    )}
    if report.get("registry_sha256") != hashes:
        raise ValueError("registry evidence does not match checkout")
    canonical = {name: _canonical_sha256(json.loads((root / name).read_bytes().decode("utf-8"))) for name in hashes}
    if report.get("registry_canonical_sha256") != canonical:
        raise ValueError("canonical registry evidence does not match content")
    expected_verdicts = [
        ("sm1-129", "standard", "in_person", "2026-10-22", "legal"),
        ("swsh2-154", "standard", "in_person", "2026-10-22", "legal"),
        ("me01-125", "standard", "in_person", "2026-10-22", "legal"),
        ("me01-114", "standard", "in_person", "2026-10-22", "legal"),
        ("sm5-114", "expanded", "in_person", "2026-10-22", "not_legal"),
        ("sv07-086", "standard", "in_person", "2026-10-22", "unknown"),
        ("me01-125", "standard", "live", "2026-10-22", "unknown"),
        ("me01-125", "standard", "in_person", "2026-10-23", "unknown"),
    ]
    verdicts = report.get("verdicts")
    fields = ("tcgdex_id", "format", "platform", "as_of", "status")
    if not isinstance(verdicts, list) or len(verdicts) != len(expected_verdicts):
        raise ValueError("incomplete verdict evidence")
    if any(not isinstance(row, dict) or tuple(row.get(key) for key in fields) != expected_row
           for row, expected_row in zip(verdicts, expected_verdicts)):
        raise ValueError("unexpected verdict evidence")
    # Emit a fixed whitelist; arbitrary JUnit text is never copied to GitHub.
    return {**expected, "registry_sha256": hashes, "registry_canonical_sha256": canonical,
            "canonical_algorithm": "JSON_UTF8_SORTED_KEYS_COMPACT_UNESCAPED_UNICODE_V1",
            "verdicts": [dict(zip(fields, values)) for values in expected_verdicts]}


def main() -> int:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        print("CI_EVIDENCE_REQUIRES_GITHUB_ACTIONS")
        return 2
    sha = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if (not re.fullmatch(r"[0-9a-f]{40}", sha) or not run_id.isdigit()
            or len(sys.argv) not in {2, 3}
            or len({Path(p).resolve() for p in sys.argv[1:]}) != len(sys.argv) - 1):
        print("CI_EVIDENCE_CONTEXT_INVALID")
        return 2
    suites = []
    for path in sys.argv[1:]:
        document = ElementTree.parse(Path(path)).getroot()
        group = [document] if document.tag == "testsuite" else list(document.findall("testsuite"))
        if not group or not any(int(s.get('tests', '0')) for s in group):
            print("CI_EVIDENCE_TESTS_NOT_GREEN")
            return 2
        suites.extend(group)
    counts = {key: sum(int(suite.get(key, "0")) for suite in suites) for key in ("tests", "failures", "errors", "skipped")}
    if not suites or counts["tests"] < 1 or counts["failures"] or counts["errors"]:
        print("CI_EVIDENCE_TESTS_NOT_GREEN")
        return 2
    try:
        rules = rules_reproduction(suites)
        competitive = competitive_reproduction(suites)
        advisor = advisor_reproduction(suites)
        preflight = preflight_reproduction(suites)
        knowledge = knowledge_reproduction(suites)
        library_matchup = library_matchup_reproduction(suites)
        counter_learning = counter_learning_reproduction(suites)
        selected_review = selected_review_reproduction(suites)
    except (ValueError, TypeError, OSError):
        print("CI_EVIDENCE_RULES_REPRODUCTION_INVALID")
        return 2
    passed = counts["tests"] - counts["skipped"]
    repository = os.environ.get("GITHUB_REPOSITORY", "Sd-tech-Sol/PokeMind")
    url = f"https://github.com/{repository}/actions/runs/{run_id}"
    body = (
        f"## PokeMind — TECHNICAL_TESTS_GREEN · {platform.system()}\n\n"
        f"Commit testé : `{sha}`. [Run GitHub Actions]({url}).\n\n"
        f"Tests : **{passed} passed, {counts['skipped']} skipped**, 0 failure/error.\n\n"
        "Compilation, hygiène Git et diff check exécutés avant cette preuve.\n\n"
        "Fixtures synthétiques/hors ligne seulement. Les skips sont explicités dans les logs. "
        "Ce statut ne prouve ni vision propriétaire, ni données exhaustives, ni mise en service. "
        "V1 NOT_RELEASE_READY; audit indépendant ChatGPT requis, aucun VERIFIED autoattribué.\n"
        "\n## Registres officiels reproduits dans une SQLite neuve\n\n"
        "Registre courant : **4 sources / 16 assertions**. Après les deux registres : "
        "**15 sources / 22 assertions / 1 règle de structure**. Lignes SQL comparées, "
        "rechargement stable, intégrité/FK et huit décisions contrôlées réussis.\n\n"
        "Impressions minimales **synthétiques**; sans catalogue le verdict reste unknown. "
        "Ce résultat ne vérifie ni la base du PC, ni les identités TCGdex, ni les PDF, "
        "ni les listes/résultats compétitifs.\n\n"
        "Les empreintes des registres PUBLIC et décisions sont dans le log "
        "`rules_registry_evidence` de ce job au SHA testé.\n"
        "\n## Listes compétitives : chaîne synthétique\n\n"
        "Une page et un index entièrement synthétiques → SQLite PUBLIC neuve → "
        "liste 60 cartes → réimport idempotent → export hors ligne en lecture seule. "
        "Intégrité/FK vérifiés. Aucune liste réelle ou donnée du PC copiée dans la CI. "
        "Voir `competitive_pages_evidence`; le cache PUBLIC réel reste rapporté localement.\n"
        "\n## Comparateur PUBLIC hors ligne : preuve synthétique\n\n"
        "6 placements inventés → 4 compositions distinctes → comparaison 59 copies "
        "partagées / 1 retirée / 1 ajoutée → 4 options de familles différentes. "
        "Cache inchangé, réseau/client/écriture interdits pendant le test et "
        "inconnues préservées. `competitive_advisor_evidence` ne certifie pas le PC.\n"
        "\n## Prévol PUBLIC : preuve synthétique\n\n"
        "Quatre options inventées de 60 cartes, catalogue et règles dans une seconde base PUBLIC. "
        "Règles inventées : 4 decks legal en présentiel, 4 unknown sur Live; réimpression et errata "
        "contrôlés, caches inchangés et réseau interdit. Aucune impression réelle ni disponibilité "
        "Live certifiée. Voir `public_deck_preflight_evidence`.\n"
        "\n## Deck Knowledge PUBLIC : preuve synthétique\n\n"
        "Quatre fiches et exports inventés60/60; pont optionnel sourcé, noms non devinés, "
        "alias ambigus bloqués, faits/hypothèses séparés et inconnus Live/matchups conservés. "
        "Caches inchangés, réseau interdit; `deck_knowledge_evidence` ne certifie aucune liste du PC.\n"
        "\n## Bibliothèque / Observer / Matchups : scénario inventé\n\n"
        "4 compositions / 6 placements PUBLIC synthétiques, exports60 et cinq matchs fictifs. "
        "v1 contre hypothèse adverse : 2 défaites / n2 et 1 issue inconnue; v2 : 1 victoire, "
        "1 match sans version attestée séparé. Pioches cachées exclues, proxy distinct d'un deck exact, "
        "doublons/versions contrôlés et caches inchangés. Aucun journal réel ouvert; "
        "`deck_library_matchup_evidence` ne certifie aucune partie ou base du PC.\n"
        "\n## Counter-Deck / Learning Loop : expérience inventée\n\n"
        "4 options PUBLIC artificielles60/60, 6 matchs retenus, 1 doublon probable exclu, "
        "2 versions fictives, révision/retrait/réouverture/rejet sans écraser les faits. "
        "Petits effectifs et aucun progrès causal démontré. `counter_learning_evidence` "
        "ne certifie aucun contre, journal personnel ou cache PUBLIC du PC.\n"
        "\n## Revue volontaire : scénario inventé\n\n"
        "Lecture, import et attestation séparés, dry-run sans mutation, reprise idempotente, "
        "versions/révocations et quatre exports60. `selected_match_review_evidence` "
        "ne certifie aucune vraie partie. Les empreintes canoniques JSON complètent "
        "les octets du checkout, sans revalidation des sites officiels.\n"
    )
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(f"ci_evidence=TECHNICAL_TESTS_GREEN os={platform.system()} passed={passed} skipped={counts['skipped']} sha={sha}")
    print("competitive_pages_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **competitive}, sort_keys=True))
    print("competitive_advisor_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **advisor}, sort_keys=True))
    print("public_deck_preflight_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **preflight}, sort_keys=True))
    print("deck_knowledge_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **knowledge}, sort_keys=True))
    print("deck_library_matchup_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **library_matchup}, sort_keys=True))
    print("counter_learning_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **counter_learning}, sort_keys=True))
    print("selected_match_review_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **selected_review}, sort_keys=True))
    print("rules_registry_evidence=" + json.dumps({"sha": sha, "run_id": run_id, **rules}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
