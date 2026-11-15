# RESULT — PM-COACH-LOSS-PRIORITY-001 : défaites suivies, aucune création de deck adverse après une victoire (D-289), 2026-11-06

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (`4b72cdc`, activé
`df2d839`). Statut : **IMPLEMENTED / REPORTED** (pas VERIFIED). **STOP pour audit ChatGPT.**
Rapport précédent (D-286 à D-288) : [archive/2026-11/RESULT_PM-UI-BRAINBALL-BRANDING-002_D286-D288_2026-11-06.md](archive/2026-11/RESULT_PM-UI-BRAINBALL-BRANDING-002_D286-D288_2026-11-06.md).

## Commits (branche privée `work/pm-v1-lotj-final-readiness-windows`)
- Code et tests : **`5ee8c45`** (`5ee8c457f4fa813731b6a57b298018baaaf6f88f`), poussé; HEAD distant vérifié identique.
- Rapport : commit suivant (ce fichier, HANDOFF, NEXT_ACTION, STATE, DECISIONS D-289, archive du RESULT précédent).
- Dépôt public : **inchangé**. Aucune version, aucun tag, aucune installation.

## Audit préalable : vrais points d'entrée trouvés
Flux : journal collé → `ingestion.ingest` (refuse toute issue absente ou contradictoire : seules W/L arrivent) →
`window.ingest_done` → question automatique `LOG_QUESTION` → `Services.prepare_question(log_followup=True)` → outils.
1. `window.LOG_QUESTION` demandait au coach de reconstruire 60 cartes et de **« l'enregistrer dans mes decks »**, quelle
   que soit l'issue, et le chat annonçait « … l'ajoute à Mes decks ».
2. `prepare_question` : `candidate_allowed = SAVE_REQUEST… or log_followup` → `save_candidate` ouvert d'office.
3. Outil `save_deck` : **aucune garde** (décision du 2026-11-02 : pas de mot-clé), et sa description disait « … ou colle un journal ».
4. Prompt du coach (`provider.COACH_SYSTEM`) : « valide… puis enregistre avec operation=save_deck ».
5. Écritures de decks dans le code : **seulement** `Services.save_deck` (« Mes decks ») et `save_candidate`
   (`latest-candidate.json`). `opponent_observer.reconstruct`, l'ingestion et le rapport n'écrivent aucun deck.
6. Statistiques existantes réutilisables : `battle_batch.group_matches` (familles triées par défaites, V/D/inconnu, cartes
   observées, signaux) et `added_on` par partie (D-288). Aucun suivi spécifique des défaites n'existait.

## Ce qui change
| Point | Avant | Après |
|---|---|---|
| Question auto. après journal | « reconstruis… enregistre-le dans mes decks » | `LOG_QUESTIONS['loss']` (famille, suivi, comment préparer) ou `['win']` (bref bilan); aucune n'est une demande d'enregistrement (testé contre `SAVE_REQUEST`); issue inconnue : aucune question |
| Note dans le chat | « … l'ajoute à Mes decks… » | « Défaite ajoutée au suivi des matchups difficiles; aucun deck enregistré. » / « Victoire comptée…; aucun deck adverse enregistré. » / inconnu : « …aucun suivi créé ni deck enregistré. » |
| `save_candidate` | ouvert par tout journal collé | demande explicite seulement |
| `save_deck` pendant le tour d'un journal | toujours permis | refusé `DECK_SAVE_REQUIRES_OWNER_REQUEST` sauf si les mots du propriétaire autour du journal le demandent |
| `save_deck` dans un tour normal | sans mot-clé | inchangé (commande explicite du propriétaire, décision du 2026-11-02) |
| Reconstruction déterministe | à chaque journal | défaite, ou question qui parle du deck |
| Coach | aucun suivi | `loss_watch` dans `context()` et `log_followup` dans le tour du journal |

**`src/pokemind/loss_watch.py` (92 lignes), dérivé du rapport canonique local, sans second stockage** : persistance = le
rapport que chaque import enregistre déjà; aucune table, aucun fichier nouveau, rien d'effacé. Par famille ayant au moins
une défaite : V, D, inconnu, n, part des défaites, `watch` (1 défaite) / `recurring_loss` (≥ 2), 1re et dernière date
de défaite (date d'ajout du journal), cartes vues **dans les défaites seulement**, signaux, incertitude
(n < 5 : « sujet à surveiller, aucune conclusion statistique »), `causal_effect: unknown`. Une famille seulement battue
n'apparaît pas; une victoire contre une famille déjà suivie met son bilan à jour. Portée : toutes les parties, toutes
saisons. Issue lue du côté du propriétaire (`wins`/`losses` du parseur), `unknown` sinon, jamais inférée.

**Confidentialité** : `loss_watch` n'est ajouté qu'avec « + mes statistiques anonymes » (testé absent en public seul);
il contient des noms de familles et de cartes déjà transmis par `matchups`/`selected_match`, des comptes et des dates
de jour; aucun journal brut, nom de joueur ni chemin (testé). Consentement D-287 et permissions des outils inchangés.

**Anciens decks adverses (D-263)** : aucun supprimé ni déplacé. Un deck de « Mes decks » non entré par le propriétaire
dont le nom contient adversaire/adverse/opponent/reconstruit… est listé **après** ses propres decks, type « Deck adverse
reconstruit · référence personnelle, ancien enregistrement du coach », sélecteur « deck adverse · date ».
**Limite** : un ancien deck adverse nommé autrement reste affiché comme « Mon deck »; pas de migration des fichiers.

## Tests (journaux et decks inventés)
`tests/test_loss_watch.py` (10) : victoire/inconnu sans suivi; une défaite sur faible échantillon = `watch`; deux
défaites même famille = une seule entrée `recurring_loss`; WIN→LOSS→WIN→LOSS (bilan 2V/2D, n=4, dates, cartes des
défaites seulement, aucune liste de 60); victoire après suivi existant (mise à jour sans effacement); focus/limite;
défaite collée de bout en bout (suivi, reconstruction, `save_deck` et `save_candidate` refusés, aucun fichier de deck);
victoire collée (pas de reconstruction ni suivi, refus d'enregistrement); WIN→LOSS→doublon→WIN réels (doublon détecté,
2V/1D exacts, une seule famille suivie); demande explicite autour du journal (enregistrement permis) et `save_deck`
d'un tour normal, deck entré par le propriétaire, ancien deck adverse identifié, 2 fichiers conservés; questions
« contre quels decks je perds le plus / comment battre / propose-moi un deck » avec `loss_watch`; mots des questions auto.
Qt : `test_pasted_defeat_alone_is_followed_and_never_saves_the_opponent_deck` (remplace le test qui exigeait
l'enregistrement) et `test_pasted_win_counts_and_the_coach_gets_a_short_review_without_deck`.

**Porte locale complète VERTE** sur l'arbre de `5ee8c45` : compilation, hygiène Git, **Qt 119 passés**, **cœur 1621
passés / 0 échec / 3 ignorés**. Instabilité trouvée et corrigée avant le commit : une passe complète avait échoué sur
un nouveau test qui supposait l'ordre du rapport = ordre de collage (l'ordre suit les noms de fichiers aléatoires);
reproduit 38 fois sur 90 sous charge, le test sélectionne désormais la partie collée comme l'application
(`ingest_done`) : 0/90 ensuite, puis porte complète verte. Aucun défaut produit : l'application sélectionne déjà la partie importée.
Pas de CI GitHub (retirée le 2026-11-01) : la porte locale n'est pas une CI.

## EXE candidat local (hors Git)
`Build-PokeMindDesktop.ps1 -StagingRoot` → `build/exe-upgrade-ae54ac696754469880b235ad091ef6c8/dist/PokeMind/`
(797 fichiers, `PokeMind.exe` SHA-256 `d740219562aefa21…`), depuis l'arbre de `5ee8c45`; `pokemind.loss_watch` présent
dans l'archive PYZ. Fumée gelée (mode autonome, `POKEMIND_DATA_ROOT` synthétique vide, proxy fermé) : fenêtre visible,
plateforme `windows`, 7 pages, terminal disponible; sortie 2 = dossier vide (attendu, comme D-286). **Non installé,
non copié dans `dist/PokeMind`, non publié**; la copie installée du propriétaire reste celle de `6cb86c4`.

## Limites et risques
- L'identification d'un ancien deck adverse repose sur son nom (voir plus haut).
- La famille est celle du rapport (« unknown » si non résolue); deux variantes d'une même famille classées différemment
  par le moteur restent deux entrées.
- Le coach reste un modèle : il peut ignorer la consigne, mais l'écriture est refusée côté hôte dans le tour du journal.
- Aucune donnée personnelle lue, aucun test exécuté dans le dépôt; aucune vérification sur les vraies parties du propriétaire.
