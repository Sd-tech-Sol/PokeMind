# VERIFICATION_PM-0004 — audit indépendant ChatGPT (2026-10-11)

## Verdict
**ACCEPTÉ POUR LA FONDATION DU CATALOGUE**, sous réserve explicite d'une couverture **encore très partielle** et de l'absence de réexécution indépendante des tests. Le code de synchronisation bornée, le schéma SQLite 4 et la lecture hors ligne sont présents et cohérents en revue statique. Ne pas qualifier le catalogue de complet, ni les règles/légalité Live/optimisation comme développées.

## GitHub vérifié directement
- Dépôt privé : `Sd-tech-Sol/PokeMind`.
- Branche publiée : `work/pm-0004-catalogue-foundation`; HEAD Codex `b89989ab1097253168c1b863d49ff80c3f26385d`; commit de code `9e566515539183d92a1fd6255f6d8f9c9fbe6419`.
- Base orchestrateur `8e91d2c80312fef3e8c36c7fd72d8ffa4039763d` : 2 commits ajoutés, 16 fichiers changés, pas de divergence.
- Lecture directe `src/pokemind/cards.py`, `database.py`, `cli.py`, `tests/test_cards.py`, README, documentation et rapport Codex; arbre Git complet : **101 entrées, truncated=false**, aucun journal, image, SQLite, sauvegarde ou autre donnée personnelle sous `data/local` dans l'arbre.
- Aucun statut ou workflow CI associé au HEAD n'a été retourné par GitHub; le résultat `83 passed` est **une attestation Codex** non réexécutée indépendamment par ChatGPT.

## Fonctions inspectées
- Catalogue multilingue local : tables `catalog_sets`, `catalog_printings`, `catalog_translations`, `catalog_sync_state`; migration additive schéma 3→4; backup SQLite via `sqlite3.backup()` et tests de rollback.
- Impression identifiée par ID TCGdex et traductions séparées par langue; champs et détails optionnels `NULL` plutôt qu'inventés; FTS5 et repli LIKE, distincts de la recherche des quatre volumes.
- Client TCGdex GET JSON : hôte HTTPS `api.tcgdex.net`, contrôle de redirection, longueur max 8 MiB, budget `--max-requests` comptant tentatives et retries, intervalle, timeout, gestion 404/429/5xx et `Retry-After`.
- Découverte sets/cartes par pages, curseur SQLite transactionnel, détails par petits budgets, reprise/idempotence, statut distinct `present/absent/not_fetched/network_error`. Pas d'envoi de deck, crédit ou combat.
- CLI `cards sync`, `search`, `show`, `coverage`, `resolve-deck`; `sync --dry-run` ne touche ni au réseau ni à SQLite. Le résolveur reste lecture seule et exige concordance code TCG Online + numéro + nom; `unresolved` autrement.
- Tests synthétiques pertinents : migration et rollback, FR/EN, doublons/aliases, langue absente, pagination, panne partielle, quota, idempotence, consultation offline et protection du deck.

## Preuves d'exécution rapportées (non indépendamment reproduites)
- Prévol `73 passed`; livraison `83 passed`, compilation et vérifications Git selon Codex.
- Source réellement appelée en 2 tranches de 8 requêtes, sans erreur signalée.
- Cache local partiel : **221 extensions découvertes, 247 impressions distinctes, 444 traductions**, dont **2 détails EN et 2 détails FR**, 245 impressions sans détails complets. Ces nombres ne sont pas la taille réelle du catalogue TCGdex.
- Base locale schema 4/intégrité `ok` et invariants conservés (4 volumes, 87 sections, 5 combats dont 4 W/1 L, un deck exact 60 cartes version 1), selon Codex.
- Diagnostic lecture seule du deck : 0/26 lignes résolues; résultat prudent et cohérent avec un catalogue très incomplet.

## Réserves et dette technique
1. **Complétude très partielle** : aucune promesse que le catalogue historique est déjà importé. La prochaine étape devra reprendre les pages et détails en requêtes bornées, mesurer couverture par langue et par extension; ne pas faire de collecte massive non contrôlée.
2. **Détection des nouveautés à venir non implémentée** : dans `_sync_index_page`, un scope `completed` n'est plus reconsulté. C'est correct pour le premier passage, mais la future mise à jour quotidienne devra prévoir **un mécanisme explicite de rafraîchissement incrémental sécurisé** (fenêtres, ETag/Last-Modified si API le permet, réouverture de scope ou resynchronisation planifiée), avec tests pour nouvelles cartes/extensions après un index terminé. Ne pas prétendre que la veille quotidienne est déjà possible.
3. Les noms/en-têtes FR/EN peuvent être incomplets ou diverger; les métriques portent sur le cache. Les codes TCG Live doivent être liés aux IDs TCGdex par preuve, non par heuristique forcée.
4. **Légalité, disponibilité et fabrication dans TCG Live restent `unknown`** : TCGdex est le catalogue, pas la source normative des règles, bannissements, rotations et coûts; Pokémon officiel et Limitless restent des sous-tranches futures.
5. La licence MIT déclarée pour le dépôt open-source TCGdex n'autorise pas nécessairement de republier textes, marques ou images protégées. Respecter conditions du fournisseur, provenance; pas de dump dans Git. Aucun scheduler installé.
6. Les deux originaux historiques des journaux de combat manquants demeurent non réanalysés (PM-0003F). Ils ne bloquent pas cette tranche, mais aucune prétention de vérification historique exhaustive.

## Décision de continuation
**PM-0004 fondation acceptée; PM-0004B/PM-0005 non lancées automatiquement.** Recommander une prochaine tranche ciblée pour poursuivre la couverture du catalogue, vérifier la fraîcheur après index terminé et fiabiliser la résolution de codes de sets, avant règles officielles et méta. Toute nouvelle tâche Codex requiert nouvelle branche, `NEXT_PROMPT.md` versionné, tests et audit indépendant. Interface utilisateur reste Codex uniquement; pas d'API distante, de dépense de crédits, de merge ou de tâche Windows planifiée.
