# RESULT — PM-AUDIT-CLAUDE-PLAN : données hors du dépôt (D-264); chat dans le dossier PokeMind par défaut (D-265), 2026-11-01

Exécuteur : Claude Code (Opus 5.5). Autorisation : D-258; ordres du propriétaire en session (« go sort lai », étape 2 du plan,
audit P0-1; puis « que ça rouvre … directement dans le dossier de PokeMind … pour qu'ils suivent les règles du dossier »).
Code : **`5958022e9fe5584e89748de7e41e75173a367776`** (app, D-264), **`574b1445576e4265c3cd1b964d1317c5ac0b0824`** (CLI, D-264),
**`a92e92529c66b4c187f6450cf5790f55d79f1ad4`** (chat, D-265). Session précédente (D-263) :
[archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_D263_2026-10-31.md](archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_D263_2026-10-31.md).

## D-265 — le chat parle à Codex / Claude Code dans le dossier PokeMind, par défaut
Demande : parler dans le chat de l'app « comme si je te parlais à toi dans PowerShell, mais dans PokeMind », Codex et
Claude ouverts directement dans le dossier PokeMind, règles du dossier suivies, tout enregistré là. Le chemin donné
(`dist\PokeMind`) est celui du programme; les règles (`AGENTS.md`, `CLAUDE.md`) et l'historique des sessions sont à la
racine du projet, qui est le dossier utilisé (la page Terminal l'utilisait déjà).
- Réglages : case « Le chat travaille dans le dossier PokeMind », **cochée par défaut** (`chat_project`).
- Question tapée → Codex / Claude démarré dans le dossier de développement (racine du projet par défaut) avec les règles
  du dossier, leurs outils natifs selon le mode (Standard / Accès complet) **et** les outils du coach
  (`PROJECT_SYSTEM` = consignes de développement + consignes du coach). Claude : `--setting-sources project,local`,
  invite système de Claude Code conservée, outils `Read,Edit,Write,Bash,Glob,Grep` + pont MCP du coach, refus de
  `./data/**`. Codex : `AGENTS.md` lu, outils `pokemind_project` + `pokemind_read` + `pokemind_tool`. Question Pokémon :
  contexte PokeMind selon le partage choisi; demande de développement : envoyée telle quelle. Canal `project:<mode>`.
- **Journal collé : jamais vers un moteur doté d'un shell** (texte en partie écrit par d'autres joueurs) → coach isolé,
  comme avant (reconstruction et `save_deck` inchangés). Question personnelle sans partage permis : réponse locale.
  Ollama : coach isolé. Case décochée : comportement précédent.
- Consentement de développement demandé une fois par moteur / mode / dossier (inchangé); consentement cloud exigé.

Preuves : porte locale complète au SHA `a92e925` : compilation et hygiène OK, **Qt 81 passed**, **cœur 1520 passed, 3 skipped**, **1601 réussis, 0 échec**, PORTE LOCALE **VERTE**. Une première exécution complète a donné 18 erreurs de nettoyage (aucun échec de test) : la fixture automatique des tests utilisait `monkeypatch`, défait après `local_tmp`, si bien qu'un test resté dans son dossier (`chdir`) empêchait Windows de l'effacer; corrigé sans `monkeypatch`.
Nouveaux tests : arguments réels de Claude (règles du dossier, invite conservée, outils natifs + outils du coach appelés
par le pont, refus `./data/**`) et paramètres de Codex (`AGENTS.md` lu, trois outils, consignes `PROJECT_SYSTEM`; sans
outils du coach en développement explicite); fenêtre : question Pokémon → dossier du projet, outils du coach, contexte;
demande de code → envoyée telle quelle, même session; journal collé → coach isolé même case cochée; case décochée →
coach isolé; défaut livré coché. Les anciens parcours testent le coach isolé (case décochée dans les tests).
**Essai réel** (dossier jetable dont `AGENTS.md` impose de commencer par TOURNESOL, outils du coach branchés) :
Claude 3 s et Codex 4 s, les deux réponses commencent par « TOURNESOL » : les règles du dossier sont bien lues.
EXE : build depuis `a92e925` (staging neuf, production) **exit 0, 796 fichiers**; **69/69 modules identiques** aux sources, 0 module QA; smoke du vrai EXE sur fixture **inventée** neuve **exit 0**, 7 pages, terminal disponible, 5 bases synthétiques inchangées, `%LOCALAPPDATA%\PokeMind` toujours absent; permutation, application fermée : ancien dossier (796 fichiers) conservé sous `dist/PokeMind-before-project-chat-…`, **796 fichiers installés identiques** au candidat.

## Problème (audit P0-1)
Toutes les données du propriétaire (base, combats, decks, discussions, caches publics) vivaient dans `data/local` du
dépôt : un `git clean -fdx`, une réinitialisation ou un agent pouvait les effacer, et l'EXE n'avait aucun autre emplacement.

## Correctifs
- `src/pokemind/data_location.py` (nouveau) : dossier de données hors du dépôt, `%LOCALAPPDATA%\PokeMind` par défaut,
  même disposition interne (`<dossier>/data/local/...`), donc aucun chemin ni garde existant ne change. Pointeur
  `%LOCALAPPDATA%\PokeMind\location.json` par dossier de projet; `POKEMIND_DATA_ROOT` force un dossier; la QA de
  publication (`POKEMIND_DESKTOP_SMOKE`) ne lit jamais le pointeur.
  - Copie : inventaire sans lecture de contenu (liens et points de redirection refusés), place disque vérifiée, dossier
    partiel neuf, chaque fichier copié en création seule, **SHA-256 relu après écriture**, arrêt si un fichier change ou
    est verrouillé pendant sa copie, renommage seulement quand tout est copié. Échec ou annulation : seul le duplicata
    partiel est retiré, le pointeur ne change pas. **L'original n'est jamais déplacé, modifié ni supprimé.** Une copie
    antérieure n'est jamais écrasée (nouveau dossier daté). `test-runs` (sorties de tests synthétiques) exclu.
- `desktop/app.py` : au démarrage, si le projet contient encore des données, question « Sortir tes données du projet »
  (destination, taille, nombre de fichiers, original intact); sur **Oui** seulement : barre de progression annulable,
  puis « Copie vérifiée : N fichiers » et ouverture sur la copie. Refus mémorisé; échec : message, rien de remplacé,
  copie reproposée. Résultat journalisé (sans chemin ni contenu) une fois le journal installé.
- `desktop/window.py` : la fenêtre distingue le dossier de données (`root`) du dossier du projet (`project_root`) :
  mode développement et page Terminal restent dans le projet, refus de `data/` inchangés. Réglages : « Dossier de
  données » (champ en lecture seule, copiable), état, bouton « Sortir mes données du projet… » ou « Revenir au dossier
  du projet » (effet au prochain démarrage, confirmation pour revenir).
- `tests/conftest.py` : `LOCALAPPDATA` redirigé vers un dossier temporaire pour toute la session de tests (le vrai
  pointeur n'est jamais lu ni écrit par un test). Traductions anglaises des nouveaux textes.

## Complément : le CLI suit le même dossier (`574b1445576e4265c3cd1b964d1317c5ac0b0824`, « oui » du propriétaire)
- `data_location.cli_root` : `python -m pokemind` prend le dossier de données seulement si la copie a été acceptée ou si
  `POKEMIND_DATA_ROOT` est défini; sinon le projet, comme avant. Il ne propose ni ne copie rien et ne liste jamais
  `data/local` du projet pour décider (le parcours de bout en bout, qui interdit tout accès hors fixture, l'a exigé :
  une première version listait ce dossier et a été refusée par son garde).
- `cli.py` : sources d'amorçage (`import-seed`), registre des règles, démo synthétique et prévisualisation du planificateur
  restent lus dans le projet; un chemin privé explicite (sauvegarde, clone, restauration) doit rester sous `data/local`
  dans le projet **et** dans le dossier de données.
- Tests : `status` réel du CLI qui suit la copie acceptée, revient au projet après retour, obéit à `POKEMIND_DATA_ROOT`,
  sans créer de pointeur quand les données sont encore dans le projet; garde des chemins privés sur les deux racines.
- L'EXE installé (`5958022`) n'est pas recompilé : pour l'app, le comportement est identique (seul le découpage interne
  de `resolve` a changé).

Porte locale complète au SHA `574b144` : compilation et hygiène OK, **Qt 78 passed**, **cœur 1517 passed, 3 skipped**,
**1595 réussis, 0 échec** — PORTE LOCALE : **VERTE**.

## Preuves
`python scripts/local_gate.py` (copie hors dépôt, sans `data/local`, hors ligne, Qt `offscreen`) sur l'arbre du code :
| Étape | Résultat |
|---|---|
| Compilation, hygiène Git | OK, OK |
| Tests Qt | **78 passed** |
| Tests du cœur | **1515 passed, 3 skipped (OCR non attesté)** |
| **Total** | **1593 réussis, 0 échec** — PORTE LOCALE : **VERTE** |

Une première exécution complète a montré un échec réel (`test_qt_motion_rapid_navigation_and_resize_restore_live_page`) :
le chemin du dossier de données, sans espace, élargissait la page Réglages (défilement horizontal). Corrigé par un champ
en lecture seule; deux exécutions sur des arbres dépassés ont été arrêtées (processus tués, copies retirées); seule
l'exécution sur l'arbre définitif est retenue.

Nouveaux tests (tout inventé, `tmp_path`) : copie vérifiée fichier par fichier, original identique (SHA-256 avant/après),
dossiers vides gardés, `test-runs` exclu, progression jusqu'au total, pointeur propre à un projet; QA de publication et
`POKEMIND_DATA_ROOT` qui ignorent le pointeur; refus, retour au projet, seconde copie dans un nouveau dossier sans écraser
la première; annulation, fichier verrouillé, place insuffisante et destination dans le projet sans duplicata ni
changement; fichier modifié pendant sa lecture refusé; projet sans données sans proposition; Réglages (bouton, retour
confirmé, champ de chemin); mode développement dans le projet quand les données sont ailleurs; question au démarrage
(refus mémorisé, copie et ouverture sur la copie).

**Essai dans la vraie fenêtre** (projet jetable, 31 fichiers inventés dont un de 64 Mo, `LOCALAPPDATA` redirigé) :
question affichée avec destination, « 67 Mo, 31 fichiers », Oui → progression → « Copie vérifiée : 31 fichiers »;
original de 64 Mo intact, copie de même taille, pointeur « outside »; Réglages montre le nouveau dossier et « Revenir au
dossier du projet ». Captures inspectées puis supprimées avec le dossier jetable.

Mesures sans lecture de contenu sur le PC : `data/local` du propriétaire compte environ 2 560 fichiers et 850 Mo hors
`test-runs` (environ 2 Go de sorties de tests, non copiés); chemin copié le plus long environ 200 caractères (sous la
limite Windows de 260); aucun lien ni point de redirection; `%LOCALAPPDATA%\PokeMind` n'existait pas.

## EXE
- Build depuis `5958022` (staging neuf, paramètres de production) : **exit 0, 796 fichiers, 122 Mio** (même liste de
  fichiers que l'EXE précédent; le « 118 Mo » du rapport D-263 venait d'une autre mesure).
- Archive figée lue sans exécution : **69/69 modules `pokemind.*` identiques** aux sources (dont `data_location`),
  entrée `app` identique, **0 module QA**.
- **Smoke du vrai EXE** sur une fixture **inventée** neuve, seul `POKEMIND_DESKTOP_SMOKE=1` actif : **exit 0**, figé, visible,
  7 pages, rapport, liste exacte 60, galerie, import, activité, terminal disponible; **5 bases synthétiques inchangées**;
  `%LOCALAPPDATA%\PokeMind` toujours absent après le smoke (la QA ne suit ni n'écrit le pointeur).
- Permutation, application du propriétaire fermée (vérifié avant), PowerShell 7 : ancien `dist/PokeMind` (**796 fichiers**)
  conservé intact sous `dist/PokeMind-before-data-location-…`; **796 fichiers installés identiques** au candidat (SHA-256).
  `data/local` jamais ciblé.
- **Retour arrière** (non exécuté) : fermer l'app, renommer `dist/PokeMind` en un nom neuf, renommer
  `dist/PokeMind-before-data-location-…` en `dist/PokeMind`. Si la copie a déjà été acceptée, l'ancien EXE ignore le
  pointeur et relit l'original du projet (les ajouts faits depuis restent dans la copie).

## Non fait / limites
- **La copie réelle n'est pas faite** : elle se fera dans l'EXE du propriétaire, sur son « Oui ». Aucun agent n'a ouvert ni
  copié `data/local` personnel; seuls le nombre, la taille et la longueur des chemins ont été mesurés.
- Les scripts Python autonomes de `scripts/` calculent encore `data/local` du projet (le CLI, lui, suit le dossier).
- L'EXE vit encore sous `dist/` du dépôt et trouve le projet par `parents[2]`.
- La fixture `local_tmp` des tests écrit encore sous `data/local/test-runs` de l'arbre testé (copie de la porte locale sous
  `%TEMP%`, jamais le dépôt); 51 fichiers de tests en dépendent.
- Supprimer l'original ou les sorties `test-runs` du dépôt : décision du propriétaire seulement.
- GitHub Actions : bloqué par le budget; non revendiqué.
