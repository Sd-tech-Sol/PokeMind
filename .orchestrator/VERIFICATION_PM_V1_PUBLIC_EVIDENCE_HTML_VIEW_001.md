# Audit indépendant — PM-V1-PUBLIC-EVIDENCE-HTML-VIEW-001

**Date Québec : 2026-10-23. Verdict : `VERIFIED_GITHUB_CODE_CI_SYNTHETIC_SCOPE_ONLY_WITH_SOURCE_BLOCK`.**
Audit de code et tests synthétiques seulement. **V1 NOT_RELEASE_READY**.

## GitHub et intégrité
- Branche `work/pm-v1-lotj-final-readiness-windows`. Base [`45a5f27`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/45a5f27bb5071c3fe40780beafa04d250ae08caf), [commit `6ceb8e5`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/6ceb8e5e6de38d9b06febbe6647ca72638919b05) : **un seul commit d'avance, zéro retard, 13 fichiers**. Changements circonscrits à `src/pokemind/cli.py`, `src/pokemind/public_deck_preflight.py`, `tests/test_public_evidence_explain_cli.py`, guide HTML et documents orchestrateur. Aucun nouveau service ou dépendance.
- Arbre Git complet : **446 entrées, non tronqué**, `data/local/.gitkeep` seul sous `data/local`; aucune vraie SQLite, image, journal, archive ou autre source locale versionnée.

## CI finale au SHA exact
- [Actions `40055613509`](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40055613509) `completed/success` au SHA `6ceb8e5e6de38d9b06febbe6647ca72638919b05`. Windows job 120757815649 : **1140 passed, 2 skipped**. Ubuntu job 120757815504 : **1139 passed, 3 skipped**. **29 tests supplémentaires** par plateforme depuis `5c53e6d`; aucun échec final.
- **9 marqueurs de preuve hérités dans chacun des deux journaux**, SHA et run exacts, y compris le marqueur texte `ci_evidence`. Hashes JSON canoniques officiels égaux Windows/Linux : `official_rules_2026.json = 6039ba349a5dcb3a0af605fb2b2834108a0c5c58b1fb5e1b610ea22cf996b7ba`; `official_rules_20261022.json = 330790df14d7d5474503d04b31c29c36eddd1ba8b003736271ab82704f55e3d7`.

## Revue fonctionnelle et sécurité
- `meta public-identity-explain --as-of ... [--selector ...] --html` branché dans la CLI avant toute découverte générique de racine ou de base privée; `--html` et `--json` exclusifs. Réutilisation de `identity_explain` et de ses **deux SQLite PUBLIC exactement nommées en lecture seule**; aucune découverte de dossiers et aucun GET ajouté.
- `html_identity_explain` génère **sur stdout** un document HTML autonome UTF-8 avec CSS interne, tableau global/sélection, liens de fragments générés, sections `details/summary` accessibles au clavier, identités et preuves manquantes, avis très visibles `SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE` et `in_person/live = unknown`. Les URLs cache sont affichées comme **texte échappé**, jamais comme requête/attribut navigable. Aucun JavaScript, image ou ressource distante. CSP : `default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'`.
- Revue de `tests/test_public_evidence_explain_cli.py` : 29 nouveaux cas sur fixtures inventées, véritable CLI HTML complète/filtrée, égalité avec JSON, 74 ciblés cumulés rapportés par Codex, XSS et champs hostiles/candidats, fragments internes, CSP et structure clavier, erreur neutre en page HTML, absence de source privée/écriture/réseau, CP1252 → UTF-8. La CI complète certifie **les tests synthétiques**, pas le navigateur sur le PC.

## Limites et décision
- **CODEX_LOCAL_REPORTED**, non vérifiable indépendamment par GitHub : 5 exécutions CLI PC, 32 placements/28 compositions, filtre `581:1` (3 placements, 1 composition, 21/24 lignes et 51/60 copies), fichiers PUBLIC inchangés, zéro GET, aucune donnée personnelle. Aucun HTML écrit ni navigateur ouvert; aucun audit réel `file://`, rendu visuel ou lecteur d'écran effectué.
- Dix identités (7 MEE, 3 30C) restent inconnues, légalités des 28 compositions **unknown** présentiel et Live, sources/pages `BLOCKED_SOURCE_SCOPE`, aucune certification réglementaire/TCG Live. La V1 reste **`NOT_RELEASE_READY`**.

**Verdict : code et CI synthétique acceptés, aucun critère terrain A–J levé.** Suivant D-196, lancer un **nouveau lot synthétique de parcours joueur de bout en bout**, limité aux modules déjà présents et aux fixtures fictives; zéro donnée personnelle réelle, aucun GET, OS ou navigateur, et aucune découverte de fichiers.
