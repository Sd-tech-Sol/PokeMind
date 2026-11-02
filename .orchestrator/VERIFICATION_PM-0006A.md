# VERIFICATION_PM-0006A — audit indépendant ChatGPT (2026-10-12)

## Verdict
**PM-0006A LIVRÉE — FONDATION ACCEPTÉE EN REVUE STATIQUE, MAIS CORRECTION CIBLÉE PM-0006A-R1 REQUISE avant VERIFIED complet.** L'analyse du deck, des combats, du catalogue, des règles et du métagame est réellement hors ligne et en lecture seule. Trois défauts de précision/confiance restent, en particulier la datation des instantanés Limitless.

## Preuves directement vérifiées sur GitHub
- Repo privé `Sd-tech-Sol/PokeMind`; branche `work/pm-0006a-evidence-readonly`; commit code Codex `29f6a8968fa636f6f4ba2a0f8628e49b8067ce3c`, HEAD final livré `806c978fa8d4c53cfdaf695b5beb94cfc769cc6e`, base orchestration `7bf90261873e33fef646c44f6e788400ba611882`.
- Comparaison : **2 commits d'avance, aucun retard, 9 fichiers changés**. Nouveau `src/pokemind/analysis.py` (500 lignes), CLI et tests `tests/test_analysis.py` (312 lignes) examinés; documentation et RESULT/HANDOFF/NEXT_ACTION consultés.
- Arbre Git **126 entrées, non tronqué**, aucun SQLite, vrai journal ou deck, backup, secret, image ou contenu personnel sous `data/local/` détecté. Cela ne démontre pas l'absence de toute fuite en dehors de Git.
- **0 statut CI et 0 workflow PR** attachés au HEAD dans les réponses du connecteur. Codex annonce **171 passed au prévol, 181 passed au final**, compilation et diff check, empreinte byte pour byte inchangée de base synthétique, SQLite privée schéma 7 et intégrité ok, conservation des 4 volumes/87 sections, 5 combats et deck exact de 60 cartes : **rapports Codex**, non exécutés indépendamment par ChatGPT.
- Pas de fusion, achat, action sur compte Pokémon, tâche Windows, ni API réelle appelée dans cette tranche selon le code et les rapports.

## Conforme en revue de code
1. `analyze_deck()` valide l'identifiant local, format, plateforme et date ISO stricte; gère la base absente et ouvre la SQLite par `connect_readonly`. Les fonctions composées `cards_coverage`, `resolve_deck_cards`, `rules_status` et `check_deck` sont hors ligne/read-only; aucune mutation ni HTTP dans le nouveau chemin.
2. `_deck_fact` sélectionne la dernière version sans substituer une précédente plus favorable, expose confirmation, total enregistré, somme des quantités et date d'effet. `_battle_fact` ne crédite pas un combat à la version sans ligne `battle_deck_versions`, dédoublonne par hash et sépare W/L/nul/ambigu; le taux/matchup personnel demeure absent.
3. `_catalog_fact` cache les lignes réelles du deck et ne restitue que fractions résolues/ambiguës/inconnues avec dénominateurs. `_rules_fact` conserve le garde-fou `DECK_STRUCTURE_NOT_VERIFIED`, les conditions de légalité et la provenance.
4. `_meta_fact` sépare PTCG, Standard/Expanded, PTCGL/en ligne contre TABLETOP/présentiel, public et snapshots complets; ne fait pas correspondre de façon spéculative un archétype Limitless au deck de l'utilisateur, ni ne calcule de matchup sur zéro données pertinentes.
5. CLI JSON/humain, tests sans DB, deck manquant, dernière version non confirmée, quantités incohérentes, cinq combats, zéro archétype, confidentialité et hash identique : implémentations présentes.

## PROBLÈME 1 — « as_of » ne borne pas la date de disponibilité d'un snapshot Limitless
**`src/pokemind/analysis.py::_meta_fact`, environ lignes 294–306.**
- SQL actuel : `AND date(date_utc) <= date(?)`, **sans** condition `fetched_at <= as_of`. `date_utc` est la date du tournoi, **pas** la date où ses classements/appariements ont été récupérés et connus du cache.
- Cas reproductible : événement daté **2026-05-01**, résultats importés **2026-06-01**, diagnostic **`--as-of 2026-05-15`**. L'analyse signale alors des placements/archétypes « disponibles dans le contexte » malgré une récupération après la date demandée.
- Cela constitue du biais rétrospectif si `as_of` veut dire « preuves connues à cette date ». **R1 :** distinguer `event_through` et `evidence_available_through`, ou filtrer aussi `date(fetched_at) <= date(as_of)` avec raison `LATER_FETCH_EXCLUDED`; si les deux sens temporels doivent être pris en charge, rendre la sémantique explicite plutôt qu'un seul `as_of` ambigu. Tests sur événements antérieurs mais fetch postérieur; cours de journée/date TZ; ne pas modifier le cache.

## PROBLÈME 2 — évaluation réglementaire d'une version postérieure à `as_of`
**`_deck_fact` / `analyze_deck` environ lignes 83–115 et 377–430.**
- La version courante est conservée (bonne décision), et un `LATEST_VERSION_OUTSIDE_AS_OF` est ajouté si sa date d'effet est postérieure à `as_of`. Mais le code appelle quand même `_rules_fact` et `_catalog_fact` sur **ce deck futur** à la date antérieure, pouvant présenter un `not_legal` comme applicable au diagnostic rétrospectif d'un deck qui n'existait pas encore.
- **R1 :** garder la dernière version visible sans choisir une autre, mais signaler explicitement `historical_applicability=unknown/not_applicable` pour cette version et **ne pas présenter une conclusion de légalité ou de performance historiquement applicable**. Tests version effective après `as_of` et réponse réglementaire potentiellement `not_legal`. Les faits statiques du deck peuvent rester consultables si marqués non applicables temporellement.

## PROBLÈME 3 — texte brut d'exception technique dans une sortie censée être caviardée
**`analyze_deck`, blocs `except (ValueError, sqlite3.DatabaseError) as exc` dans catalogue et règles.**
- Le résultat JSON ajoute `str(exc)` au champ `unknowns[].message`, malgré l'exigence de ne jamais exposer chemin local, nom utilisateur ou donnée interne. Certains messages d'erreurs futurs de bibliothèque peuvent contenir un chemin ou une valeur sensible; les tests fournis couvrent le cas normal et la suppression des hashes, **pas ce chemin d'erreur**.
- **R1 :** réponse stable, neutre, sans `str(exc)` ni contenu brut venant de la base; éventuellement diagnostic technique uniquement journalisé localement de manière sûre **sans journaliser de données personnelles**. Injecter une erreur synthétique contenant un chemin/personne/token dans les tests et vérifier l'absence en stdout JSON/humain.

## Portée de la correction
**PM-0006A-R1 :** trois ajustements bornés au diagnostic et à ses tests/docs, sans migration, sans HTTP, sans modifier parties/deck et sans créer de recommandations. Ajouter tests synthétiques sur les limites historiques et les exceptions. Conserver tous les 181 tests précédents rapportés. Si une règle de date ne peut pas être définie sans ambiguïté, privilégier `unknown` et l'expliciter dans le rapport.

Aucune CI/Windows indépendante ni catalogue global/collection complète ne sont démontrés. **Ne pas avancer PM-0006B avant audit de R1.** Feu vert durable de l'utilisateur : préparer automatiquement R1 sur branche distincte, sans « go », Codex exécute ensuite une tâche et s'arrête pour audit GitHub.
