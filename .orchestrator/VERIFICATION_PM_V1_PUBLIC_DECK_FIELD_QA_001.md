# Audit indépendant ChatGPT — PM-V1-PUBLIC-DECK-FIELD-QA-001

**Date : 2026-10-23 (Québec). Verdict : `VERIFIED_GITHUB_CODE_CI_SYNTHETIC_SCOPE_ONLY`.**
Ce verdict valide le code et les preuves de CI synthétiques, **pas les caches PUBLIC du PC ni la légalité des cartes ni la V1**. `NOT_RELEASE_READY` demeure.

## Git, périmètre et sécurité du dépôt
- Branche `work/pm-v1-lotj-final-readiness-windows`. Base [`b7b1e0d`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/b7b1e0d7d37cb6de39c32ffc7b2a7e240618861a), livraison [`c4d50ee`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/c4d50ee68fac1d173a70a9abe102192f7eea20cd). Comparaison officielle GitHub : **1 commit en avance, 0 en retard, 14 fichiers** (nouveaux `scripts/qa_public_decks.py`, `tests/test_public_deck_field_qa.py`, guide, rapport; correctif ciblé `deck_knowledge.py`).
- Tree Git complet : **429 entrées, non tronqué**; sous `data/local/`, seulement `.gitkeep`, aucun SQLite, journal, export brut ou image privée versionnée dans cet arbre.
- D-211 consigne que le propriétaire a accordé à l'exécuteur **lecture seule** des registres/pages PUBLIC référencés, en plus des deux SQLite explicitement connues. Cette autorisation n'est ni accès aux données personnelles ni autorisation de GET/installation.

## CI indépendante à SHA exact
- [Actions 40020962088](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40020962088), `completed/success`, SHA `c4d50ee68fac1d173a70a9abe102192f7eea20cd`.
- **Windows** job 120645100225 : **1066 passed / 2 skipped** (OCR non attesté).
- **Ubuntu** job 120645099823 : **1065 passed / 3 skipped** (2 OCR, 1 essai Windows-junction réservé à Windows).
- **9 marqueurs présents dans chacun des deux journaux**, tous au SHA/run de livraison : `selected_match_review_evidence`, `counter_learning_evidence`, `deck_library_matchup_evidence`, `deck_knowledge_evidence`, `public_deck_preflight_evidence`, `competitive_advisor_evidence`, `competitive_pages_evidence`, `rules_registry_evidence`, `ci_evidence`.
- Les deux empreintes SHA-256 JSON canoniques des registres sont égales Windows/Ubuntu : `6039ba349a5dcb3a0af605fb2b2834108a0c5c58b1fb5e1b610ea22cf996b7ba` et `330790df14d7d5474503d04b31c29c36eddd1ba8b003736271ab82704f55e3d7`. SHA bruts différents sous CRLF/LF, sans nouvelle certification réglementaire.
- Suite finale CI sur code livré + **15 nouveaux tests synthétiques** par rapport à la précédente (Windows 1051→1066, Ubuntu 1050→1065). Les 15 tests réels du PC annoncés par Codex ne sont pas mesurés par GitHub, seulement les fixtures CI.

## Inspection du code et des preuves
- `_roles` de `deck_knowledge.py` traite maintenant séparément chaque effet/phrase. Le correctif vise deux erreurs confirmées par Codex : fausse perturbation sur condition mentionnant l'adversaire, suppression erronée d'une pioche permise à cause d'une limite dans une autre phrase. Les tests inventés couvrent effets indépendants, négations ASCII et typographiques, noms non probants, recherche et vraie perturbation. Ce système demeure **un classificateur heuristique**, pas un interpréteur complet du Pokémon TCG.
- Nouveau script de QA `qa_public_decks.py` : **seuls deux chemins DB PUBLIC explicites**; validation marqueurs, sidecars et registre `requests.json` PUBLIC; pages adressées par empreinte depuis le registre, sans découverte de répertoires; fingerprints avant/après, relecture des listes et identité de composition, exports60, fiches, légalités séparées, contres conditionnels. Les limites TOCTOU contre un autre processus hostile restent non démontrées.
- Tests synthétiques du nouveau script : 6 placements/4 compositions inventées, non-mutation, interdiction de découverte et réseau, source manquante, détection d'une modification du marqueur, commandes CLI humaines/JSON/export sous démarrage `CP1252` et décodage UTF-8 strict. Les tests GitHub certifient **ces fixtures**, pas l'ouverture des caches locaux du propriétaire.
- Guide `docs/PUBLIC_DECK_FIELD_QA.md` lu : sélection manuelle PUBLIC, Dragapult conditionnel, sources/dates, état `unknown` Live/présentiel, copie manuelle. Aucun winrate ni légalité fabriqués.

## Observations locales : déclaratives
**`CODEX_LOCAL_REPORTED` uniquement** : 2 événements, 32 placements, 28 compositions, 32 exports60, 626/698 lignes sourcées, 1439/1680 copies résolues; 10 identités distinctes manquantes (7 MEE, 3 30C), 28/28 légalités `unknown` sur présentiel et Live, quatre cibles Counter×4 options, 52 fichiers PUBLIC inchangés, zéro GET, 15 CLI terrain, absence de lecture privée. GitHub **ne peut pas confirmer indépendamment** les lectures, octets, 0 GET ou la non-mutabilité réelle des fichiers du PC. Les sources publiques de tournois ne prouvent pas le résultat des matchups ni la légalité actuelle.

## Verdict et suite
**Lot accepté**, portée code GitHub/tests CI/fixtures exclusivement; aucune régression bloquante manifeste détectée dans cette portée. `D-196` permet de préparer le prochain lot de **preuves d'identité/normes PUBLIC hors ligne, synthétique et borné**, mais interdit toujours toute lecture réelle de partie, deck joué, collection, compte, OCR, OS, sauvegarde, installation, suppression, provider GET et merge sans autorisation. V1 reste `NOT_RELEASE_READY`.
