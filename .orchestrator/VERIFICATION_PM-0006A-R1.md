# VERIFICATION_PM-0006A-R1 — audit indépendant ChatGPT (2026-10-12)

## Verdict
**PM-0006A-R1 ACCEPTÉE EN REVUE STATIQUE INDÉPENDANTE, dans la portée des trois corrections.** La lecture seule du diagnostic local et la politique prudente des preuves sont préservées. Aucun accès à la SQLite privée Windows ni réexécution de pytest par ChatGPT; l'acceptation ne prétend pas certifier le contenu des données locales.

## Références GitHub vérifiées
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0006a-r1-temporal-redaction`.
- HEAD Codex **`a3fd79eada00a26f4fe6cd56be598a333c49e371`**, parent préparé `334644fc4525fdb0ba53b4c6cc9eb6ccbe160c00`. Comparaison GitHub : **un seul commit en avance, zéro retard, 8 fichiers modifiés**. `src/pokemind/analysis.py` et `cli.py`, tests `tests/test_analysis.py`, documentation et relais examinés.
- Arbre Git de la livraison : **128 entrées, `truncated=false`**, aucun chemin SQLite privé, capture, deck/journal réel, sauvegarde ou token détecté; cela ne prouve pas l'absence de tout secret dans chaque contenu ou transmission hors Git.
- GitHub retourne **0 statut CI** et **0 workflow PR associé** à ce HEAD. **181 tests réussis au prévol et 185 tests finaux**, compilation, diff-check, intégrité SQLite 7 et empreinte DB locale inchangée sont **rapportés par Codex uniquement**.
- Aucune fusion, migration SQL, synchronisation publique, achat, scheduler Windows ou accès compte Pokémon déclaré dans la livraison.

## Correctif 1 : temporalité des snapshots Limitless — conforme
- `_meta_fact` ajoute `date(fetched_at) <= date(as_of)` à `date(date_utc) <= date(as_of)` **avant** calcul des tournois, placements, archétypes, matchs, données de provenance et `last_fetched_at`.
- Retourne `snapshot_availability` et le nombre `snapshot_captured_after_as_of`; `analyze_deck` ajoute `SNAPSHOT_NOT_AVAILABLE_AS_OF` et n'ajoute pas de preuve de méta pour zéro tournoi admis. `fetched_at` est explicitement la date de capture locale, non une date officielle de publication.
- Test synthétique : tournoi au 2026-05-01, capture au 2026-06-01, exclu au 2026-05-15 et disponible au 2026-06-02, avec filtre Live/présentiel et tournoi futur séparés.

## Correctif 2 : version future — conforme
- `_deck_fact` expose `historical_applicability=applicable|not_applicable|unknown`, sans substituer la version précédente. Les faits descriptifs de la dernière version restent visibles.
- `analyze_deck` **n'appelle pas** `_rules_fact` pour une version historiquement non applicable et force `rules.status=unknown` avec `LATEST_VERSION_OUTSIDE_AS_OF`. `_battle_fact` supprime les preuves `with_selected_version_proven` pour les combats antérieurs à la version; garde observation séparée `selected_version_not_applicable`.
- Test avec impression synthétique interdite par le moteur normatif autonome, version effective en juin et diagnostic en mai : aucun faux verdict historique `not_legal` ni lien valide de combat à cette version.

## Correctif 3 : messages d'erreur — conforme à la portée
- Les blocs catch catalogue et règles ne sérialisent plus `str(exc)`, mais des messages fixes neutres `CATALOG_UNAVAILABLE` et `RULES_UNAVAILABLE`.
- Tests injectant un chemin Windows, un token et un nom de carte synthétiques dans une `sqlite3.DatabaseError`; absence des fragments en sortie JSON et humaine confirmée par assertions de tests.
- **Limite hors correction :** le traitement d'erreurs imprévues en dehors de ces blocs mérite ultérieurement une politique générale de confidentialité, sans rouvrir R1 sans preuve de risque bloquant.

## Limites permanentes
- Les importations de combat sont datées localement; cela ne reconstitue pas forcément la date de la partie ni une date de publication externe.
- Caches TCGdex, règles officielles et échantillon Limitless demeurent incomplets; l'identité des impressions, la collection, la légalité structurelle et le coût ne sont pas établis. Une reconnaissance de W/L sur cinq combats n'autorise aucun taux de victoire prédictif.
- L'absence d'un workflow CI indépendant et l'impossibilité d'inspecter la SQLite du joueur imposent la distinction entre **revue statique ChatGPT** et **tests Windows déclarés par Codex**.

## Suite
**PM-0006A-R1 clôturable.** Sur le feu vert permanent utilisateur, préparer PM-0006B en tranche bornée : améliorer les preuves de liaison combat↔version, comparer des versions seulement si elles sont fiables et rendre visibles les blocages avant toute recommandation. Aucune attribution rétroactive automatique, aucune modification du deck ou des résultats, aucun merge, achat/crédit, scheduler, action sur compte Pokémon ni publication privée. Codex exécute la nouvelle tranche et s'arrête pour audit.
