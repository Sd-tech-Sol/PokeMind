# RESULT — PM-DECKLAB-PUBLIC-STATS-001 : Deck Lab › Statistiques publiques par archétype (D-291), 2026-11-07

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (`3c71b6a`, activé
`42ccd84`). Statut : **IMPLEMENTED / REPORTED; AWAITING_CHATGPT_AUDIT**. Cible **0.9.5**, non publiée, non installée.
La 0.9.4 candidate (`fae10da`, audit source ChatGPT `3f89a01` : VERIFIED_SOURCE, NOT_RELEASE_READY) n'est pas modifiée :
aucun binaire 0.9.4 touché, aucune build, aucune version changée (`pokemind.__version__` reste 0.9.4).
Rapport précédent (D-290) : [archive/2026-11/RESULT_PM-RELEASE-094-FINAL-GATE-001_D290_2026-11-07.md](archive/2026-11/RESULT_PM-RELEASE-094-FINAL-GATE-001_D290_2026-11-07.md).
**STOP pour audit ChatGPT.**

## Commits (branche privée `work/pm-v1-lotj-final-readiness-windows`)
- Prévol : `git fetch` + `git pull --ff-only` de `90bd600` à `42ccd84`, arbre propre, aucune divergence.
- Code + tests + CHANGELOG/PRIVACY : **`3a56023`**, poussé. Rapport : commit suivant (ce fichier, HANDOFF,
  NEXT_ACTION, NEXT_PROMPT consommé, STATE, DECISIONS D-291). Le renommage pur (0 ligne) de l'ancien RESULT vers
  l'archive, déjà indexé, est parti dans le commit de code. Dépôt public : inchangé.

## 1. Audit avant code (composants réutilisés)
| Composant | Constat | Usage |
|---|---|---|
| `batch_public_research.research_matchups` | Collecteur API Limitless existant, cache quotidien `chat-matchups.json`, campagne PUBLIC marquée, `meta_budget=8`, **1 tournoi par campagne**, garde le dernier `valid_campaign`. | Réutilisé tel quel + `force` (Actualiser) et `error` (code du refus) dans le reçu. |
| `meta.LimitlessApiClient` / `sync_meta` | Sans clé, borné, 429/5xx, `Retry-After`, quota annoncé, annulation; `/games/{id}/decks` refusé; pseudos/listes non conservés (HMAC). Filtres PTCG/STANDARD/PTCGL/en ligne/public. | Inchangé (vrai client dans les tests, seul l'opener HTTP est inventé). |
| `meta.meta_tournaments/meta_archetypes/meta_matchups` | Byes/doubles défaites exclus (`eligible`), doublon inversé = même `match_key`, mode BO1/BO3 par phase, Wilson 95 %. **Pas de taux global** ni de dédoublonnage entre bases. | Réutilisés par base de campagne; fusion des comptes sur tournois disjoints dans le nouveau module. |
| `competitive.py` (cache limitlesstcg.com) | Tournois **physiques**, top placements sélectionnés, ≤ 3 événements, **aucun pairing** : aucun taux calculable. | Non mélangé (autre population); ses étiquettes servent seulement de preuve d'archétype pour une référence PUBLIC. |
| `window._decks / deck_selected`, `services.deck_options`, `charts.CountChart` | Sélection de deck = source de vérité; barres Qt accessibles clavier existantes. | Troisième onglet; `CountChart` généralisé (séries, non cliquable, texte vide). |

Conclusion : les caches existants permettent **réellement** part des placements classifiés, taux par mode et matchups
**pour la population PTCGL en ligne**; pas pour les tournois physiques. Aucune bibliothèque ni dépendance ajoutée.

## 2. Livré
- `src/pokemind/deck_public_stats.py` (nouveau) : garde de rafraîchissement, dédoublonnage des instantanés, identification
  deck→archétype, vue hors ligne. Détail des règles : D-291.
- `services.deck_pokemon` (noms anglais des impressions exactes via le catalogue PUBLIC, local) et
  `services.deck_public_stats(row, refresh)`.
- `desktop/insights.project_public_stats` (textes FR/EN, aucun chiffre sans n ni source), `charts.PublicStatsPanel`.
- Deck Lab : onglets **Galerie · Liste texte · Statistiques** (défilant). Lecture hors ligne d'abord; si aucune tentative
  aujourd'hui, **une** actualisation automatique en arrière-plan; jeton + clé du deck contre les mélanges; annulation à
  la fermeture; thème clair/sombre et mouvement réduit propagés.
- Affiché : archétype + nature de la preuve; représentation (population de tournois); taux de victoire du mode choisi
  (V/D/N, n, IC 95 %, miroirs exclus); barres de matchups (V/D/N) avec description texte par barre; méta publique
  générale; évolution datée par tournoi (≥ 2 tournois); exclusions (byes, doubles défaites, non publiés); source + doc
  officielle; population et fenêtre; plage des tournois; **dernière synchronisation (date de récupération ≠ date des
  matchs)**; dernière tentative et son résultat.
- CHANGELOG « Unreleased — 0.9.5 » et PRIVACY (nouvel accès réseau décrit).

## 3. Audit explicite des chiffres (tests `tests/test_deck_public_stats.py`)
Un **oracle indépendant** recompte V/D/N par adversaire à partir des pairings bruts inventés (24 joueurs, 5 rondes en
round-robin + un bye, une double défaite, un match listé deux fois inversé, un miroir) :
- matchups `{adversaire: [V, D, N]}` du code = oracle exactement; taux = V/(V+D+N) = 20/37 (54 %), IC Wilson contient
  le point; miroirs (1) hors taux; byes = 1 et doubles défaites = 1 dans les exclusions; doublon compté une fois;
- représentation BO1 = 8/22 (24 placements, 22 classifiés), BO3 = 2/4 → **pas de pourcentage** (< 20);
- BO3 (n = 2) jamais fusionné avec BO1, taux non affiché (< 20); pourcentage d'un matchup nul si n < 10;
- deux instantanés du même tournoi → compté une fois (`duplicate_snapshots_skipped = 1`); tournoi hors fenêtre de
  28 jours ignoré; aucun instantané → `NO_SNAPSHOT`, aucun taux.
Exemple réel de rendu vérifié (capture locale non versionnée) : « Représentation (tournois BO1) : 36 % (8 / 22) ·
Taux de victoire BO1 : 54 % (IC 95 % 38–69 %) · 20 V / 12 D / 5 N · n=37 ».

## 4. Réseau, confidentialité, robustesse (prouvés par tests)
- Cache du jour → **zéro requête** (autres decks, changement d'onglet, sélection rapide); jour suivant → 1 tentative.
- Actualiser : trop tôt (< 10 min) → refus sans requête; ≤ 2 par jour puis `REFRESH_DAILY_LIMIT`.
- Hors ligne / 429 (arrêt au **premier** refus, code `PUBLIC_SOURCE_HTTP_429_BLOCKED`) / JSON invalide → dernier
  instantané identique, date de dernière synchro inchangée, tentative étiquetée, pas de nouvel essai le même jour.
- Annulation avant le premier GET → zéro requête, `INTERRUPTED`.
- URL émises = exactement `/api/games`, `/api/tournaments`, `/api/tournaments/{id}/details|standings|pairings`; aucune
  ne contient le nom du deck ni une carte de la liste privée; aucun fichier JSON écrit ne contient de nom de carte
  ni de pseudo.
- Identification : nom du deck ignoré (« Gammaroo secret » identifié Alphamon Betadrake par sa liste); tech à 1
  exemplaire ignoré; égalité → `AMBIGUOUS` (candidats listés, aucun taux); étiquette publique non corroborée refusée.
- Qt (`tests/test_desktop_workflow_qt.py`, 2 parcours) : onglet non montré → aucune requête; 1 collecte à l'ouverture;
  changement de deck/onglet → 0; trois sélections rapides → la vue est celle du dernier deck; lecture clavier ↑/↓;
  bouton Actualiser borné; thème clair; bascule EN/FR; source refusée sans instantané → texte honnête, aucune boucle.

## 5. Porte locale
`python scripts/local_gate.py` sur l'arbre final (copie temporaire hors dépôt, hors ligne, offscreen) :
**PORTE LOCALE : VERTE — compilation OK, hygiène Git OK, tests Qt 121 réussis, tests du cœur 1634 réussis / 0 échec / 3 ignorés (arbre final avant le retrait d'un prénom dans une chaîne de fixture; après ce retrait, porte ciblée `-k "deck_public_stats or deck_lab_statistics"` VERTE : Qt 2, cœur 10)**.
Note de méthode : deux sélections de tests ont d'abord été lancées directement dans le dépôt pendant le développement
(écart à AGENTS.md); `data/local/test-runs` vérifié ensuite sans résidu daté d'aujourd'hui. La preuve est la porte ci-dessus.

## 6. Limites honnêtes
1. Collecteur existant = **1 tournoi PTCGL en ligne par campagne** (souvent le plus récent, parfois le même d'un jour à
   l'autre) : l'échantillon grossit lentement; il est affiché tel quel (k tournois, n, fenêtre), jamais « mondial ».
2. Tournois physiques : aucun taux possible avec les caches existants (pas de pairings); non affichés.
3. Identification (b) = indice par noms de Pokémon; archétypes dont le nom n'est pas fait de Pokémon (« … Box »,
   « Control ») non reconnus par (b). Pas de choix manuel d'archétype (non indispensable, à décider).
4. Rondes suisses et top cut d'un même mode additionnées (même tournoi, même format); phases listées dans la vue.
5. Taux = matchs (BO1 ou BO3 publiés), pas parties; nuls au dénominateur; adversaires non classifiés exclus.
6. Aucun essai réseau réel contre Limitless dans cette session (tests sur serveur inventé, conformément au mandat);
   le comportement réel de l'API (noms d'archétypes, plateforme `PTCGL`) repose sur le client existant.
7. Aucune build ni installation; réception Windows du propriétaire à faire après audit.

## Prochaine action unique
**Audit indépendant ChatGPT de `3a56023`** (D-291). Ensuite seulement : build candidat 0.9.5 en staging isolé et
réception propriétaire, chacun sur GO distinct. La 0.9.4 reste en attente de réception/GO propre.
