# Matrice d'acceptation — LOT A (2026-10-13)

## Verdict d'exécution

Les chantiers A1 à A5 ont tous été exécutés. Les mécanismes demandés sont livrés,
mais le **contenu mondial** visé n'est pas déclaré complet : le lot est globalement
`PARTIAL_WITH_EVIDENCE` jusqu'à l'achèvement mesuré des données publiques. Ce verdict
ne signifie ni `VERIFIED`, ni V1 terminée.

## État mesuré

- Base privée, consultation seulement : schéma 7, intégrité `ok`, 223 sets, 602
  impressions, 973 lignes de traduction, 13 sources de règles, 1 tournoi/16 matchs.
  Les SHA-256 avant/après `knowledge status` et `knowledge audit` étaient identiques.
- Smoke public isolé sous `data/local/test-runs/`, ignoré par Git : 4 GET TCGdex,
  117 sets, 107 impressions, 200 lignes d'index FR/EN, 0 détail, soit `0/107` détail
  dans chaque langue. Le reste de l'index est inconnu faute de total fournisseur;
  448 GET de détails de cartes/sets découverts étaient exactement comptables.
- Registre neuf chargé dans le smoke : 14 sources (9 `verified`, 2 `non_verified`,
  3 `navigation_only`), 6 assertions vérifiées, 1 règle de structure vérifiée et
  0 équivalence de réimpression vérifiée.
- Refresh Limitless isolé : 4 GET, 1 snapshot public complet, `28/28` placements
  classifiés, `56/59` matchs admissibles et classifiables, BO1; 3 exclusions
  `bye_or_automatic_loss`. C'est un échantillon de plateforme, pas le monde.

## Exigences A1–A5

| Chantier / exigence | Statut | Preuve livrée | Reste explicite |
|---|---|---|---|
| A1 — découverte FR/EN paginée, reprenable, bornée | `DONE` | `cards.py`, états par scope/langue, pagination confirmée, budgets/retries; `tests/test_cards.py` | Aucun mécanisme manquant |
| A1 — métriques observées et dénominateurs honnêtes | `DONE` | `cards coverage`: index, détail, ratios, total visible seulement après scan complet, GET connus/inconnus | Aucun mécanisme manquant |
| A1 — catalogue historique public complet | `PARTIAL_WITH_EVIDENCE` | Smoke `107` impressions; base privée `602`; aucun scan n'est complet et aucun total global n'est publié | Continuer les index puis détails par budgets bornés; afficher x/y seulement quand y existe |
| A1 — priorité deck → Standard → arrière-catalogue sans fuite | `DONE` | Seulement IDs TCGdex exacts; Standard issu d'assertions officielles actives; tests `test_local_deck_priority_sends_only_public_tcgdex_identity` et `test_standard_context_precedes_back_catalog_without_private_values` | Charger davantage de données publiques n'altère pas cette priorité |
| A2 — fiches, alias FR/EN, variantes, provenance | `DONE` | `cards show/search --lang all`, identité d'impression stable, langues/URL/date/champs manquants | Les champs absents du fournisseur restent `unknown` |
| A2 — résolution déterministe Unicode/collisions | `DONE` | NFC + `casefold`, code/numéro/nom exact; tests Unicode, collisions et ambiguïtés | Aucune mutation de deck/inventaire |
| A2 — équivalences de réimpressions vérifiées | `PARTIAL_WITH_EVIDENCE` | `cards reprints ID --as-of`; même nom explicitement refusé comme preuve; `0` assertion vérifiée dans le registre actuel | Cartographier seulement de futures preuves Pokémon officielles aux IDs TCGdex |
| A3 — provenance officielle et temporalité | `DONE` | Registre versionné `pm-lota-1`; 14 URLs auditées accessibles par HEAD au 2026-10-13; fenêtres/source/statut conservés | HEAD prouve l'accès, pas le contenu; 2 PDF demeurent `non_verified` |
| A3 — structure 60/copies/Énergie de base/Pokémon de base | `DONE` | Table additive schéma 9; `rules check-deck`; tests 59/61, >4, sans Basic, exceptions, conflits, fenêtres et source non vérifiée | Aucun verdict global `legal` si une dimension requise manque |
| A3 — exceptions spéciales, Expanded Live, promos, errata, restrictions, réimpressions | `PARTIAL_WITH_EVIDENCE` | Couverture exposée par `rules status`; tri-state conservateur | Registres officiels complets non disponibles/chargés; continuer sans inférence |
| A3 — migration/backup/rollback et données privées | `DONE` | Test 8→9, sauvegarde restaurable, rollback DDL simulé, intégrité; contrôles en lecture seule | Migration de la vraie base volontairement non exécutée dans ce lot |
| A4 — couverture Limitless contextualisée | `DONE` | `meta coverage`: format/plateforme/online/date, fraîcheur, snapshots, ratios, phases/BO, exclusions, biais; aucun winrate | Le mécanisme reste borné à la Tournament Platform publique |
| A4 — couverture mondiale / finalisation normative | `PARTIAL_WITH_EVIDENCE` | 1 snapshot smoke; statut fournisseur exposé comme interprétation `unknown` | Accumuler des snapshots publics datés; ne jamais appeler l'échantillon mondial |
| A4 — Trainer Hill | `BLOCKED_WITH_REASON` | Audit du 2026-10-13 : aucune API publique ni condition d'automatisation vérifiée; aucun scraping | Réévaluer seulement si un accès public autorisé est documenté |
| A5 — `knowledge status/audit` hors ligne | `DONE` | Schéma ancien supporté sans migration, intégrité/FK/FTS5, métriques séparées, actions et quotas prouvés; `tests/test_knowledge.py` | Aucun réseau implicite |
| A5 — questions Codex et guide portable | `DONE` | `.agents/skills/knowledge/SKILL.md`, `docs/AUDIT_CONNAISSANCES.md`, README; recherche/fiche/réimpression/légalité/méta routées | Le validateur officiel du skill était inexécutable sans `PyYAML`; validation frontmatter équivalente réussie |

## Preuves de test

- Baseline avant LOT A : `216 passed`.
- Intermédiaires : A1/A2 `220 passed`; A3 `224 passed`; A5 et modules croisés
  `117 passed`.
- Final : `230 passed in 39.58s`; `python -m compileall -q src tests` réussi;
  `git diff --check` réussi avant la documentation finale.
- Réseau : deux smokes explicitement bornés dans une base temporaire; aucune donnée
  personnelle, image, deck, collection, journal, crédit, HMAC ou identifiant privé
  transmis ou versionné.
- Validation du skill : le script `quick_validate.py` fourni par `skill-creator` a
  arrêté sur `ModuleNotFoundError: yaml`; aucun paquet n'a été installé. Les mêmes
  contraintes applicables (frontmatter, nom, description, absence de TODO) ont toutes
  réussi par contrôle PowerShell, et les parcours CLI sont couverts par pytest.

## Commits fonctionnels

- `07cea71` — A1/A2, découverte, couverture, identité et réimpressions.
- `7e687f6` — A3, structure officielle, schéma 9 et migration.
- `13e204d` — A4, couverture contextuelle du métagame.
- `9f174dd` — A5, audit intégré, skill, guides et tests.

Les sources publiques et leurs limites sont détaillées dans
`docs/LOT_A_SOURCE_AUDIT.md`. Les lots B, C, D et E demeurent intégralement dans le
plan V1 et ne sont pas démarrés par ce lot.
