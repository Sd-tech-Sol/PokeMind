"""Interface de ligne de commande locale de PokeMind."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Sequence

from pokemind import __version__
from pokemind.analysis import analyze_deck
from pokemind.attestations import (
    confirm_battle_version,
    list_link_candidates,
    revoke_battle_version,
)
from pokemind.battle_logs import MAX_LOG_BYTES, decode_log_bytes, import_battle_log, read_clipboard
from pokemind.cards import (
    card_reprints,
    cards_coverage,
    resolve_deck_cards,
    search_cards,
    show_card,
    sync_cards,
)
from pokemind.candidates import create_candidate, export_candidate, show_candidate
from pokemind.capabilities import capability_status
from pokemind.collection import (
    collection_coverage,
    collection_missing,
    collection_status,
    credits_status,
    import_collection,
    rollback_collection,
    rollback_credits,
    set_credits,
)
from pokemind.database import database_status, import_seed
from pokemind.deck_exports import (
    PreparedDeck,
    copy_ready_file,
    copy_text_to_clipboard,
    export_confirmed_deck,
    prepare_proposal,
)
from pokemind.decks import MAX_DECK_BYTES, decode_deck_bytes, import_deck, show_deck
from pokemind.paths import default_db_path, find_project_root
from pokemind.profiles import profile_review, profile_summary
from pokemind.meta import (
    meta_archetypes,
    meta_coverage,
    meta_matchups,
    meta_status,
    meta_tournaments,
    sync_meta,
)
from pokemind.knowledge import knowledge_audit, knowledge_status
from pokemind.lessons import battle_lessons, save_battle_note
from pokemind.recommendations import recommend_deck
from pokemind.readiness import v1_readiness
from pokemind.recovery import (
    _redirected,
    apply_retention,
    backup_plan,
    backup_status,
    create_backup,
    restore_backup,
    restore_plan,
    restore_verify,
    retention_plan,
    verify_backup,
)
from pokemind.rules import (
    check_card as check_card_legality,
    check_deck as check_deck_legality,
    default_registry_path,
    load_official_registry,
    rules_sources,
    rules_status,
)
from pokemind.search import search_database
from pokemind.scheduler import scheduler_preview, cadence_preview
from pokemind.ocr_benchmark import benchmark_ocr
from pokemind.vision_evidence import review_observation, revoke_visual_review
from pokemind.official_reviews import record_official_review
from pokemind.commissioning import commissioning_preflight, STEPS
from pokemind.security import public_error
from pokemind.updates import run_public_update, update_status
from pokemind.version_evidence import compare_deck_versions, version_evidence
from pokemind.visual_coach import (
    advise_turn,
    close_session,
    correct_observation,
    observe_training,
    revoke_correction,
    session_memory,
    start_session,
    vision_backend_status,
)


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="produire du JSON UTF-8")
    parser.add_argument("--db", type=Path, help="chemin explicite de la base SQLite")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pokemind",
        description="Cerveau local sourcé pour Pokémon TCG Live.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="parcours synthétique hors ligne dans un espace temporaire; aucune base personnelle")
    demo.add_argument("--json", action="store_true")
    runtime = subparsers.add_parser("preflight", help="vérifier Python/SQLite FTS5 en mémoire, sans ouvrir une base personnelle")
    runtime.add_argument("--json", action="store_true")
    owner_plan = subparsers.add_parser("owner-plan", help="prévol propriétaire en lecture seule, sans exécuter ni autoriser un acte")
    owner_plan.add_argument("--step", required=True, choices=STEPS)
    owner_plan.add_argument("--backup", type=Path)
    owner_plan.add_argument("--clone", type=Path)
    _common_options(owner_plan)

    import_parser = subparsers.add_parser(
        "import-seed", help="importer idempotemment les quatre volumes Markdown"
    )
    _common_options(import_parser)

    search_parser = subparsers.add_parser("search", help="chercher dans la bibliothèque locale")
    search_parser.add_argument("query", help="mots ou expression à chercher")
    search_parser.add_argument("--limit", type=int, default=5, help="nombre maximal de résultats (1-100)")
    _common_options(search_parser)

    status_parser = subparsers.add_parser("status", help="diagnostiquer la base et la fraîcheur")
    _common_options(status_parser)

    v1_parser = subparsers.add_parser("v1", help="rapporter la disponibilité V1 sans donnée privée")
    v1_commands = v1_parser.add_subparsers(dest="v1_command", required=True)
    v1_readiness_parser = v1_commands.add_parser("readiness", help="agréger runtime, vision, données et reprise")
    v1_readiness_parser.add_argument("--backup-directory", type=Path)
    _common_options(v1_readiness_parser)

    backup_parser = subparsers.add_parser(
        "backup", help="planifier et vérifier des sauvegardes SQLite privées"
    )
    backup_commands = backup_parser.add_subparsers(dest="backup_command", required=True)
    for name, help_text in (
        ("plan", "vérifier source, destination et disque sans écrire"),
        ("create", "créer une sauvegarde cohérente après confirmation"),
        ("status", "inventorier les sauvegardes sans les modifier"),
    ):
        command = backup_commands.add_parser(name, help=help_text)
        command.add_argument("--destination", type=Path)
        if name == "create":
            command.add_argument("--apply", action="store_true")
            command.add_argument("--confirm-owner", action="store_true")
        command.add_argument("--min-free-bytes", type=int, default=64 * 1024 * 1024)
        _common_options(command)
    backup_verify = backup_commands.add_parser("verify", help="vérifier checksum et SQLite sans écrire")
    backup_verify.add_argument("--backup", type=Path, required=True)
    _common_options(backup_verify)
    backup_retention = backup_commands.add_parser(
        "retention", help="prévisualiser, puis appliquer explicitement une rétention bornée"
    )
    backup_retention.add_argument("--destination", type=Path)
    backup_retention.add_argument("--keep-last", type=int, default=7)
    backup_retention.add_argument("--max-age-days", type=int, default=90)
    backup_retention.add_argument("--max-total-bytes", type=int, default=20 * 1024 * 1024 * 1024)
    backup_retention.add_argument("--work-max-age-days", type=int, default=7)
    backup_retention.add_argument("--log-max-age-days", type=int, default=30)
    backup_retention.add_argument("--plan-sha256")
    backup_retention.add_argument("--apply", action="store_true")
    backup_retention.add_argument("--confirm-owner", action="store_true")
    _common_options(backup_retention)

    restore_parser = subparsers.add_parser(
        "restore", help="vérifier ou restaurer atomiquement une sauvegarde SQLite"
    )
    restore_commands = restore_parser.add_subparsers(dest="restore_command", required=True)
    for name, help_text in (
        ("plan", "prévisualiser une restauration sans toucher la cible"),
        ("verify", "restaurer dans un clone temporaire puis le vérifier"),
        ("apply", "remplacer une cible synthétique/privée après confirmation"),
    ):
        command = restore_commands.add_parser(name, help=help_text)
        command.add_argument("--backup", type=Path, required=True)
        command.add_argument("--migrate-clone", action="store_true")
        command.add_argument("--min-free-bytes", type=int, default=64 * 1024 * 1024)
        if name == "apply":
            command.add_argument("--apply", action="store_true")
            command.add_argument("--confirm-owner", action="store_true")
        _common_options(command)

    knowledge_parser = subparsers.add_parser(
        "knowledge", help="auditer les connaissances publiques hors ligne"
    )
    knowledge_commands = knowledge_parser.add_subparsers(
        dest="knowledge_command", required=True
    )
    for name, help_text in (
        ("status", "mesurer cartes, règles, méta et actions prioritaires"),
        ("audit", "vérifier cohérence, index et acceptation A1-A5"),
    ):
        knowledge_command = knowledge_commands.add_parser(name, help=help_text)
        _common_options(knowledge_command)
    knowledge_update = knowledge_commands.add_parser(
        "update", help="planifier, exécuter ou diagnostiquer l'actualisation publique"
    )
    knowledge_update.add_argument("update_action", nargs="?", choices=("status",))
    knowledge_update.add_argument("--mode", choices=("daily", "deep", "auto"), default="daily")
    update_mode = knowledge_update.add_mutually_exclusive_group()
    update_mode.add_argument("--dry-run", action="store_true", help="planifier sans réseau ni écriture (défaut)")
    update_mode.add_argument("--apply", action="store_true", help="actualiser uniquement les caches publics")
    knowledge_update.add_argument("--confirm-owner", action="store_true", help="confirmer l'écriture locale publique")
    knowledge_update.add_argument("--public-only", action="store_true",
                                  help="exiger une base PUBLIC marquée distincte de la base personnelle")
    knowledge_update.add_argument(
        "--probe-public-network", action="store_true",
        help="sonder une source publique bornée sans écriture; distinct du dry-run normal",
    )
    knowledge_update.add_argument(
        "--deep-time", metavar="HH:MM", help="heure locale Toronto configurable pour mardi/vendredi"
    )
    knowledge_update.add_argument("--tcgdex-budget", type=int)
    knowledge_update.add_argument("--official-budget", type=int)
    knowledge_update.add_argument("--limitless-budget", type=int)
    _common_options(knowledge_update)
    knowledge_scheduler = knowledge_commands.add_parser(
        "scheduler", help="prévisualiser le planificateur Windows sans l'installer"
    )
    knowledge_scheduler.add_argument(
        "--action", choices=("preview", "install", "uninstall", "status"), default="preview"
    )
    knowledge_scheduler.add_argument("--daily-time", metavar="HH:MM")
    knowledge_scheduler.add_argument("--deep-time", metavar="HH:MM")
    knowledge_scheduler.add_argument(
        "--windows-timezone",
        help="sortie exacte de tzutil /g; permet une simulation explicite hors Windows",
    )
    knowledge_scheduler.add_argument("--dry-run", action="store_true")
    knowledge_scheduler.add_argument("--confirm-owner", action="store_true")
    _common_options(knowledge_scheduler)
    cadence = knowledge_commands.add_parser("cadence", help="simuler les échéances Toronto sans contacter le planificateur")
    cadence.add_argument("--start-utc", required=True)
    cadence.add_argument("--daily-time", required=True)
    cadence.add_argument("--deep-time", required=True)
    cadence.add_argument("--days", type=int, default=14)
    _common_options(cadence)
    official_review = knowledge_commands.add_parser("review-official", help="enregistrer une revue complète sans promouvoir les assertions normatives")
    official_review.add_argument("--source", required=True)
    official_review.add_argument("--content-sha256", required=True)
    official_review.add_argument("--document-version", required=True)
    official_review.add_argument("--decision", required=True, choices=("verified", "non_verified", "conflict"))
    official_review.add_argument("--full-document-reviewed", action="store_true")
    official_review.add_argument("--apply", action="store_true")
    official_review.add_argument("--confirm-owner", action="store_true")
    _common_options(official_review)

    capability_parser = subparsers.add_parser("capability", help="auditer les parcours personnels hors ligne")
    capability_commands = capability_parser.add_subparsers(dest="capability_command", required=True)
    capability_status_parser = capability_commands.add_parser("status", help="afficher objets, lacunes et dates sans valeurs privées")
    _common_options(capability_status_parser)

    cards_parser = subparsers.add_parser("cards", help="synchroniser et consulter le catalogue TCGdex")
    cards_commands = cards_parser.add_subparsers(dest="cards_command", required=True)
    cards_sync = cards_commands.add_parser("sync", help="synchroniser une tranche bornée du catalogue")
    cards_sync.add_argument("--dry-run", action="store_true", help="afficher le plan sans réseau ni écriture")
    cards_sync.add_argument("--lang", default="en,fr", help="langues séparées par une virgule: en,fr")
    cards_sync.add_argument("--max-requests", type=int, default=10, help="budget strict de requêtes HTTP (1-1000)")
    cards_sync.add_argument(
        "--phase", choices=("index", "details", "balanced"), default="balanced",
        help="faire progresser les index, les détails, ou les deux",
    )
    cards_sync.add_argument(
        "--refresh-index", action="store_true",
        help="rafraîchir manuellement les index avec un curseur distinct",
    )
    cards_sync.add_argument(
        "--recheck-absent", action="store_true",
        help="recontrôler explicitement les détails auparavant absents",
    )
    cards_sync.add_argument(
        "--prioritize-deck", metavar="DECK",
        help="prioriser localement les identités déjà prouvées d'un deck confirmé",
    )
    _common_options(cards_sync)
    cards_search = cards_commands.add_parser("search", help="chercher hors ligne dans les cartes locales")
    cards_search.add_argument("query", help="nom ou texte à chercher")
    cards_search.add_argument("--lang", default="fr", choices=("en", "fr", "all"))
    cards_search.add_argument("--limit", type=int, default=20, help="nombre maximal de résultats (1-100)")
    _common_options(cards_search)
    cards_show = cards_commands.add_parser("show", help="afficher une impression TCGdex locale")
    cards_show.add_argument("tcgdex_id", help="identifiant stable d'impression TCGdex")
    cards_show.add_argument("--lang", default="fr", choices=("en", "fr"))
    _common_options(cards_show)
    cards_reprints = cards_commands.add_parser(
        "reprints", help="lister les équivalences de réimpression officiellement prouvées"
    )
    cards_reprints.add_argument("tcgdex_id", help="identifiant stable d'impression TCGdex")
    cards_reprints.add_argument("--as-of", help="date optionnelle YYYY-MM-DD")
    _common_options(cards_reprints)
    cards_coverage_parser = cards_commands.add_parser("coverage", help="mesurer la couverture locale")
    _common_options(cards_coverage_parser)
    cards_resolve = cards_commands.add_parser(
        "resolve-deck", help="diagnostiquer sans écriture les identités d'un deck local"
    )
    cards_resolve.add_argument("deck", help="identifiant du deck exact")
    _common_options(cards_resolve)

    rules_parser = subparsers.add_parser("rules", help="consulter les règles officielles datées")
    rules_commands = rules_parser.add_subparsers(dest="rules_command", required=True)
    rules_load = rules_commands.add_parser("load-official", help="charger le registre versionné sans réseau")
    rules_load.add_argument("--registry", type=Path, help="registre JSON explicite")
    _common_options(rules_load)
    rules_sources_parser = rules_commands.add_parser("sources", help="lister les sources officielles locales")
    _common_options(rules_sources_parser)
    rules_status_parser = rules_commands.add_parser("status", help="afficher la couverture normative")
    _common_options(rules_status_parser)
    rules_card = rules_commands.add_parser("check-card", help="vérifier une impression TCGdex locale")
    rules_card.add_argument("tcgdex_id")
    rules_card.add_argument("--format", required=True, choices=("standard", "expanded"))
    rules_card.add_argument("--platform", required=True, choices=("live", "in_person"))
    rules_card.add_argument("--as-of", required=True, help="date YYYY-MM-DD")
    _common_options(rules_card)
    rules_deck = rules_commands.add_parser("check-deck", help="vérifier la dernière version exacte d'un deck")
    rules_deck.add_argument("deck")
    rules_deck.add_argument("--format", required=True, choices=("standard", "expanded"))
    rules_deck.add_argument("--platform", required=True, choices=("live", "in_person"))
    rules_deck.add_argument("--as-of", required=True, help="date YYYY-MM-DD")
    _common_options(rules_deck)

    meta_parser = subparsers.add_parser("meta", help="synchroniser et consulter la méta Limitless")
    meta_commands = meta_parser.add_subparsers(dest="meta_command", required=True)
    meta_sync = meta_commands.add_parser("sync", help="synchroniser une petite tranche publique")
    meta_sync.add_argument("--dry-run", action="store_true", help="planifier sans réseau ni écriture")
    meta_sync.add_argument("--max-requests", type=int, default=8, help="budget strict de GET (1-100)")
    meta_sync.add_argument("--max-tournaments", type=int, default=2, help="maximum de tournois (1-20)")
    meta_sync.add_argument(
        "--mode", choices=("discover", "refresh"), default="discover",
        help="découvrir de nouveaux tournois ou rafraîchir explicitement les snapshots existants",
    )
    meta_sync.add_argument("--format", default="standard", help="format Limitless, par défaut standard")
    meta_sync.add_argument("--platform", default="PTCGL", help="plateforme Limitless, par défaut PTCGL")
    meta_sync.add_argument("--online", choices=("true", "false"), default="true")
    _common_options(meta_sync)
    meta_tournaments_parser = meta_commands.add_parser("tournaments", help="lister les instantanés hors ligne")
    meta_archetypes_parser = meta_commands.add_parser("archetypes", help="agréger les archétypes publiés")
    meta_matchups_parser = meta_commands.add_parser("matchups", help="agréger les matchs classifiables")
    meta_matchups_parser.add_argument("--archetype", required=True, help="ID public d'archétype Limitless")
    meta_matchups_parser.add_argument("--min-sample", type=int, default=5)
    meta_coverage_parser = meta_commands.add_parser(
        "coverage", help="mesurer la couverture d'un contexte compétitif"
    )
    for meta_query in (
        meta_tournaments_parser, meta_archetypes_parser,
        meta_matchups_parser, meta_coverage_parser,
    ):
        meta_query.add_argument("--format", default="standard")
        meta_query.add_argument("--platform", default="PTCGL")
        meta_query.add_argument("--online", choices=("true", "false"), default="true")
        meta_query.add_argument("--since", help="date minimale YYYY-MM-DD")
        _common_options(meta_query)
    meta_status_parser = meta_commands.add_parser("status", help="diagnostiquer le cache Limitless hors ligne")
    _common_options(meta_status_parser)
    competitive_summary_parser = meta_commands.add_parser("competitive-summary", help="consulter les listes publiques de tournois hors ligne")
    _common_options(competitive_summary_parser)
    competitive_export_parser = meta_commands.add_parser("competitive-export", help="exporter une liste publique publiée au format TCG Live")
    competitive_export_parser.add_argument("--event", required=True)
    competitive_export_parser.add_argument("--placement", required=True, type=int)
    _common_options(competitive_export_parser)
    advisor_inventory = meta_commands.add_parser("competitive-inventory", help="inventorier les compositions PUBLIC distinctes hors ligne")
    advisor_compare = meta_commands.add_parser("competitive-compare", help="comparer deux listes PUBLIC 60/60 hors ligne")
    advisor_compare.add_argument("--left", required=True, help="référence événement:placement, ex. 581:1")
    advisor_compare.add_argument("--right", required=True, help="référence événement:placement, ex. 582:1")
    advisor_compare.add_argument("--limit", type=int, default=12, help="identités affichées par groupe, 1–60; totaux toujours complets")
    advisor_shortlist = meta_commands.add_parser("competitive-shortlist", help="proposer 2–4 plans PUBLIC différents sans classement de force")
    advisor_shortlist.add_argument("--options", type=int, default=4)
    advisor_shortlist.add_argument("--base", help="référence Dragapult événement:placement; sinon représentant descriptif")
    for advisor_parser in (advisor_inventory, advisor_compare, advisor_shortlist):
        advisor_parser.add_argument("--as-of", required=True, help="date de consultation YYYY-MM-DD, sans certifier la compatibilité à date")
        _common_options(advisor_parser)

    public_preflight = meta_commands.add_parser("competitive-preflight", help="vérifier les preuves de légalité des options PUBLIC hors ligne")
    public_preflight.add_argument("--reference-db", type=Path, required=True, help="base catalogue/règles PUBLIC explicite, lue seulement")
    public_preflight.add_argument("--as-of", required=True)
    public_preflight.add_argument("--format", required=True, choices=("standard",))
    public_preflight.add_argument("--platform", required=True, choices=("in_person", "live"))
    public_preflight.add_argument("--select", action="append", help="référence événement:placement; répétable, sinon shortlist 2–4")
    public_preflight.add_argument("--options", type=int, default=4)
    public_preflight.add_argument("--set-aliases", action="store_true", help="pont optionnel depuis métadonnées PUBLIC vérifiées, sans écriture")
    _common_options(public_preflight)

    identity_explain = meta_commands.add_parser(
        "public-identity-explain", help="expliquer les preuves PUBLIC inconnues, sur les deux caches fixes seulement")
    identity_explain.add_argument("--as-of", required=True, help="date YYYY-MM-DD")
    identity_explain.add_argument("--selector", help="composition événement:rang, sinon toutes")
    identity_output = identity_explain.add_mutually_exclusive_group()
    identity_output.add_argument("--json", action="store_true", help="rapport JSON UTF-8")
    identity_output.add_argument("--html", action="store_true", help="document HTML autonome UTF-8 sur stdout")

    deck_knowledge = meta_commands.add_parser("deck-knowledge", help="fiche PUBLIC sourcée et export60, hors ligne")
    deck_knowledge.add_argument("--selector", required=True, help="événement:placement PUBLIC")
    deck_knowledge.add_argument("--reference-db", type=Path, required=True)
    deck_knowledge.add_argument("--as-of", required=True)
    deck_knowledge.add_argument("--set-aliases", action="store_true")
    _common_options(deck_knowledge)

    deck_library = meta_commands.add_parser("deck-library", help="chercher les compositions PUBLIC déjà en cache")
    deck_library.add_argument("--as-of", required=True)
    deck_library.add_argument("--archetype")
    deck_library.add_argument("--event")
    deck_library.add_argument("--since")
    deck_library.add_argument("--until")
    deck_library.add_argument("--version", help="empreinte complète de composition PUBLIC")
    _common_options(deck_library)

    for name in ("counter-plan", "learning-simulate"):
        counter = meta_commands.add_parser(name, help="plan PUBLIC ou cycle entièrement fictif, hors ligne")
        counter.add_argument("--as-of", required=True)
        counter.add_argument("--target", required=True, help="archétype adverse hypothétique")
        counter.add_argument("--reference-db", type=Path, required=True, help="catalogue PUBLIC explicite")
        counter.add_argument("--base", help="sélecteur PUBLIC Dragapult événement:placement")
        counter.add_argument("--set-aliases", action="store_true")
        if name == "counter-plan":
            counter.add_argument("--options", type=int, default=4)
        _common_options(counter)

    analyze_parser = subparsers.add_parser("analyze", help="composer un diagnostic personnel hors ligne")
    analyze_commands = analyze_parser.add_subparsers(dest="analyze_command", required=True)
    analyze_deck_parser = analyze_commands.add_parser("deck", help="diagnostiquer un deck local sans écriture")
    analyze_deck_parser.add_argument("deck", help="identifiant local explicitement choisi")
    analyze_deck_parser.add_argument("--as-of", required=True, help="date stricte YYYY-MM-DD")
    analyze_deck_parser.add_argument("--format", default="standard", choices=("standard", "expanded"))
    analyze_deck_parser.add_argument("--platform", default="live", choices=("live", "in_person"))
    _common_options(analyze_deck_parser)

    recommend_parser = subparsers.add_parser("recommend", help="produire des conseils conditionnels sourcés")
    recommend_commands = recommend_parser.add_subparsers(dest="recommend_command", required=True)
    recommend_deck_parser = recommend_commands.add_parser("deck", help="conseiller sans modifier un deck local")
    recommend_deck_parser.add_argument("deck")
    recommend_deck_parser.add_argument("--as-of", required=True)
    recommend_deck_parser.add_argument("--format", default="standard", choices=("standard", "expanded"))
    recommend_deck_parser.add_argument("--platform", default="live", choices=("live", "in_person"))
    recommend_deck_parser.add_argument("--collection", action="store_true", help="consulter la collection volontaire active")
    _common_options(recommend_deck_parser)

    subparsers.add_parser("desktop", help="ouvrir l'application Windows PokeMind et son chatbot")
    battle_parser = subparsers.add_parser("battle", help="consulter ou valider des leçons de combats")
    battle_commands = battle_parser.add_subparsers(dest="battle_command", required=True)
    coach_parser = battle_commands.add_parser("coach", help="afficher vos conseils locaux; --update intègre les nouveaux journaux hors ligne")
    coach_parser.add_argument("--player", default=os.environ.get("POKEMIND_PLAYER_NAME"), help="joueur à mémoriser localement au premier lancement")
    coach_parser.add_argument("--update", action="store_true", help="actualiser les matchs et connaissances locales, aucun GET")
    coach_parser.add_argument("--as-of", help="date d'évaluation YYYY-MM-DD; aujourd'hui par défaut")
    coach_parser.add_argument("--json", action="store_true")
    archived = battle_commands.add_parser("batch-report", help="consulter un rapport déjà conservé, sans nouvelle analyse")
    archived.add_argument("--report", type=Path, required=True)
    archived.add_argument("--learning", type=Path, help="journal Learning Loop explicitement choisi, facultatif")
    archived.add_argument("--json", action="store_true")
    legacy = battle_commands.add_parser("legacy-plan", help="diagnostic SQLite lecture seule, aucune migration")
    legacy.add_argument("--db", type=Path, required=True)
    legacy.add_argument("--json", action="store_true")
    batch = battle_commands.add_parser("batch-intelligence", help="analyser le dossier de journaux explicitement autorisé, mémoire locale")
    batch.add_argument("--folder", type=Path, default=os.environ.get("POKEMIND_BATTLE_LOGS_DIR"))
    batch.add_argument("--player", default=os.environ.get("POKEMIND_PLAYER_NAME"))
    batch.add_argument("--db", type=Path, required=True)
    batch.add_argument("--as-of", required=True)
    batch.add_argument("--apply", action="store_true", help="import compatible et mémoire dérivée locale sans migration")
    batch.add_argument("--no-recommendations", action="store_true", help="bilan des événements seulement")
    batch.add_argument("--refresh-public", action="store_true", help="actualisation PUBLIC distincte et bornée")
    batch.add_argument("--json", action="store_true")
    selected = battle_commands.add_parser("review-selected", help="revoir une partie choisie, consentements lecture/import/attestation séparés")
    source = selected.add_mutually_exclusive_group(required=True)
    source.add_argument("--log-file", type=Path)
    source.add_argument("--battle-id", type=int)
    selected.add_argument("--db", type=Path, required=True)
    selected.add_argument("--deck", required=True)
    selected.add_argument("--as-of", required=True)
    mode = selected.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    selected.add_argument("--confirm-owner-read", action="store_true")
    selected.add_argument("--confirm-owner-import", action="store_true")
    selected.add_argument("--confirm-owner-attest", action="store_true")
    selected.add_argument("--version", type=int)
    selected.add_argument("--battle-date")
    selected.add_argument("--revoke-version", action="store_true")
    selected.add_argument("--reason")
    selected.add_argument("--learning-out", type=Path, help="JSON local explicitement choisi, sans écrasement")
    selected.add_argument("--public-db", type=Path)
    selected.add_argument("--reference-db", type=Path)
    selected.add_argument("--set-aliases", action="store_true")
    selected.add_argument("--json", action="store_true")
    opponent_parser = battle_commands.add_parser("opponent", help="observer un combat explicitement sélectionné, lecture opt-in")
    opponent_parser.add_argument("--battle-id", type=int, required=True)
    matchup_parser = battle_commands.add_parser("matchups", help="bilan par version attestée et hypothèse adverse, lecture opt-in")
    matchup_parser.add_argument("--deck", required=True)
    matchup_parser.add_argument("--since")
    matchup_parser.add_argument("--until")
    for analysis_parser in (opponent_parser, matchup_parser):
        analysis_parser.add_argument("--as-of", required=True)
        analysis_parser.add_argument("--public-db", type=Path, help="cache de listes PUBLIC optionnel pour les proxies")
        analysis_parser.add_argument("--reference-db", type=Path, help="catalogue PUBLIC optionnel pour les noms FR/EN")
        analysis_parser.add_argument("--confirm-owner-read", action="store_true", help="autoriser uniquement la lecture des données explicitement choisies")
        _common_options(analysis_parser)
    battle_lessons_parser = battle_commands.add_parser("lessons", help="résumer faits, hypothèses et questions")
    battle_lessons_parser.add_argument("--deck", required=True)
    battle_lessons_parser.add_argument("--as-of", required=True)
    _common_options(battle_lessons_parser)
    battle_note = battle_commands.add_parser("note", help="prévisualiser ou conserver une note propriétaire")
    battle_note.add_argument("--deck", required=True)
    battle_note.add_argument("--battle-id", required=True, type=int)
    battle_note.add_argument("--text", required=True)
    battle_note.add_argument("--confidence", default="unknown", choices=("high", "medium", "low", "unknown"))
    battle_note.add_argument("--kind", default="owner_note", choices=("owner_note", "validated_fact"))
    battle_note.add_argument("--source-url")
    battle_note.add_argument("--source-date")
    battle_note_mode = battle_note.add_mutually_exclusive_group()
    battle_note_mode.add_argument("--dry-run", action="store_true")
    battle_note_mode.add_argument("--apply", action="store_true")
    battle_note.add_argument("--confirm-owner", action="store_true")
    _common_options(battle_note)

    collection_parser = subparsers.add_parser(
        "collection", help="gérer les déclarations locales de collection"
    )
    collection_commands = collection_parser.add_subparsers(dest="collection_command", required=True)
    collection_import = collection_commands.add_parser("import", help="prévisualiser ou importer un JSON propriétaire")
    collection_import.add_argument("--path", required=True, type=Path)
    collection_import_mode = collection_import.add_mutually_exclusive_group()
    collection_import_mode.add_argument("--dry-run", action="store_true", help="prévisualiser sans écriture (défaut)")
    collection_import_mode.add_argument("--apply", action="store_true", help="appliquer un nouvel instantané")
    collection_import.add_argument("--confirm-owner", action="store_true", help="confirmer la déclaration propriétaire")
    _common_options(collection_import)
    for name, help_text in (
        ("status", "afficher l'instantané actif et l'historique"),
        ("coverage", "mesurer la résolution des impressions"),
    ):
        command = collection_commands.add_parser(name, help=help_text)
        command.add_argument("--as-of", help="état historiquement disponible à cette date YYYY-MM-DD")
        _common_options(command)
    collection_missing_parser = collection_commands.add_parser(
        "missing", help="comparer un deck exact à la collection déclarée"
    )
    collection_missing_parser.add_argument("--deck", required=True)
    collection_missing_parser.add_argument("--as-of", help="état historiquement disponible à cette date YYYY-MM-DD")
    _common_options(collection_missing_parser)
    collection_rollback = collection_commands.add_parser(
        "rollback", help="prévisualiser ou restaurer un instantané historique"
    )
    collection_rollback.add_argument("--snapshot", required=True, type=int)
    collection_rollback_mode = collection_rollback.add_mutually_exclusive_group()
    collection_rollback_mode.add_argument("--dry-run", action="store_true")
    collection_rollback_mode.add_argument("--apply", action="store_true")
    collection_rollback.add_argument("--confirm-owner", action="store_true")
    _common_options(collection_rollback)

    credits_parser = subparsers.add_parser("credits", help="gérer les crédits déclarés localement")
    credits_commands = credits_parser.add_subparsers(dest="credits_command", required=True)
    credits_set = credits_commands.add_parser("set", help="prévisualiser ou enregistrer un montant déclaré")
    credits_set.add_argument("--amount", required=True, type=int)
    credits_set.add_argument("--as-of", required=True, help="date YYYY-MM-DD")
    credits_set_mode = credits_set.add_mutually_exclusive_group()
    credits_set_mode.add_argument("--dry-run", action="store_true")
    credits_set_mode.add_argument("--apply", action="store_true")
    credits_set.add_argument("--confirm-owner", action="store_true")
    _common_options(credits_set)
    credits_status_parser = credits_commands.add_parser("status", help="afficher le montant actif et l'historique")
    credits_status_parser.add_argument("--as-of", help="état historiquement disponible à cette date YYYY-MM-DD")
    _common_options(credits_status_parser)
    credits_rollback = credits_commands.add_parser("rollback", help="restaurer un montant historique")
    credits_rollback.add_argument("--snapshot", required=True, type=int)
    credits_rollback_mode = credits_rollback.add_mutually_exclusive_group()
    credits_rollback_mode.add_argument("--dry-run", action="store_true")
    credits_rollback_mode.add_argument("--apply", action="store_true")
    credits_rollback.add_argument("--confirm-owner", action="store_true")
    _common_options(credits_rollback)

    match_parser = subparsers.add_parser("match", help="coacher une partie d'entraînement autorisée")
    match_commands = match_parser.add_subparsers(dest="match_command", required=True)
    match_capabilities = match_commands.add_parser(
        "capabilities", help="inspecter les composants vision locaux sans téléchargement"
    )
    _common_options(match_capabilities)
    preflight = match_commands.add_parser("preflight", help="diagnostiquer un OCR déjà installé, sans installation ni capture")
    _common_options(preflight)
    benchmark = match_commands.add_parser("benchmark-ocr", help="rasteriser un corpus synthétique et tester uniquement un OCR déjà installé")
    _common_options(benchmark)
    for ocr_parser in (preflight, benchmark):
        ocr_parser.add_argument("--ocr-trust", type=Path, help="politique privée de chemins/origine/empreintes revus")
        ocr_parser.add_argument("--execute-reviewed-ocr", action="store_true", help="autoriser séparément l'exécution du moteur revu")
    review = match_commands.add_parser("review", help="attester une observation textuelle précise, sans promouvoir la certitude")
    review.add_argument("--session", required=True)
    review.add_argument("--observation", type=int, required=True)
    review.add_argument("--verdict", choices=("confirmed", "rejected"), required=True)
    review.add_argument("--scope", choices=("synthetic", "owner_training"), required=True)
    review.add_argument("--calibration-sha256", required=True)
    review.add_argument("--apply", action="store_true")
    review.add_argument("--confirm-owner", action="store_true")
    _common_options(review)
    revoke_review = match_commands.add_parser("revoke-review", help="révoquer une attestation visuelle sans effacer son historique")
    revoke_review.add_argument("--review", required=True)
    revoke_review.add_argument("--apply", action="store_true")
    revoke_review.add_argument("--confirm-owner", action="store_true")
    _common_options(revoke_review)
    match_start = match_commands.add_parser("start", help="prévisualiser ou ouvrir une séance textuelle")
    match_start.add_argument("--format", default="standard", choices=("standard", "expanded"))
    match_start.add_argument("--platform", default="live", choices=("live",))
    match_start.add_argument("--as-of", required=True)
    match_start_mode = match_start.add_mutually_exclusive_group()
    match_start_mode.add_argument("--dry-run", action="store_true")
    match_start_mode.add_argument("--apply", action="store_true")
    match_start.add_argument("--confirm-owner", action="store_true")
    _common_options(match_start)
    match_observe = match_commands.add_parser("observe", help="lire explicitement une image locale éphémère")
    match_observe.add_argument("--image", type=Path)
    match_observe.add_argument("--annotation", type=Path, help="annotation JSON locale réconciliée")
    match_observe.add_argument("--calibration", type=Path, help="profil local explicite pour l'adaptateur PNG")
    match_observe.add_argument("--ocr-trust", type=Path)
    match_observe.add_argument("--execute-reviewed-ocr", action="store_true")
    match_observe.add_argument("--session")
    match_observe.add_argument("--turn", type=int, required=True)
    match_observe.add_argument("--mode", default="training", choices=("training",))
    match_observe.add_argument("--frame-scope", default="unknown", choices=("full_board", "crop", "unknown"))
    match_observe_mode = match_observe.add_mutually_exclusive_group()
    match_observe_mode.add_argument("--dry-run", action="store_true")
    match_observe_mode.add_argument("--apply", action="store_true")
    match_observe.add_argument("--confirm-owner", action="store_true")
    _common_options(match_observe)
    match_show = match_commands.add_parser("show", help="relire la mémoire textuelle d'une séance")
    match_show.add_argument("--session", required=True)
    _common_options(match_show)
    match_correct = match_commands.add_parser("correct", help="réviser une observation sans effacer l'historique")
    match_correct.add_argument("--session", required=True)
    match_correct.add_argument("--observation", required=True, type=int)
    match_correct.add_argument("--annotation", required=True, type=Path)
    match_correct_mode = match_correct.add_mutually_exclusive_group()
    match_correct_mode.add_argument("--dry-run", action="store_true")
    match_correct_mode.add_argument("--apply", action="store_true")
    match_correct.add_argument("--confirm-owner", action="store_true")
    _common_options(match_correct)
    match_revoke = match_commands.add_parser("revoke-correction", help="révoquer une correction et restaurer sa version précédente")
    match_revoke.add_argument("--session", required=True)
    match_revoke.add_argument("--observation", required=True, type=int)
    match_revoke_mode = match_revoke.add_mutually_exclusive_group()
    match_revoke_mode.add_argument("--dry-run", action="store_true")
    match_revoke_mode.add_argument("--apply", action="store_true")
    match_revoke.add_argument("--confirm-owner", action="store_true")
    _common_options(match_revoke)
    match_advise = match_commands.add_parser("advise", help="obtenir un conseil conditionnel pour un tour observé")
    match_advise.add_argument("--session", required=True)
    match_advise.add_argument("--turn", required=True, type=int)
    match_advise.add_argument("--format", default="standard", choices=("standard", "expanded"))
    match_advise.add_argument("--platform", default="live", choices=("live",))
    match_advise.add_argument("--as-of", required=True)
    _common_options(match_advise)
    match_close = match_commands.add_parser("close", help="clore volontairement une séance")
    match_close.add_argument("--session", required=True)
    match_close_mode = match_close.add_mutually_exclusive_group()
    match_close_mode.add_argument("--dry-run", action="store_true")
    match_close_mode.add_argument("--apply", action="store_true")
    match_close.add_argument("--confirm-owner", action="store_true")
    _common_options(match_close)

    log_parser = subparsers.add_parser("log", help="importer des journaux de combat locaux")
    log_commands = log_parser.add_subparsers(dest="log_command", required=True)
    log_import = log_commands.add_parser("import", help="importer un journal texte")
    log_import.add_argument("path", nargs="?", help="fichier local, ou '-' pour stdin")
    log_import.add_argument("--clipboard", action="store_true", help="lire explicitement le presse-papiers Windows")
    log_import.add_argument("--deck", help="identifiant local du deck observé")
    log_import.add_argument(
        "--reparse", action="store_true",
        help="remplacer transactionnellement l'analyse du même journal sans changer son deck",
    )
    _common_options(log_import)

    profile_parser = subparsers.add_parser("profile", help="résumer les observations cumulées")
    profile_commands = profile_parser.add_subparsers(dest="profile_command", required=True)
    for name, help_text in (
        ("summary", "produire le profil cumulatif"),
        ("review", "produire un rapport analysable avec preuves"),
    ):
        profile_command = profile_commands.add_parser(name, help=help_text)
        profile_command.add_argument("--deck", help="limiter à un identifiant local de deck")
        _common_options(profile_command)

    deck_parser = subparsers.add_parser("deck", help="importer et consulter des decks exacts")
    deck_commands = deck_parser.add_subparsers(dest="deck_command", required=True)
    deck_import = deck_commands.add_parser("import", help="importer un export de deck de 60 cartes")
    deck_import.add_argument("path", nargs="?", help="fichier local, ou '-' pour stdin")
    deck_import.add_argument("--clipboard", action="store_true", help="lire explicitement le presse-papiers Windows")
    deck_import.add_argument("--deck", required=True, help="identifiant local du deck")
    _common_options(deck_import)
    deck_show = deck_commands.add_parser("show", help="afficher la dernière version exacte d'un deck")
    deck_show.add_argument("deck", help="identifiant local du deck")
    _common_options(deck_show)
    deck_compare = deck_commands.add_parser(
        "compare", help="comparer deux versions explicites sans écriture"
    )
    deck_compare.add_argument("deck", help="identifiant local du deck")
    deck_compare.add_argument("--from-version", required=True, type=int)
    deck_compare.add_argument("--to-version", required=True, type=int)
    deck_compare.add_argument("--as-of", help="date historique stricte YYYY-MM-DD")
    deck_compare.add_argument(
        "--show-changes",
        action="store_true",
        help="afficher localement les cartes modifiées (données privées)",
    )
    _common_options(deck_compare)
    deck_evidence = deck_commands.add_parser(
        "version-evidence", help="auditer les liens explicites combat-version"
    )
    deck_evidence.add_argument("deck", help="identifiant local du deck")
    deck_evidence.add_argument("--as-of", required=True, help="date stricte YYYY-MM-DD")
    _common_options(deck_evidence)
    deck_candidates = deck_commands.add_parser(
        "link-candidates", help="lister les combats locaux en attente de confirmation"
    )
    deck_candidates.add_argument("--deck", required=True, help="identifiant local du deck")
    _common_options(deck_candidates)
    deck_link = deck_commands.add_parser(
        "link-battle", help="prévisualiser ou confirmer une seule paire combat-version"
    )
    deck_link.add_argument("--deck", required=True, help="identifiant local du deck")
    deck_link.add_argument("--battle-id", required=True, type=int, help="clé SQLite locale")
    deck_link.add_argument("--version", required=True, type=int, help="numéro de version exact")
    deck_link.add_argument(
        "--battle-date", help="date réelle YYYY-MM-DD déclarée volontairement, sinon inconnue"
    )
    link_mode = deck_link.add_mutually_exclusive_group()
    link_mode.add_argument("--dry-run", action="store_true", help="prévisualiser sans écriture (défaut)")
    link_mode.add_argument("--apply", action="store_true", help="appliquer à cette paire seulement")
    deck_link.add_argument(
        "--confirm-owner", action="store_true", help="confirmer explicitement la déclaration propriétaire"
    )
    _common_options(deck_link)
    deck_unlink = deck_commands.add_parser(
        "unlink-battle", help="prévisualiser ou révoquer une attestation propriétaire"
    )
    deck_unlink.add_argument("--deck", required=True, help="identifiant local du deck")
    deck_unlink.add_argument("--battle-id", required=True, type=int, help="clé SQLite locale")
    unlink_mode = deck_unlink.add_mutually_exclusive_group()
    unlink_mode.add_argument("--dry-run", action="store_true", help="prévisualiser sans écriture (défaut)")
    unlink_mode.add_argument("--apply", action="store_true", help="révoquer cette paire seulement")
    deck_unlink.add_argument(
        "--confirm-owner", action="store_true", help="confirmer explicitement la révocation propriétaire"
    )
    _common_options(deck_unlink)
    deck_export = deck_commands.add_parser(
        "export", help="préparer la dernière version exacte pour l'import dans TCG Live"
    )
    deck_export.add_argument("deck", help="identifiant local du deck")
    deck_export.add_argument(
        "--copy", action="store_true", help="copier explicitement le texte importable dans le presse-papiers"
    )
    _common_options(deck_export)
    deck_prepare = deck_commands.add_parser(
        "prepare", help="préparer une proposition JSON de 60 cartes"
    )
    deck_prepare.add_argument("--proposal", required=True, type=Path, help="fichier JSON de proposition")
    deck_prepare.add_argument(
        "--copy", action="store_true", help="copier seulement si toutes les impressions sont résolues"
    )
    _common_options(deck_prepare)
    deck_copy = deck_commands.add_parser(
        "copy", help="copier explicitement un .txt privé déjà prêt à importer"
    )
    deck_copy.add_argument("path", type=Path, help="fichier sous data/local/decks/import_ready")
    _common_options(deck_copy)
    candidate_create = deck_commands.add_parser(
        "candidate-create", help="prévisualiser ou enregistrer des changements contrôlés"
    )
    candidate_create.add_argument("--changes", required=True, type=Path)
    candidate_create_mode = candidate_create.add_mutually_exclusive_group()
    candidate_create_mode.add_argument("--dry-run", action="store_true")
    candidate_create_mode.add_argument("--apply", action="store_true")
    candidate_create.add_argument("--confirm-owner", action="store_true")
    _common_options(candidate_create)
    candidate_show = deck_commands.add_parser("candidate-show", help="afficher un candidat sans écriture")
    candidate_show.add_argument("--candidate", required=True, type=int)
    _common_options(candidate_show)
    candidate_export = deck_commands.add_parser(
        "candidate-export", help="prévisualiser ou exporter volontairement un candidat"
    )
    candidate_export.add_argument("--candidate", required=True, type=int)
    candidate_export_mode = candidate_export.add_mutually_exclusive_group()
    candidate_export_mode.add_argument("--dry-run", action="store_true")
    candidate_export_mode.add_argument("--apply", action="store_true")
    candidate_export.add_argument("--confirm-owner", action="store_true")
    _common_options(candidate_export)
    return parser


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _db_for(args: argparse.Namespace, root: Path) -> Path:
    candidate = args.db.absolute() if args.db else default_db_path(root)
    # Resolving first erases the junction/symlink that recovery must reject.
    if any(_redirected(p) for p in (candidate, *candidate.parents)):
        raise ValueError("RECOVERY_PATH_REDIRECTED")
    return candidate


def _private_path(path: Path, *roots: Path, label: str) -> Path:
    """Inside the repository or the data folder, a private path must stay under its data/local."""
    if any(_redirected(p) for p in (path, *path.absolute().parents)):
        raise ValueError("RECOVERY_PATH_REDIRECTED")
    resolved = path.resolve(strict=False)
    for root in roots:
        project = root.resolve()
        private = (project / "data" / "local").resolve(strict=False)
        if resolved.is_relative_to(project) and not resolved.is_relative_to(private):
            raise ValueError(f"{label} doit rester sous data/local lorsqu'il est dans le dépôt.")
    return resolved


def _human_import(result: dict[str, Any]) -> None:
    print(
        "Import terminé: "
        f"{result['documents_total']} documents, {result['sections_total']} sections; "
        f"ajoutés={result['documents_inserted']}, mis à jour={result['documents_updated']}, "
        f"inchangés={result['documents_unchanged']}; index={result['search_backend']}."
    )


def _human_status(status: dict[str, Any]) -> None:
    print(f"Base: {status['database']} ({'présente' if status['database_exists'] else 'absente'})")
    print(f"Intégrité: {status['integrity']} | version: {status['schema_version']}")
    print(f"Documents: {status['documents']} | sections: {status['sections']}")
    print(f"Journaux: {status['battle_logs']} | parties valides: {status['valid_battles']}")
    print(f"Decks exacts: {status['exact_decks']} | versions: {status['deck_versions']}")
    print(
        f"Catalogue: {status['catalog_sets']} sets | "
        f"{status['catalog_printings']} impressions | {status['catalog_translations']} traductions"
    )
    print(f"Dernière importation: {status['last_import_completed_at'] or 'jamais'}")
    print(f"Index: {status['search_backend'] or 'non créé'}")
    print(f"Fraîcheur externe: {status['external_freshness']}")
    print("Sources externes: " + "; ".join(f"{key}={value}" for key, value in status["external_sources"].items()))
    print(f"Planificateur: {status['scheduler']}")


def _human_log_import(result: dict[str, Any]) -> None:
    state = "réanalysé" if result.get("reparsed") else ("doublon ignoré" if result["duplicate"] else "importé")
    print(
        f"Journal {state}: partie={result['battle_id']}, deck={result['deck_id']}, "
        f"issue={result['outcome']}, valide={'oui' if result['valid'] else 'non'}; brut non conservé."
    )


def _human_profile(result: dict[str, Any], *, review: bool) -> None:
    summary = result["summary"] if review else result
    sample = summary["sample"]
    outcomes = summary["outcomes"]
    if sample.get("probable_duplicates_excluded"):
        print(f"Bilan provisoire : {sample['stored_valid_games']} enregistrements, "
              f"{sample['probable_duplicates_excluded']} doublon(s) probable(s) exclu(s) en mémoire; "
              "identité des parties à confirmer, ratio de victoire inconnu.")
    print(
        f"Échantillon: n={sample['valid_games']} parties valides; "
        f"W/L/inconnues={outcomes['wins']}/{outcomes['losses']}/{outcomes['unknown']}."
    )
    print(summary["assessment"])
    if summary["repeated_findings"]:
        print("Constats répétés: " + " ".join(summary["repeated_findings"][:5]))
    if review:
        print(f"Preuves: {len(result['facts'])} partie(s); hypothèses conditionnelles seulement.")


def _read_log_input(args: argparse.Namespace) -> tuple[str, str, str | None, str | None]:
    if args.clipboard and args.path:
        raise ValueError("Choisir un fichier, stdin ou --clipboard, pas plusieurs sources.")
    if args.clipboard:
        return read_clipboard(), "clipboard", None, None
    if args.path == "-":
        text = sys.stdin.read(MAX_LOG_BYTES + 1)
        if not text.strip():
            raise ValueError("Aucun journal reçu sur stdin.")
        return text, "stdin", None, "utf-8"
    if not args.path:
        raise ValueError("Indiquer un fichier, '-' pour stdin, ou --clipboard.")
    path = Path(args.path).resolve()
    if path.stat().st_size > MAX_LOG_BYTES:
        raise ValueError(f"Journal trop volumineux (maximum {MAX_LOG_BYTES} octets).")
    text, encoding = decode_log_bytes(path.read_bytes())
    return text, "file", str(path), encoding


def _read_deck_input(args: argparse.Namespace) -> tuple[str, str, str | None, str | None]:
    if args.clipboard and args.path:
        raise ValueError("Choisir un fichier, stdin ou --clipboard, pas plusieurs sources.")
    if args.clipboard:
        return read_clipboard(), "clipboard", None, None
    if args.path == "-":
        text = sys.stdin.read(MAX_DECK_BYTES + 1)
        if not text.strip():
            raise ValueError("Aucun export de deck reçu sur stdin.")
        return text, "stdin", None, "utf-8"
    if not args.path:
        raise ValueError("Indiquer un fichier, '-' pour stdin, ou --clipboard.")
    path = Path(args.path).resolve()
    if path.stat().st_size > MAX_DECK_BYTES:
        raise ValueError(f"Export de deck trop volumineux (maximum {MAX_DECK_BYTES} octets).")
    text, encoding = decode_deck_bytes(path.read_bytes())
    return text, "file", str(path), encoding


def _human_deck_import(result: dict[str, Any]) -> None:
    state = "déjà présente" if result["duplicate"] else "importée"
    print(
        f"Version exacte {state}: deck={result['deck_id']}, version={result['version']}, "
        f"total={result['total_cards']}; brut non conservé, parties historiques non associées."
    )


def _human_deck_show(result: dict[str, Any]) -> None:
    if not result["exact_confirmed"]:
        print(f"Deck {result['deck_id']}: {result['status']}; aucune liste exacte de 60 cartes.")
        return
    print(
        f"Deck {result['deck_id']}: {result['status']}, version={result['version']}, "
        f"total={result['total_cards']}, couverture impressions={result['coverage']['printing_coverage']:.0%}."
    )
    for card in result["cards"]:
        print(card["normalized_line"])


def _human_deck_compare(result: dict[str, Any]) -> None:
    context = result["context"]
    print(
        f"Comparaison {context['deck_id']} v{context['from_version']}→v{context['to_version']}: "
        f"{result['comparison_status']} (lecture seule, hors ligne)."
    )
    changes = result["facts"].get("changes")
    if not changes:
        if result["unknowns"]:
            print(result["unknowns"][0]["message"])
        return
    print(
        f"Impressions ajoutées/retirées={changes['impressions_added']}/{changes['impressions_removed']}; "
        f"quantités +{changes['quantity_increased']}/-{changes['quantity_decreased']}; "
        f"delta total={changes['delta_total']}."
    )
    if changes["details_included"]:
        print("PRIVÉ — détails locaux demandés; ne pas partager.")
        for item in changes["details"]:
            identity = " ".join(
                value for value in (item["card_name"], item["set_code"], item["collector_number"]) if value
            )
            print(f"{identity}: {item['from_quantity']} → {item['to_quantity']}")


def _human_version_evidence(result: dict[str, Any]) -> None:
    context = result["context"]
    battles = result["facts"]["battles"]
    print(
        f"Preuves combat→version {context['deck_id']} au {context['as_of']}: "
        f"{result['evidence_status']} (lecture seule, hors ligne)."
    )
    print(
        f"Combats uniques={battles['valid_unique_declared_deck']}; "
        f"liés et cohérents={battles['proven_same_deck_links']}; sans lien={battles['unlinked']}; "
        f"attestés propriétaire={battles['owner_attested_active']}; "
        f"legacy non attestés={battles['legacy_explicit_link_unattested']}; "
        f"révoqués={battles['owner_attested_revoked']}; conflits={battles['conflicting_links']}; "
        f"doutes temporels={battles['temporal_doubts']}."
    )
    print(result["facts"].get("sample_conclusion", "données insuffisantes"))
    if result["confirmations"]:
        print(f"Confirmations requises: {len(result['confirmations'])} référence(s) locale(s) opaque(s).")


def _human_link_candidates(result: dict[str, Any]) -> None:
    print(
        f"Combats locaux en attente pour {result['deck_id']}: {result['count']} "
        "(lecture seule, hors ligne)."
    )
    for item in result["candidates"]:
        print(
            f"battle-id={item['battle_id']} | import={item['imported_date'] or 'inconnu'} | "
            f"issue={item['outcome']} | date réelle={item['battle_date']}"
        )
    print(result["warning"])


def _human_attestation(result: dict[str, Any]) -> None:
    action = "Confirmation" if result["operation"] == "confirm_battle_version" else "Révocation"
    mode = "appliquée" if result["applied"] else "prévisualisée sans écriture"
    print(
        f"{action} {mode}: battle-id={result['battle_id']}, statut={result['status']}, "
        "source=owner_asserted (non vérifiée indépendamment)."
    )
    if result.get("confirmed_at"):
        print(f"Confirmation UTC: {result['confirmed_at']}")
    if result.get("revoked_at"):
        print(f"Révocation UTC: {result['revoked_at']}")


def _prepared_payload(prepared: PreparedDeck, *, copied: bool) -> dict[str, Any]:
    return {
        "status": prepared.report["status"],
        "format_validation": prepared.report["format_validation"],
        "total_cards": prepared.report["total_cards"],
        "text_path": str(prepared.text_path),
        "report_path": str(prepared.report_path),
        "copied": copied,
        "fallback": "ouvrir le .txt, Ctrl+A, Ctrl+C",
        "warnings": prepared.report["warnings"],
    }


def _human_deck_prepared(result: dict[str, Any]) -> None:
    print(f"Deck préparé: {result['status']} | 60/60 | {result['text_path']}")
    print(f"Rapport local: {result['report_path']}")
    if result["copied"]:
        print("Texte importable copié explicitement dans le presse-papiers.")
    else:
        print("Presse-papiers inchangé; repli: ouvrir le .txt, Ctrl+A, Ctrl+C.")


def _human_cards_sync(result: dict[str, Any]) -> None:
    if result["dry_run"]:
        print(
            f"Simulation: réseau=non, écritures=0, langues={','.join(result['languages'])}, "
            f"budget={result['max_requests']}, migration={'oui' if result['would_migrate'] else 'non'}."
        )
        return
    coverage = result["coverage"]
    print(
        f"TCGdex: {result['requests_made']}/{result['max_requests']} requêtes; "
        f"{coverage['unique_printings']} impressions, {coverage['details_retrieved_any_language']} détaillées."
    )
    print(f"Arrêt: {result['stopped_reason']}" + (f" — {result['error']}" if result["error"] else "."))


def _human_cards_coverage(result: dict[str, Any]) -> None:
    print(
        f"Catalogue local: {result['sets_discovered']} sets, {result['unique_printings']} impressions, "
        f"{result['details_retrieved_any_language']} détaillées; complet={'oui' if result['complete'] else 'non'}."
    )
    for language, values in result["languages"].items():
        statuses = values["statuses"]
        print(
            f"{language}: noms={values['names']}, présents={statuses['present']}, "
            f"non récupérés={statuses['not_fetched']}, absents={statuses['absent']}, "
            f"erreurs réseau={statuses['network_error']}."
        )


def _human_rules_verdict(result: dict[str, Any]) -> None:
    subject = result.get("tcgdex_id") or result.get("deck_id")
    print(f"{subject}: {result['status']} ({result['format']}, {result['platform']}, {result['as_of']}).")
    if result.get("reason_codes"):
        print("Raisons: " + ", ".join(result["reason_codes"]))


def _human_meta(result: dict[str, Any], command: str) -> None:
    if command == "sync":
        if result["dry_run"]:
            print(f"Simulation Limitless: réseau=non, écritures=0, budget={result['max_requests']}.")
        else:
            print(f"Limitless: {result['requests_made']}/{result['max_requests']} GET; "
                  f"tournois importés={len(result['imported'])}; arrêt={result['stopped_reason']}.")
        return
    if command == "status":
        print(f"Cache Limitless: {result['tournaments']} tournois, {result['matches']} matchs; hors ligne=oui.")
        return
    if command == "tournaments":
        print(f"Tournois admissibles: {result['count']} (filtres explicites, hors ligne).")
        return
    if command == "archetypes":
        print(f"Archétypes publiés: {len(result['archetypes'])}; classifiés={result['n_classified']}/{result['n_placements']}.")
        return
    if command == "coverage":
        print(
            f"Couverture méta: {result['tournaments']['complete_snapshots']} tournoi(s), "
            f"placements classifiés={result['placements']['classified']}/"
            f"{result['placements']['denominator']}, matchs classifiables="
            f"{result['matches']['classifiable']}/{result['matches']['denominator']}."
        )
        return
    print(f"Matchups descriptifs: {len(result['matchups'])}; unité=match publié.")


def _human_competitive_advisor(result: dict[str, Any], command: str) -> None:
    print(f"PUBLIC hors ligne — {result['as_of']} — {result['status']}")
    if command == "competitive-inventory":
        print(f"{result['sampled_placements']} placements; {result['valid_placements']} vérifiés; "
              f"{result['distinct_compositions']} compositions distinctes; {len(result['archetype_labels'])} étiquettes.")
        for group in result["compositions"]:
            print(f"  {group['reference']} | {', '.join(group['archetypes'])} | "
                  f"{group['placements']} placement(s), éventail {group['placement_range']} | "
                  f"{group['date_range'][0]}–{group['date_range'][1]} | {group['composition_id'][:12]}")
            print("    " + " ; ".join(group["source_urls"]))
    elif command == "competitive-compare":
        for label, group in (("A", result["left"]), ("B", result["right"])):
            facts = group["build_facts"]
            print(f"{label} {group['reference']} | {', '.join(group['archetypes'])} | "
                  f"60 cartes : {facts['section_copies']} | dates {group['date_range']}")
            print("  " + " ; ".join(group["source_urls"]))
        counts = result["changes"]["counts"]
        print(f"Copies partagées {counts['shared']}; retirées de A {counts['removed']}; ajoutées en B {counts['added']}.")
        print(f"Même composition : {result['same_composition']}. Identités d'impression exactes; aucune équivalence déduite.")
        for field, label in (("shared", "Partagées"), ("removed", "Retirées"), ("added", "Ajoutées")):
            print(label + " :")
            for card in result["changes"][field]:
                print(f"  {card['quantity']} {card['name']} {card['set']} {card['number']}")
            omitted = result["changes"]["omitted_identities"][field]
            if omitted:
                print(f"  … {omitted} autres identités; augmenter --limit pour les afficher.")
    else:
        print("Options de plans différents; base Dragapult, puis familles distinctes. Aucun classement de force.")
        for group in result["options"]:
            facts = group["build_facts"]
            print(f"  {group['export_selector']} | {', '.join(group['archetypes'])} | 60 cartes : {facts['section_copies']}")
            print("    Fait, Énergies de la liste : " + "; ".join(f"{card['quantity']} {card['name']}" for card in facts["energy_cards"]))
            if facts["stages_from_cached_text"]:
                print("    Fait, stades sourcés : " + "; ".join(f"{card['name']}={card['stage']}" for card in facts["stages_from_cached_text"]) + "; autres stades inconnus.")
            print(f"    {group['plan_hypothesis']}")
            print(f"    Différence depuis la base (copies) : {group['difference_from_base']}; dates {group['date_range']}.")
            print("    " + " ; ".join(group["source_urls"]))
    if result["issues"]:
        print(f"Données écartées/incomplètes : {len(result['issues'])}; détails dans --json.")
    print("Échantillon de bonnes places biaisé. Inconnus : matchup,winrate,BO1/BO3,Live,collection,crédits,compatibilité à date.")
    print("Export séparé : meta competitive-export --db PUBLIC --event ID --placement RANG. Aucun réseau ni changement de deck.")


def _human_analysis(result: dict[str, Any]) -> None:
    context = result["context"]
    deck = result["facts"]["deck"]
    battles = result["facts"]["battles"]
    print(
        f"Diagnostic {context['deck_id']} — {context['format']}/{context['platform']} au {context['as_of']}: "
        f"{result['assessment']} (confiance {result['confidence']['level']})."
    )
    if deck.get("found"):
        print(
            f"Deck: version {deck['version']}, exact={'oui' if deck['exact_confirmed'] else 'non'}, "
            f"quantités={deck['quantity_sum']}/{deck['recorded_total']}, "
            f"applicabilité historique={deck.get('historical_applicability', 'unknown')}."
        )
    else:
        print("Deck: aucune version locale trouvée.")
    print(
        f"Combats: n={battles['valid_unique']} uniques; W={battles['outcomes']['wins']}, "
        f"L={battles['outcomes']['losses']}, nuls={battles['outcomes']['draws']}, "
        f"ambigus={battles['outcomes']['ambiguous']}; liés à cette version={battles['with_selected_version_proven']}."
    )
    catalog = result["facts"]["catalog"]
    if catalog.get("available"):
        resolution = catalog["entry_resolution"]
        print(
            f"Impressions: {resolution['resolved']}/{resolution['denominator']} résolues; "
            f"ambiguës={resolution['ambiguous']}, non résolues={resolution['unresolved']}."
        )
    rules = result["facts"]["rules"]
    meta = result["facts"]["metagame"]
    print(
        f"Règles: {rules.get('status', 'unknown')}; méta compatible: "
        f"{meta.get('n_tournaments', 0)} tournoi(s), {meta.get('n_published_archetypes', 0)} archétype(s), "
        f"{meta.get('n_exploitable_matches', 0)} match(s) exploitable(s)."
    )
    print("Prochaine preuve: " + (result["next_evidence"][0] if result["next_evidence"] else "aucune identifiée"))


def _human_knowledge(result: dict[str, Any], *, audit: bool) -> None:
    cards = result["cards"]
    rules = result["rules"]
    meta = result["metagame"]
    print(
        f"Connaissances hors ligne: schéma={result['schema_version']}, "
        f"intégrité={result['integrity']}, actuel={'oui' if result['schema_current'] else 'non'}."
    )
    print(
        f"Cartes={cards.get('unique_printings', 0)}; règles de structure vérifiées="
        f"{rules.get('deck_structure_rule_counts', {}).get('verified', 0)}; "
        f"réimpressions vérifiées={result['reprints']['verified_assertions']}; "
        f"tournois méta complets={meta.get('tournaments', {}).get('complete_snapshots', 0)}."
    )
    print(f"Actions prioritaires: {len(result['actions'])}.")
    if audit:
        print(f"Audit: {result['audit']['status']}.")


def main(argv: Sequence[str] | None = None) -> int:
    # Rend les sorties redirigées déterministes sur Windows, où la page de codes
    # historique varie selon le terminal.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    wants_json = bool(getattr(args, "json", False))
    try:
        if args.command == "desktop":
            try:
                from pokemind.desktop.app import launch
                return launch(Path.cwd())
            except ImportError:
                print("Interface non installée. Utiliser scripts/Install-PokeMindDesktop.ps1.", file=sys.stderr)
                return 2
        if args.command == "battle" and args.battle_command == "coach":
            from pokemind.battle_coach import coach
            result = coach(Path.cwd(), player=args.player, update=args.update, as_of=args.as_of)
            ok = result["status"] == "COACH_LOCAL_REPORT"
            _print_json({"ok": ok, **{k: v for k, v in result.items() if k != "text"}}) if wants_json else print(result["text"], end="")
            return 0 if ok else 1
        if args.command == "battle" and args.battle_command in {"batch-report", "legacy-plan"}:
            from pokemind.legacy_bridge import saved_report, legacy_plan, human_legacy_plan
            if args.battle_command == "batch-report":
                result = saved_report(Path.cwd(), report=args.report, learning=args.learning)
                _print_json({"ok": True, **{k:v for k,v in result.items() if k != "text"}}) if wants_json else print(result["text"], end="")
            else:
                result = legacy_plan(Path.cwd(), db=args.db)
                _print_json({"ok": True, **result}) if wants_json else print(human_legacy_plan(result), end="")
            return 0
        if args.command == "battle" and args.battle_command == "batch-intelligence":
            from pokemind.battle_batch import batch_analyze, human_report
            if not args.folder or not args.player:
                raise ValueError("BATCH_EXPLICIT_FOLDER_AND_PLAYER_REQUIRED")
            if args.refresh_public:
                from pokemind.batch_public_research import refresh_public
                try:
                    refresh_public(Path.cwd(), as_of=args.as_of)
                except (ValueError, OSError, sqlite3.Error):
                    # A public-source block must not cancel the authorized offline
                    # match analysis. Closed/reserved envelopes are never retried.
                    print("Recherche PUBLIC partielle/bloquée; analyse locale poursuivie.", file=sys.stderr)
            result = batch_analyze(Path.cwd(), folder=args.folder, player=args.player, db=args.db,
                as_of=args.as_of, apply=args.apply, recommendations=not args.no_recommendations)
            _print_json({"ok": True, **result}) if wants_json else print(human_report(result), end="")
            return 0
        if args.command == "meta" and args.meta_command == "public-identity-explain":
            from pokemind.public_deck_preflight import identity_explain, human_identity_explain, html_identity_explain
            # This command requires the current directory to be the selected
            # project root. No root discovery, arbitrary DB flag or owner fallback.
            try:
                result = identity_explain(Path.cwd(), as_of=args.as_of, selector=args.selector)
            except (KeyError, TypeError, AttributeError, IndexError):
                # Malformed cached fields must not expose a traceback or path.
                raise ValueError("PUBLIC_IDENTITY_EXPLAIN_BLOCKED") from None
            if args.html:
                print(html_identity_explain(result))
            elif wants_json:
                _print_json({"ok": True, **result})
            else:
                human_identity_explain(result)
            return 0
        project = find_project_root()
        # Owner data may live outside the repository once the owner accepted the copy (D-264);
        # tracked files (seed sources, rules registry, demo fixtures, scripts) stay in the project.
        from pokemind import data_location
        root = data_location.cli_root(project)
        if args.command == "preflight":
            from pokemind.runtime_preflight import runtime_preflight
            result = runtime_preflight()
            _print_json({"ok": True, **result}) if wants_json else print(f"Prévol: {result['status']}; aucune base personnelle ouverte.")
            return 0 if result["status"] == "RUNTIME_READY" else 2
        if args.command == "demo":
            from pokemind.demo import run_demo
            result = run_demo(project)
            _print_json({"ok": True, **result}) if wants_json else print(
                f"Démo synthétique: {result['status']}; 10 recherches, 60 cartes, {result['battles']['n']} combats, 3 tours; {result['release_status']}.")
            return 0
        # These diagnostics do not consume a database. Avoid even inspecting
        # the default database path (including reparse metadata) on first use.
        if args.command == "battle" and args.battle_command == "review-selected":
            from pokemind.selected_match_review import review_selected, human_review
            result = review_selected(root, args.db, deck_id=args.deck, as_of=args.as_of,
                **{name: getattr(args, name) for name in (
                    "log_file", "battle_id", "dry_run", "apply", "confirm_owner_read", "confirm_owner_import",
                    "confirm_owner_attest", "version", "battle_date", "revoke_version", "reason",
                    "public_db", "reference_db", "learning_out")}, use_set_aliases=args.set_aliases)
            _print_json({"ok": result["status"] != "PARTIAL_LOCAL_REVIEW_REQUIRED", **result}) if wants_json else human_review(result)
            return 2 if result["status"] == "PARTIAL_LOCAL_REVIEW_REQUIRED" else 0
        if args.command == "meta" and args.meta_command in {"counter-plan", "learning-simulate"}:
            from pokemind.counter_deck import counter_plan, human_counter
            from pokemind.learning_simulation import simulate, human_simulation
            kwargs = dict(as_of=args.as_of, target=args.target, base=args.base, use_set_aliases=args.set_aliases)
            if args.meta_command == "counter-plan":
                result = counter_plan(root, args.db, args.reference_db, options=args.options, **kwargs)
                _print_json({"ok": True, **result}) if wants_json else human_counter(result)
            else:
                result = simulate(root, args.db, args.reference_db, **kwargs)
                _print_json({"ok": True, **result}) if wants_json else human_simulation(result)
            return 0
        if args.command == "battle" and args.battle_command in {"opponent", "matchups"}:
            from pokemind.matchup_analytics import opponent_for_battle, matchup_report, human_matchups
            from pokemind.opponent_observer import human_opponent
            shared = dict(as_of=args.as_of, confirm_owner_read=args.confirm_owner_read,
                          public_db=args.public_db, reference_db=args.reference_db)
            if args.battle_command == "opponent":
                result = opponent_for_battle(root, args.db, battle_id=args.battle_id, **shared)
                _print_json({"ok": True, **result}) if wants_json else human_opponent(result)
            else:
                result = matchup_report(root, args.db, deck_id=args.deck, since=args.since, until=args.until, **shared)
                _print_json({"ok": True, **result}) if wants_json else human_matchups(result)
            return 0
        if args.command == "meta" and args.meta_command == "deck-library":
            from pokemind.deck_library import library_list, human_library
            if args.db is None:
                raise ValueError("DECK_LIBRARY_EXPLICIT_PUBLIC_DATABASE_REQUIRED")
            result = library_list(root, args.db, as_of=args.as_of, archetype=args.archetype,
                                  event=args.event, since=args.since, until=args.until, version=args.version)
            _print_json({"ok": True, **result}) if wants_json else human_library(result)
            return 0
        if args.command == "meta" and args.meta_command == "deck-knowledge":
            from pokemind.deck_knowledge import knowledge_show, human_knowledge
            if args.db is None:
                raise ValueError("DECK_KNOWLEDGE_EXPLICIT_PUBLIC_DATABASE_REQUIRED")
            result = knowledge_show(root, args.db, args.reference_db, selector=args.selector,
                                    as_of=args.as_of, use_set_aliases=args.set_aliases)
            _print_json({"ok": True, **result}) if wants_json else human_knowledge(result)
            return 0
        if args.command == "meta" and args.meta_command == "competitive-preflight":
            from pokemind.public_deck_preflight import competitive_preflight, human_preflight
            if args.db is None:
                raise ValueError("PUBLIC_PREFLIGHT_EXPLICIT_PUBLIC_DATABASE_REQUIRED")
            result = competitive_preflight(root, args.db, args.reference_db, as_of=args.as_of,
                                           format=args.format, platform=args.platform,
                                           selectors=args.select, options=args.options, use_set_aliases=args.set_aliases)
            _print_json({"ok": True, **result}) if wants_json else human_preflight(result)
            return 0
        if args.command == "meta" and args.meta_command in {
            "competitive-inventory", "competitive-compare", "competitive-shortlist",
        }:
            if args.db is None:
                raise ValueError("COMPETITIVE_ADVISOR_EXPLICIT_PUBLIC_DATABASE_REQUIRED")
            from pokemind.competitive import competitive_inventory, competitive_compare, competitive_shortlist
            if args.meta_command == "competitive-inventory":
                result = competitive_inventory(root, args.db, as_of=args.as_of)
            elif args.meta_command == "competitive-compare":
                result = competitive_compare(root, args.db, args.left, args.right, as_of=args.as_of, limit=args.limit)
            else:
                result = competitive_shortlist(root, args.db, as_of=args.as_of, options=args.options, base=args.base)
            _print_json({"ok": True, **result}) if wants_json else _human_competitive_advisor(result, args.meta_command)
            return 0
        if args.command == "meta" and args.meta_command in {"competitive-summary", "competitive-export"}:
            if args.db is None:
                raise ValueError("COMPETITIVE_EXPLICIT_PUBLIC_DATABASE_REQUIRED")
            from pokemind.public_campaign import require_public_database
            from pokemind.competitive import competitive_summary, competitive_export
            # Validate namespace before resolution or any default-owner inspection.
            require_public_database(root, args.db)
            if args.meta_command == "competitive-summary":
                result = competitive_summary(root, args.db)
                _print_json({"ok": True, **result})
            else:
                text = competitive_export(root, args.db, args.event, args.placement)
                if wants_json:
                    _print_json({"ok": True, "text": text, "total_cards": 60,
                                 "live_legality": "unknown", "network_used": False,
                                 "owner_database_opened": False})
                else:
                    print(text, end="")
            return 0
        if args.command == "knowledge" and args.knowledge_command == "update" and args.public_only:
            if args.db is None:
                raise ValueError("PUBLIC_UPDATE_EXPLICIT_DATABASE_REQUIRED")
            from pokemind.public_campaign import public_database_path
            args.db = public_database_path(root, args.db)
        database_free = (args.command == "match" and args.match_command in {
            "capabilities", "preflight", "benchmark-ocr",
        }) or (args.command == "knowledge" and args.knowledge_command in {"scheduler", "cadence"})
        db_path = None if database_free else _db_for(args, root)
        if args.command == "owner-plan":
            result = commissioning_preflight(db_path, step=args.step,
                backup_path=_private_path(args.backup, root, project, label="La sauvegarde") if args.backup else None,
                clone_path=_private_path(args.clone, root, project, label="Le clone") if args.clone else None)
            _print_json({"ok": True, **result}) if wants_json else print(f"Prévol {args.step}: {result['status']}; aucune action exécutée.")
            return 0
        if args.command == "import-seed":
            result = import_seed(project, db_path)
            payload = {"ok": True, **result}
            _print_json(payload) if wants_json else _human_import(result)
            return 0
        if args.command == "search":
            results = search_database(db_path, args.query, args.limit)
            payload = {"ok": True, "query": args.query, "count": len(results), "results": results}
            if wants_json:
                _print_json(payload)
            elif not results:
                print("Aucun résultat.")
            else:
                for index, result in enumerate(results, start=1):
                    print(f"{index}. {result['heading']}")
                    print(f"   {result['snippet']}")
                    print(f"   Citation: {result['citation']}")
            return 0
        if args.command == "status":
            status = database_status(db_path)
            payload = {"ok": True, **status}
            _print_json(payload) if wants_json else _human_status(status)
            return 0
        if args.command == "v1":
            backup_directory = None
            if args.backup_directory is not None:
                backup_directory = _private_path(
                    args.backup_directory, root, project, label="Le répertoire de sauvegarde",
                )
            result = v1_readiness(db_path, backup_directory=backup_directory)
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Préparation V1: {result['status']}; "
                    f"schéma={result['database']['schema_version']}/{result['database']['expected_schema_version']}; "
                    f"blocages={len(result['blockers'])}."
                )
            return 0
        if args.command == "backup":
            local_root = (root / "data" / "local").resolve()
            destination = _private_path(
                args.destination if getattr(args, "destination", None) else db_path.parent / "backups",
                root, project, label="La destination de sauvegarde",
            )
            if args.backup_command == "plan":
                result = backup_plan(db_path, destination, min_free_bytes=args.min_free_bytes)
            elif args.backup_command == "create":
                result = create_backup(
                    db_path, destination, apply=args.apply, confirm_owner=args.confirm_owner,
                    min_free_bytes=args.min_free_bytes,
                )
            elif args.backup_command == "status":
                result = backup_status(destination)
            elif args.backup_command == "verify":
                backup = _private_path(args.backup, root, project, label="La sauvegarde")
                result = verify_backup(backup)
            else:
                policy = {
                    "keep_last": args.keep_last,
                    "max_age_days": args.max_age_days,
                    "max_total_bytes": args.max_total_bytes,
                    "work_max_age_days": args.work_max_age_days,
                    "log_max_age_days": args.log_max_age_days,
                }
                if args.apply:
                    result = apply_retention(
                        destination, local_root=local_root,
                        plan_sha256=args.plan_sha256 or "", apply=True,
                        confirm_owner=args.confirm_owner, **policy,
                    )
                else:
                    result = retention_plan(destination, local_root=local_root, **policy)
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Sauvegarde locale: commande={args.backup_command}; "
                    f"état={result.get('state', result.get('mode', 'lecture seule'))}; réseau=non."
                )
            return 0
        if args.command == "restore":
            backup = _private_path(args.backup, root, project, label="La sauvegarde")
            target = _private_path(db_path, root, project, label="La cible de restauration")
            if args.restore_command == "plan":
                result = restore_plan(
                    backup, target, migrate_clone=args.migrate_clone,
                    min_free_bytes=args.min_free_bytes,
                )
            elif args.restore_command == "verify":
                result = restore_verify(
                    backup, migrate_clone=args.migrate_clone,
                    work_directory=target.parent,
                )
            else:
                result = restore_backup(
                    backup, target, apply=args.apply, confirm_owner=args.confirm_owner,
                    migrate_clone=args.migrate_clone, min_free_bytes=args.min_free_bytes,
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Restauration locale: commande={args.restore_command}; "
                    f"état={result.get('state', result.get('mode', 'lecture seule'))}; réseau=non."
                )
            return 0
        if args.command == "knowledge":
            if args.knowledge_command == "cadence":
                result = cadence_preview(start_utc=datetime.fromisoformat(args.start_utc.replace("Z", "+00:00")),
                    daily_time=args.daily_time, deep_time=args.deep_time, days=args.days)
                _print_json({"ok": True, **result}) if wants_json else print(f"Cadence simulée: {len(result['events'])} échéances; OS OWNER_ACTION_REQUIRED.")
                return 0
            if args.knowledge_command == "review-official":
                result = record_official_review(db_path, args.source, content_sha256=args.content_sha256,
                    document_version=args.document_version, decision=args.decision,
                    full_document_reviewed=args.full_document_reviewed, apply=args.apply, confirm_owner=args.confirm_owner)
                if wants_json:
                    _print_json({"ok": True, **result})
                else:
                    print(f"Revue documentaire: {result['status']}; assertions normatives inchangées.")
                return 0
            if args.knowledge_command == "scheduler":
                result = scheduler_preview(
                    project,
                    action=args.action,
                    daily_time=args.daily_time,
                    deep_time=args.deep_time,
                    dry_run=args.dry_run,
                    confirm_owner=args.confirm_owner,
                    windows_timezone=args.windows_timezone,
                    public_database=args.db,
                )
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(
                        f"Planificateur: {result['status']}; action={result['action']}; "
                        f"système modifié={'oui' if result['system_changed'] else 'non'}."
                    )
                return 0
            if args.knowledge_command == "update":
                if args.public_only:
                    if args.db is None:
                        raise ValueError("PUBLIC_UPDATE_EXPLICIT_DATABASE_REQUIRED")
                    from pokemind.public_campaign import require_public_database
                    require_public_database(root, db_path)
                if args.update_action == "status":
                    result = update_status(db_path, deep_local_time=args.deep_time)
                else:
                    requested_budgets = {
                        key: value for key, value in {
                            "tcgdex": args.tcgdex_budget,
                            "pokemon_official": args.official_budget,
                            "limitless": args.limitless_budget,
                        }.items() if value is not None
                    }
                    result = run_public_update(
                        db_path,
                        default_registry_path(project),
                        mode=args.mode,
                        dry_run=not args.apply,
                        apply=args.apply,
                        confirm_owner=args.confirm_owner,
                        probe_public_network=args.probe_public_network,
                        deep_local_time=args.deep_time,
                        budgets=requested_budgets or None,
                    )
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(
                        f"Actualisation publique: {result['status']}; "
                        f"réseau={'oui' if result.get('network_used') else 'non'}; "
                        f"lecture seule={'oui' if result.get('read_only') else 'non'}."
                    )
                return 0
            result = knowledge_audit(db_path) if args.knowledge_command == "audit" else knowledge_status(db_path)
            payload = {"ok": True, **result}
            _print_json(payload) if wants_json else _human_knowledge(
                result, audit=args.knowledge_command == "audit"
            )
            return 0
        if args.command == "capability":
            result = capability_status(db_path)
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Capacités LOT B: schéma={result['schema_version']}; "
                    f"deck exact={result['objects']['exact_deck_versions']}; "
                    f"lacunes={len(result['gaps'])}."
                )
            return 0
        if args.command == "analyze":
            result = analyze_deck(
                db_path, args.deck, as_of=args.as_of, format=args.format, platform=args.platform
            )
            payload = {"ok": True, **result}
            _print_json(payload) if wants_json else _human_analysis(result)
            return 0
        if args.command == "recommend":
            result = recommend_deck(
                db_path, args.deck, as_of=args.as_of, format=args.format,
                platform=args.platform, use_collection=args.collection,
            )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Conseil {args.deck} — {args.format}/{args.platform} au {args.as_of}: "
                    f"{result['status']}; changements candidats={len(result['candidate_changes'])}."
                )
                if result["next_evidence"]:
                    print("Prochaine preuve: " + result["next_evidence"][0])
            return 0
        if args.command == "battle":
            if args.battle_command == "lessons":
                result = battle_lessons(db_path, args.deck, as_of=args.as_of)
            else:
                result = save_battle_note(
                    db_path, deck_id=args.deck, battle_id=args.battle_id, text=args.text,
                    confidence=args.confidence, kind=args.kind,
                    public_source_url=args.source_url, public_source_date=args.source_date,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Combats: commande={args.battle_command}; "
                    f"état={result.get('status', result.get('mode', 'lecture seule'))}."
                )
            return 0
        if args.command == "collection":
            if args.collection_command == "import":
                local_root = (root / "data" / "local").resolve()
                collection_path = args.path.resolve()
                if not collection_path.is_relative_to(local_root):
                    raise ValueError("Le fichier de collection doit rester sous data/local.")
                result = import_collection(
                    db_path, collection_path, apply=args.apply, confirm_owner=args.confirm_owner
                )
            elif args.collection_command == "status":
                result = collection_status(db_path, as_of=args.as_of)
            elif args.collection_command == "coverage":
                result = collection_coverage(db_path, as_of=args.as_of)
            elif args.collection_command == "missing":
                result = collection_missing(db_path, args.deck, as_of=args.as_of)
            else:
                result = rollback_collection(
                    db_path, args.snapshot, apply=args.apply, confirm_owner=args.confirm_owner
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Collection locale: commande={args.collection_command}; "
                    f"mode={result.get('mode', 'lecture seule')}; "
                    f"disponibilité={result.get('availability_status', 'non applicable')}; réseau=non."
                )
            return 0
        if args.command == "credits":
            if args.credits_command == "set":
                result = set_credits(
                    db_path, args.amount, as_of=args.as_of,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            elif args.credits_command == "status":
                result = credits_status(db_path, as_of=args.as_of)
            else:
                result = rollback_credits(
                    db_path, args.snapshot, apply=args.apply, confirm_owner=args.confirm_owner
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Crédits déclarés: commande={args.credits_command}; "
                    f"mode={result.get('mode', 'lecture seule')}; "
                    f"disponibilité={result.get('availability_status', 'non applicable')}; dépense=0."
                )
            return 0
        if args.command == "match":
            private_root = (root / "data" / "local").resolve()
            # Preserve lexical reparse checks in the OCR policy reader.
            ocr_policy = getattr(args, "ocr_trust", None)
            if ocr_policy is not None:
                if not ocr_policy.is_absolute():
                    ocr_policy = Path.cwd() / ocr_policy
                if not ocr_policy.resolve().is_relative_to((root / "data" / "local").resolve()):
                    raise ValueError("OCR_TRUST_POLICY_MUST_BE_PRIVATE")
            if args.match_command == "capabilities":
                result = vision_backend_status()
            elif args.match_command == "preflight":
                from pokemind.ocr_preflight import ocr_preflight
                result = ocr_preflight(policy_path=ocr_policy, execute=args.execute_reviewed_ocr)
            elif args.match_command == "benchmark-ocr":
                result = benchmark_ocr(policy_path=ocr_policy, execute=args.execute_reviewed_ocr)
            elif args.match_command == "review":
                result = review_observation(db_path, args.session, args.observation, verdict=args.verdict,
                                            scope=args.scope, calibration_sha256=args.calibration_sha256,
                                            apply=args.apply, confirm_owner=args.confirm_owner)
            elif args.match_command == "revoke-review":
                result = revoke_visual_review(db_path, args.review, apply=args.apply, confirm_owner=args.confirm_owner)
            elif args.match_command == "start":
                result = start_session(
                    db_path, format=args.format, platform=args.platform, as_of=args.as_of,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            elif args.match_command == "observe":
                result = observe_training(
                    db_path, private_root, turn=args.turn, image_path=args.image,
                    annotation_path=args.annotation, session_id=args.session, mode=args.mode,
                    frame_scope=args.frame_scope,
                    calibration_path=args.calibration,
                    ocr_policy=ocr_policy, execute_reviewed_ocr=args.execute_reviewed_ocr,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            elif args.match_command == "show":
                result = session_memory(db_path, args.session)
            elif args.match_command == "correct":
                result = correct_observation(
                    db_path, private_root, args.session, args.observation, args.annotation,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            elif args.match_command == "revoke-correction":
                result = revoke_correction(
                    db_path, args.session, args.observation,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
            elif args.match_command == "advise":
                result = advise_turn(
                    db_path, args.session, turn=args.turn, format=args.format,
                    platform=args.platform, as_of=args.as_of,
                )
            else:
                result = close_session(
                    db_path, args.session, apply=args.apply, confirm_owner=args.confirm_owner,
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                print(
                    f"Entraînement: commande={args.match_command}; "
                    f"état={result.get('status', result.get('mode', 'lecture seule'))}; réseau=non."
                )
                if args.match_command == "advise" and result.get("recommended_sequence"):
                    print("Séquence: " + " → ".join(item["action"] for item in result["recommended_sequence"]))
                if result.get("next_annotation_or_capture"):
                    print("Preuve minimale: " + result["next_annotation_or_capture"][0])
            return 0
        if args.command == "cards":
            if args.cards_command == "sync":
                result = sync_cards(
                    db_path,
                    languages=args.lang,
                    max_requests=args.max_requests,
                    dry_run=args.dry_run,
                    phase=args.phase,
                    refresh_index=args.refresh_index,
                    recheck_absent=args.recheck_absent,
                    prioritize_deck=args.prioritize_deck,
                )
                payload = {"ok": result.get("error") is None, **result}
                _print_json(payload) if wants_json else _human_cards_sync(result)
                return 0 if result.get("error") is None else 2
            if args.cards_command == "search":
                results = search_cards(db_path, args.query, language=args.lang, limit=args.limit)
                payload = {"ok": True, "query": args.query, "count": len(results), "results": results}
                if wants_json:
                    _print_json(payload)
                elif not results:
                    print("Aucune carte trouvée dans le cache local.")
                else:
                    for result in results:
                        print(
                            f"{result['tcgdex_id']} [{result['language']}] {result['name']} "
                            f"({result['status']})"
                        )
                return 0
            if args.cards_command == "show":
                result = show_card(db_path, args.tcgdex_id, language=args.lang)
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(
                        f"{result['tcgdex_id']} [{result['language']}] "
                        f"{result['name'] or 'nom inconnu'} — {result['status']}"
                    )
                return 0
            if args.cards_command == "reprints":
                result = card_reprints(db_path, args.tcgdex_id, as_of=args.as_of)
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(
                        f"Réimpressions vérifiées pour {args.tcgdex_id}: "
                        f"{len(result['verified_reprints'])}; statut={result['status']}."
                    )
                return 0
            if args.cards_command == "coverage":
                result = cards_coverage(db_path)
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_cards_coverage(result)
                return 0
            result = resolve_deck_cards(db_path, args.deck)
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            else:
                counts = result["counts"]
                print(
                    f"Résolution lecture seule: {counts['resolved']} résolues, "
                    f"{counts['ambiguous']} ambiguës, {counts['unresolved']} non résolues."
                )
            return 0
        if args.command == "rules":
            if args.rules_command == "load-official":
                registry = args.registry.resolve() if args.registry else default_registry_path(project)
                result = load_official_registry(db_path, registry)
            elif args.rules_command == "sources":
                result = rules_sources(db_path)
            elif args.rules_command == "status":
                result = rules_status(db_path)
            elif args.rules_command == "check-card":
                result = check_card_legality(
                    db_path, args.tcgdex_id, format=args.format,
                    platform=args.platform, as_of=args.as_of,
                )
            else:
                result = check_deck_legality(
                    db_path, args.deck, format=args.format,
                    platform=args.platform, as_of=args.as_of,
                )
            payload = {"ok": True, **result}
            if wants_json:
                _print_json(payload)
            elif args.rules_command == "load-official":
                print(f"Registre officiel chargé: {result['sources_loaded']} sources, {result['assertions_loaded']} assertions.")
            elif args.rules_command == "sources":
                print(f"Sources officielles locales: {result['count']} (consultation hors ligne).")
            elif args.rules_command == "status":
                print(f"Registre {result['registry_version'] or 'non chargé'}; couverture des restrictions partielle.")
            else:
                _human_rules_verdict(result)
            return 0
        if args.command == "meta":
            online = getattr(args, "online", "true") == "true"
            if args.meta_command == "sync":
                result = sync_meta(
                    db_path, max_requests=args.max_requests, max_tournaments=args.max_tournaments,
                    format=args.format, platform=args.platform, online=online, mode=args.mode,
                    dry_run=args.dry_run,
                )
                payload = {"ok": result.get("error") is None, **result}
            elif args.meta_command == "tournaments":
                result = meta_tournaments(db_path, format=args.format, platform=args.platform,
                                          online=online, since=args.since)
                payload = {"ok": True, **result}
            elif args.meta_command == "archetypes":
                result = meta_archetypes(db_path, format=args.format, platform=args.platform,
                                         online=online, since=args.since)
                payload = {"ok": True, **result}
            elif args.meta_command == "matchups":
                result = meta_matchups(db_path, args.archetype, min_sample=args.min_sample,
                                       format=args.format, platform=args.platform,
                                       online=online, since=args.since)
                payload = {"ok": True, **result}
            elif args.meta_command == "coverage":
                result = meta_coverage(
                    db_path, format=args.format, platform=args.platform,
                    online=online, since=args.since,
                )
                payload = {"ok": True, **result}
            else:
                result = meta_status(db_path)
                payload = {"ok": True, **result}
            _print_json(payload) if wants_json else _human_meta(result, args.meta_command)
            return 0 if payload["ok"] else 2
        if args.command == "log":
            text, source_kind, source_name, encoding = _read_log_input(args)
            result = import_battle_log(
                db_path, text, source_kind=source_kind, source_name=source_name,
                deck_id=args.deck, reparse=args.reparse,
            )
            payload = {"ok": True, **result}
            if encoding:
                payload["encoding"] = encoding
            _print_json(payload) if wants_json else _human_log_import(result)
            return 0
        if args.command == "deck":
            if args.deck_command == "import":
                text, source_kind, source_name, encoding = _read_deck_input(args)
                result = import_deck(
                    db_path,
                    text,
                    deck_id=args.deck,
                    source_kind=source_kind,
                    source_name=source_name,
                    source_encoding=encoding,
                )
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_deck_import(result)
                return 0
            if args.deck_command == "show":
                result = show_deck(db_path, args.deck)
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_deck_show(result)
                return 0
            if args.deck_command == "compare":
                result = compare_deck_versions(
                    db_path,
                    args.deck,
                    from_version=args.from_version,
                    to_version=args.to_version,
                    as_of=args.as_of,
                    show_changes=args.show_changes,
                )
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_deck_compare(result)
                return 0
            if args.deck_command == "version-evidence":
                result = version_evidence(db_path, args.deck, as_of=args.as_of)
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_version_evidence(result)
                return 0
            if args.deck_command == "link-candidates":
                try:
                    result = list_link_candidates(db_path, args.deck)
                except sqlite3.DatabaseError as exc:
                    raise ValueError(
                        "La base locale ne peut pas être lue; le détail technique est caviardé."
                    ) from exc
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_link_candidates(result)
                return 0
            if args.deck_command == "link-battle":
                try:
                    result = confirm_battle_version(
                        db_path,
                        args.deck,
                        args.battle_id,
                        args.version,
                        apply=args.apply,
                        confirm_owner=args.confirm_owner,
                        battle_date=args.battle_date,
                    )
                except sqlite3.DatabaseError as exc:
                    raise ValueError(
                        "La base locale ne peut pas être modifiée; le détail technique est caviardé."
                    ) from exc
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_attestation(result)
                return 0
            if args.deck_command == "unlink-battle":
                try:
                    result = revoke_battle_version(
                        db_path,
                        args.deck,
                        args.battle_id,
                        apply=args.apply,
                        confirm_owner=args.confirm_owner,
                    )
                except sqlite3.DatabaseError as exc:
                    raise ValueError(
                        "La base locale ne peut pas être modifiée; le détail technique est caviardé."
                    ) from exc
                payload = {"ok": True, **result}
                _print_json(payload) if wants_json else _human_attestation(result)
                return 0
            local_root = (root / "data" / "local").resolve()
            if not local_root.is_relative_to(root.resolve()):
                raise ValueError("Le dossier data/local résolu sort de la racine PokeMind.")
            disposable_roots = tuple(local_root / name for name in ("test-runs", "demo-runs"))
            private_decks_root = (
                db_path.resolve().parent / "decks"
                if args.db and any(db_path.resolve().is_relative_to(path) for path in disposable_roots)
                else local_root / "decks"
            )
            if args.deck_command == "candidate-create":
                changes_path = args.changes.resolve()
                if not changes_path.is_relative_to(local_root):
                    raise ValueError("Le fichier de changements doit rester sous data/local.")
                result = create_candidate(
                    db_path, changes_path, apply=args.apply, confirm_owner=args.confirm_owner
                )
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(f"Candidat: {result['status']}; mode={result['mode']}; version jouée inchangée.")
                return 0
            if args.deck_command == "candidate-show":
                result = show_candidate(db_path, args.candidate)
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(f"Candidat {args.candidate}: {result['status']}; cycle={result['lifecycle_status']}.")
                return 0
            if args.deck_command == "candidate-export":
                result = export_candidate(
                    db_path, args.candidate, private_decks_root,
                    apply=args.apply, confirm_owner=args.confirm_owner,
                )
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(f"Export candidat: mode={result['mode']}; chemin={result['text_path']}.")
                return 0
            if args.deck_command == "copy":
                result = copy_ready_file(args.path, private_decks_root)
                payload = {"ok": True, **result}
                if wants_json:
                    _print_json(payload)
                else:
                    print(f"Texte importable copié: {result['path']}")
                return 0
            if args.deck_command == "export":
                prepared = export_confirmed_deck(db_path, args.deck, private_decks_root)
            else:
                proposal_path = args.proposal.resolve()
                if not proposal_path.is_relative_to(local_root):
                    raise ValueError("La proposition doit rester sous data/local.")
                prepared = prepare_proposal(proposal_path, private_decks_root)
            copied = False
            if args.copy and prepared.report["status"] == "READY_TO_TRY_UNVERIFIED_FORMAT":
                copy_text_to_clipboard(prepared.text)
                copied = True
            result = _prepared_payload(prepared, copied=copied)
            payload = {"ok": True, **result}
            _print_json(payload) if wants_json else _human_deck_prepared(result)
            return 0
        result = (
            profile_summary(db_path, args.deck)
            if args.profile_command == "summary"
            else profile_review(db_path, args.deck)
        )
        payload = {"ok": True, **result}
        _print_json(payload) if wants_json else _human_profile(result, review=args.profile_command == "review")
        return 0
    except (FileNotFoundError, ValueError, OSError, sqlite3.DatabaseError) as exc:
        if args.command == "battle" and args.battle_command == "coach":
            from pokemind.battle_coach import CoachError
            code = str(exc) if isinstance(exc, CoachError) else "COACH_LOCAL_DATA_UNAVAILABLE_OR_UNSAFE"
            message = "Coach arrêté : " + code
            if code == "COACH_PLAYER_REQUIRED":
                message += ". Premier lancement : battle coach --player VOTRE_JOUEUR; ce choix restera local."
            _print_json({"ok": False, "status": "BLOCKED_WITH_REASON", "error_code": code}) if wants_json else print(message, file=sys.stderr)
            return 2
        if args.command == "battle" and args.battle_command in {"batch-report", "legacy-plan"}:
            from pokemind.legacy_bridge import BridgeError
            code = str(exc) if isinstance(exc, BridgeError) else "BRIDGE_UNAVAILABLE_OR_INVALID"
            _print_json({"ok": False, "status": "BLOCKED_WITH_REASON", "error_code": code}) if wants_json else print("Consultation arrêtée : " + code, file=sys.stderr)
            return 2
        if args.command == "battle" and args.battle_command == "batch-intelligence":
            code = str(exc) if str(exc).startswith("BATCH_") and len(str(exc)) < 100 else "BATCH_BLOCKED"
            error = {"ok": False, "status": "BLOCKED_WITH_REASON", "error_code": code}
            _print_json(error) if wants_json else print("Lecture du lot arrêtée : " + code, file=sys.stderr)
            return 2
        if args.command == "meta" and args.meta_command == "public-identity-explain":
            from pokemind.public_deck_preflight import identity_explain_error
            error = identity_explain_error(exc)
            if args.html:
                from pokemind.public_deck_preflight import html_identity_explain
                print(html_identity_explain(error=error))
            elif wants_json:
                _print_json({"ok": False, "status": "BLOCKED_WITH_REASON", **error})
            else:
                print(f"BLOCKED_WITH_REASON [{error['error_code']}]: {error['error']}", file=sys.stderr)
            return 2
        error = public_error(exc)
        advisor_blocked = args.command == "meta" and getattr(args, "meta_command", "") in {
            "competitive-inventory", "competitive-compare", "competitive-shortlist", "competitive-preflight", "deck-knowledge", "deck-library", "counter-plan", "learning-simulate",
        }
        advisor_blocked = advisor_blocked or (args.command == "battle" and getattr(args, "battle_command", "") in {"opponent", "matchups", "review-selected"})
        if args.command == "meta" and getattr(args, "meta_command", "") == "competitive-preflight":
            from pokemind.public_deck_preflight import MISSING_EVIDENCE
            error["missing_evidence"] = MISSING_EVIDENCE
        if wants_json:
            _print_json({"ok": False, **({"status": "BLOCKED_WITH_REASON"} if advisor_blocked else {}), **error})
        else:
            label = "BLOCKED_WITH_REASON" if advisor_blocked else "Erreur"
            print(f"{label} [{error['error_code']}]: {error['error']}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
