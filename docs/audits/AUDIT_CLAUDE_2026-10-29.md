# Audit indépendant PokeMind — revue Claude Code (lecture seule)

- **Date :** 2026-10-29 (Québec)
- **Dépôt :** `Sd-tech-Sol/PokeMind` (privé), branche `work/pm-v1-lotj-final-readiness-windows`, HEAD `ac27b1e`
- **Portée :** code source (`src/`, `tests/`, `scripts/`, CI), orchestration (`.orchestrator/`), état GitHub/CI. **Aucun fichier du projet modifié**, aucune lecture de `data/local/`, aucun lancement de l'EXE, aucun appel à un fournisseur IA.
- **Exécution :** suite de tests complète relancée sur un **clone propre du HEAD** dans un dossier temporaire (fixtures synthétiques, hors ligne, `QT_QPA_PLATFORM=offscreen`, comme la CI).

> Destinataire : Codex (exécuteur) et ChatGPT (auditeur). Ton : celui d'un relecteur senior. Le but est de rendre le produit meilleur, pas de gagner un débat. Chaque constat cite le fichier et la ligne. Si tu (Codex) n'es pas d'accord, réponds avec une preuve (test, mesure, ligne de code), pas avec un nouveau rapport.

---

## Suivi d'exécution (mis à jour par Claude Code)

| Point | État au 2026-10-29 |
|---|---|
| P0-2 CI économe + porte locale `scripts/local_gate.py` | **Fait** |
| P0-3 deux tests Qt rouges | **Fait** (bouton qui renvoie le texte à la ligne; test de rendu indépendant du lissage) |
| §7 journal de diagnostic + bouton « Copier le diagnostic » | **Fait** (`pokemind/diagnostics.py`) |
| M-1 discovery qui re-parse tout | **Fait** (cache par identité de fichier) |
| M-2 rechargement à chaque question | **Fait pour le rapport**; `public_context` reste à faire |
| M-3 rendu du chat O(n²) | **Fait** : 203 ms → 4,9 ms par rafraîchissement (100 messages) |
| A-1/A-2 prompt natif + AGENTS.md/CLAUDE.md en mode dev | **Fait** |
| A-3 lecture tronquée en silence | **Fait** (pagination `offset`, `truncated`) |
| A-4 commandes/fichiers invisibles | **Fait** (commande, code, extrait de sortie, fichiers modifiés) |
| §8 orchestration allégée | **Fait** (archives dans `.orchestrator/archive/2026-10/`) |
| EXE du propriétaire à jour | **Fait** : source `397fb50`, smoke figé sur fixture inventée, ancien dossier conservé; réception propriétaire en attente |
| A-7 coach avec outils, parité Codex/Claude/Ollama | **Fait en partie** (D-259) : mêmes outils pour les trois moteurs, recherche de cartes jouables, `validate_deck` réparé, légalité présumée datée; le contexte collé reste à réduire |
| P0-1, A-5/A-6/A-8, M-4, S-1/S-2/S-5/S-8, §9 | À faire — voir `.orchestrator/NEXT_ACTION.md` |

## 0. Verdict en une minute

| Axe | Note | Résumé |
|---|---|---|
| Rigueur données/sources | **Très bon** | Séparation faits/hypothèses, `n` partout, pas de taux de victoire inventé, provenance datée. C'est la grande force du projet. |
| Sécurité défensive du code | **Bon, mais mal placé** | Beaucoup de gardes (anti-lien dur, anti-redirection, plafonds de taille, JSON durci). Mais le plus gros risque est **structurel** : tes données privées vivent *dans* le dépôt de dev où un agent avec shell travaille. |
| Mémoire vive / performance | **Faible** | Chaque chargement réanalyse **tous** les rapports historiques; chaque message du coach recharge tout; le chat se ré-affiche en entier toutes les 40 ms pendant la génération. |
| Chat / agent intégré | **Faible** | Le mode « développement » enlève volontairement à Codex et Claude ce qui les rend bons en terminal (prompt système natif, AGENTS.md/CLAUDE.md, outils natifs, affichage des diffs, approbations). D'où ton impression « ça marche, mais c'est pas efficace ». |
| Tests / CI | **Moyen** | Suite complète relancée : **1 545 réussis, 2 échecs Qt, 3 ignorés** — le moteur est solide. Mais **aucune CI verte depuis le 2026-10-26**, et toutes les fonctions visuelles récentes n'ont jamais passé la CI. |
| Maintenabilité | **Faible** | Fonctions de 400 à 900 lignes, lignes de 250+ caractères, aucun linter, aucun journal de diagnostic. |
| Processus (orchestration) | **Trop lourd** | 3,1 Mo de docs d'orchestration pour 1,75 Mo de code; 357 commits `docs` pour 75 `feat/fix`. Le protocole coûte plus cher que le produit. |
| Prêt pour public | **Non** | Licence « Propriétaire », données dans le dépôt, chemin d'EXE codé en dur, crochets de QA dans le code de production, aucun journal, aucune doc d'installation pour un tiers. |

**En une phrase pour Codex :** le moteur est sérieux et honnête, mais l'app enveloppe ce moteur sans cache, sans journal et dans le mauvais dossier, et le chat de dev a été « sécurisé » au point de perdre l'intelligence de l'agent. La prochaine étape n'est pas plus d'animations : c'est **données hors du dépôt, chargement incrémental, et un vrai mode agent**.

---

## 1. Ce qui est bien fait (à garder)

1. **Honnêteté épistémique** : `SYSTEM` (`src/pokemind/assistant/provider.py:20`) et le contexte (`desktop/services.py:220+`) imposent `n`, couverture, « inconnu », pas de causalité. Rare et précieux.
2. **Lecture SQLite en lecture seule correcte** : `connect_readonly` utilise URI `mode=ro` + `query_only` (`database.py:30-38`).
3. **Réseau défensif** : redirections refusées, Ollama limité à `127.0.0.1` sans proxy (`provider.py:229-240`), plafonds de taille sur flux.
4. **JSON durci** : clés dupliquées refusées, NaN refusés, plafond de profondeur/nœuds (`legacy_bridge.py:69-94`).
5. **Écritures atomiques** (`tmp` + `fsync` + `os.replace`) et détection de modification concurrente (`assistant/sessions.py:39-52`).
6. **Journal brut jamais envoyé au cloud** par défaut, classification locale avant tout envoi (`desktop/ingestion.py:classify`).
7. **Hygiène Git** : `.gitignore` large, script `check_repo_hygiene.py`, aucun fichier `.sqlite`, `.env` ou `data/local/*` dans tout l'historique (vérifié : seul `data/local/.gitkeep`).
8. **Dépendances épinglées** et minimales (PySide6, pytest, PyInstaller seulement).
9. **~1 550 cas de test (929 fonctions), cœur 100 % vert** sur clone propre, dont beaucoup testent des cas hostiles (sessions malveillantes, URL distantes, etc.).

---

## 2. P0 — À corriger avant toute nouvelle fonctionnalité

### P0-1. Les données privées vivent dans le dépôt de développement
- `data/local/` (DB, journaux, conversations, rapports) est **dans** le dossier Git; l'EXE est dans `dist/` du même dépôt et retrouve le projet par `Path(sys.executable).parents[2]` (`desktop/app.py:33`).
- Conséquences :
  - Le mode « développement » du chat donne un shell à Codex/Claude **dans ce même dossier** (`project_relative='.'` par défaut). L'interdiction de lire `data/local` n'est qu'**une phrase dans le prompt** (`provider.py:33`) et une règle `Read(./data/**)` que `Bash` contourne (`cat data/local/...`). Le code l'admet lui-même (`provider.py:97-98` : « not an OS security boundary »).
  - Un simple `git clean -fdx` (commande banale pour un agent) **efface toutes tes données** puisqu'elles sont ignorées par Git.
  - Les tests écrivent dans `data/local/test-runs` (`tests/conftest.py:16`) — juste à côté de ta vraie base, avec un `shutil.rmtree` en sortie.
  - Impossible à publier tel quel : un utilisateur public n'a pas de « dossier de projet ».
- **Correctif attendu :** répertoire de données utilisateur séparé (`%LOCALAPPDATA%\PokeMind\` via `QStandardPaths.AppDataLocation`), configurable, avec migration **copiée** (jamais déplacée) et validée par le propriétaire. Tests sur `tmp_path` de pytest uniquement. L'EXE devient indépendant du dépôt.

### P0-2. La CI ne vérifie plus rien depuis 3 jours
- Dernier run vert : **2026-10-26** (`2e28b33`). Depuis : 67 échecs / 58 annulations, tous « budget Actions épuisé, zéro étape ». Pokédex, animations, statistiques, FR/EN : **jamais passés en CI**.
- Cause principale : chaque commit `docs:` (la majorité) déclenche Ubuntu **et Windows** (minutes Windows ×2) sur un dépôt privé.
- **Correctif attendu :**
  ```yaml
  on:
    push:
      branches: ["work/**"]
      paths-ignore: [".orchestrator/**", "docs/**", "**/*.md"]
  ```
  + Windows seulement sur PR ou sur `workflow_dispatch`; + un script local `scripts/gate.ps1` (compile + suite complète) exécuté **avant** push, dont la sortie est résumée dans RESULT. Arrêter d'écrire « CI AWAITING_EVIDENCE » à chaque commit : ce n'est pas une preuve, c'est un constat d'absence de preuve.

### P0-3. Deux échecs Qt sur clone propre (voir §6)
- Codex rapporte « 160 tests distincts verts ». La suite complète fait ~1 550 cas et Codex n'en exécute qu'un sous-ensemble choisi. Sur clone propre au HEAD, en mode CI (`offscreen`) : **cœur 100 % vert, mais 2 tests Qt rouges** que la sélection de Codex n'a pas fait ressortir.
- **Règle à adopter :** un mandat n'est « livré » que si **la suite entière** passe localement (pas une sélection), avec le compte exact `passed/failed/skipped`.

---

## 3. Mémoire vive et performance (ta plainte principale)

### M-1. Chaque chargement analyse TOUS les rapports historiques — `battle_coach.py:114-146`
`_discover()` appelle `legacy_bridge.saved_report()` **sur chaque** `analysis-*.json` du dossier (jusqu'à 5 000 fichiers / 256 Mo) juste pour trouver le plus récent. Chaque appel : lecture complète (≤ 32 Mo), `json.loads`, re-sérialisation canonique pour le SHA-256, copie `_snapshot`, copie `_display` (récursive, regex sur chaque chaîne), puis rendu texte complet `human_report`. Comme les rapports sont immuables et jamais supprimés, **le coût grandit à chaque actualisation**, pour toujours.
- Puis `Services.load()` (`desktop/services.py:65-90`) rappelle `saved_report` sur le gagnant, **une deuxième fois** avec le learning, et `match_index()` (`desktop/ingestion.py:19-31`) relit et re-hache **encore** le même rapport. Pic mémoire ≈ plusieurs copies complètes du rapport en même temps.
- **Correctif :** `latest.json` existe déjà (`battle_coach.py:170`) → l'utiliser comme pointeur; ne valider le hash que du fichier choisi; ranger par nom/mtime sans parser. Un seul parse, une seule projection, mise en cache tant que le fichier ne change pas (stat).

### M-2. Chaque question au coach recharge tout — `desktop/window.py:1635`
Dans `send_chat → ask()`, `self.services.load(False, …)` est appelé **à chaque message** (donc M-1 à chaque message), puis `prepare_question` peut appeler `public_context()` (`battle_batch.py:174-204`) qui charge **toutes les traductions de cartes Pokémon** du catalogue en dictionnaires Python, sans cache.
- **Correctif :** cache en mémoire invalidé par signature `(chemin, taille, mtime)`; `public_context` mémoïsé par `(as_of, mtime des caches publics)`.

### M-3. Le chat se reconstruit en entier toutes les 40 ms pendant la génération — `desktop/window.py:173, 1373-1392, 1730-1738`
Chaque delta relance un timer de 40 ms qui appelle `render_chat()`, qui reconstruit le HTML de **toute** la conversation (jusqu'à 500 messages, avec regex/markdown sur chacun) puis `setHtml` → nouveau `QTextDocument` complet. Coût O(n²) pendant une réponse longue, beaucoup d'allocations Qt. De plus `content += text` sur une chaîne longue est quadratique.
- **Correctif :** n'ajouter que le **dernier** bloc (`QTextCursor` à la fin, ou un widget par bulle dans un `QListView` virtualisé); accumuler les deltas dans une liste et joindre au `chat_done`.

### M-4. L'actualisation réanalyse tout l'historique de parties — `battle_batch.py:531-581`
`batch_analyze` relit, re-segmente, re-parse et ré-analyse **tous** les journaux à chaque actualisation, et garde `accepted` (texte brut + objet parsé de chaque partie) en mémoire jusqu'à la fin. Les IDs `M0001…` dépendent de l'ordre → instables quand un fichier s'ajoute.
- **Correctif :** analyse incrémentale par `semantic_identity` (déjà calculé!) stockée en SQLite; ne parser que les nouveaux; ID stable = hash sémantique.

### M-5. `PRAGMA integrity_check` complet à chaque préflight — `battle_batch.py:161-164`
Scan complet de la base à chaque lot. Utiliser `quick_check`, et `integrity_check` seulement sur demande ou après sauvegarde.

### M-6. Bâtiments de build
`build/` = 1,4 Go, `dist/` = 815 Mo (chaque livraison conserve la distribution précédente complète de 788 fichiers). Prévoir une rotation (garder N=2) **sur décision du propriétaire**.

**Priorité mémoire :** M-1 + M-2 + M-3 règlent l'essentiel de ce que tu ressens. Ce sont des changements localisés, sans toucher au moteur.

---

## 4. Chat / agent intégré : pourquoi c'est moins bon que Codex dans PowerShell

Ton souhait : « travailler sur le projet dans la fenêtre directement, comme dans le terminal ». Le code actuel fait l'inverse : il prend Codex/Claude et leur enlève leurs forces.

### A-1. Le prompt système natif est **remplacé** par 10 lignes
- Codex : `'baseInstructions': system` (`assistant/codex_app_server.py:242`) remplace toutes les instructions de base de Codex (format de patch, usage des outils, style de travail) par `AGENT_SYSTEM` (`provider.py:31-40`). `developerInstructions` reçoit **le même texte** en doublon.
- Claude : `--system-prompt SYSTEM/AGENT_SYSTEM` (`provider.py:169, 174`) remplace le prompt Claude Code complet. Il faut `--append-system-prompt`.

### A-2. AGENTS.md / CLAUDE.md volontairement non chargés
- Codex : `project_doc_max_bytes=0` (`codex_app_server.py:183, 245`) → AGENTS.md ignoré, `include_environment_context=false`, skills désactivés.
- Claude : `--setting-sources ''` (`provider.py:169`) même en mode dev → ni CLAUDE.md ni réglages projet.
- Résultat : l'agent dans la fenêtre ne connaît **ni les règles du dépôt, ni l'état `.orchestrator`**. En terminal, il les a.

### A-3. Outil maison moins bon que les outils natifs — `codex_app_server.py:24-31, 46-123`
Le prompt pousse Codex vers `pokemind_project` au lieu de ses outils natifs. Or cet outil :
- lit au maximum **16 000 caractères** sans le signaler (`:102`) → les gros fichiers (`cli.py` 2 077 lignes, `cards.py` 2 135) sont tronqués silencieusement;
- écrit uniquement par **remplacement complet du fichier** (pas de patch) → l'agent doit réécrire 2 000 lignes pour changer une ligne : lent, cher, risqué;
- tronque stdout/stderr à 9 000 caractères (`:80`).

### A-4. L'interface cache ce que l'agent fait
`tool_event` (`desktop/window.py:1667-1677`) n'affiche que « [Outil réel · commandExecution · completed] ». Pas la commande, pas la sortie, pas le **diff**, pas le plan, pas le raisonnement résumé. En terminal tu vois tout.

### A-5. Approbations neutralisées
Mode dev : `approvalPolicy='never'` (`codex_app_server.py:249, 275`) et `--permission-mode dontAsk` / `--dangerously-skip-permissions` côté Claude (`provider.py:169, 178`). Le rappel `approval()` existe dans la fenêtre mais n'est **jamais sollicité**. Tu n'as donc ni le contrôle (approuver une commande) ni la visibilité.

### A-6. Claude relance un processus par message
`claude -p … --resume` (`provider.py:166-181`) : démarrage à froid + rechargement de session **à chaque message**. Utiliser un processus persistant `--input-format stream-json --output-format stream-json`, ou le **Claude Agent SDK** Python (`ClaudeSDKClient`, `system_prompt` preset `claude_code` + `append`, `setting_sources=["project"]`, `can_use_tool` pour de vraies approbations dans l'UI).

### A-7. Le coach Codex gonfle sa propre conversation
Chaque question coach envoie jusqu'à **24–100 Ko de JSON de contexte** collé dans le prompt (`desktop/window.py:1652`, `services.py:420-432`), et le thread Codex les **garde tous**. Après quelques questions, des dizaines de milliers de jetons redondants → lenteur, coût, compaction. L'outil `pokemind_tool` existe déjà (`assistant/tools.py`) : envoyer un contexte minimal et laisser le modèle **tirer** ce dont il a besoin.
- Asymétrie : Claude coach a `--tools ''` (`provider.py:168`) → il ne peut **pas** utiliser `pokemind_tool`. Codex et Claude ne donnent donc pas le même coach.

### A-8. Permissions déduites par regex
`research_allowed`, `candidate_allowed`, `annotation_allowed`, `development_request` (`services.py:381-384`, `assistant/tools.py:31-45`) sont décidés par expressions régulières sur ta phrase. « cherche » déclenche une collecte réseau **avant** l'inférence; « teste ce deck » peut basculer en mode développement selon les mots. Fragile et surprenant.
- **Correctif :** sélecteur explicite dans l'UI (Coach / Recherche web / Développement), ou commandes slash, et le modèle demande via un outil avec confirmation.

### Recommandation architecture pour le mode développement
Deux options, de la plus simple à la plus riche :
1. **Vrai terminal embarqué** (le plus proche de ce que tu veux) : ConPTY via `pywinpty` + `xterm.js` dans `QWebEngineView`, qui lance `codex` ou `claude` **tels quels** dans le dossier projet. Tu as exactement l'expérience PowerShell, dans la fenêtre. Peu de code, aucune réimplémentation.
2. **Client riche** : garder App Server / Agent SDK, mais avec prompt natif + AGENTS.md chargés, outils natifs (apply_patch, shell), affichage des commandes/diffs/plan, et approbations réelles dans l'UI.

Dans les deux cas, P0-1 (données hors du dépôt) est le préalable qui rend le mode dev **sûr** sans dépendre d'une phrase dans un prompt.

---

## 5. Sécurité (autres constats)

| # | Constat | Fichier | Gravité |
|---|---|---|---|
| S-1 | Mode dev workspace : `networkAccess: True` + aucune approbation → un agent influencé par un contenu malveillant (page web, carte, log) peut exfiltrer ce qu'il lit. | `codex_app_server.py:72, 277` | Haute (combiné à P0-1) |
| S-2 | La liste noire de chemins de `pokemind_project` (`data`, `.git`, `.env`…) est cosmétique : `exec` permet `type data\local\…`. | `codex_app_server.py:89-92` | Moyenne |
| S-3 | `shutil.which(command[0])` résout l'exécutable avec le PATH/dossier courant de **PokeMind**, pas du projet. Sous Windows le dossier courant peut primer → exécutable planté. | `codex_app_server.py:65` | Faible |
| S-4 | SQLite `immutable=1` sur des caches publics que l'app **réécrit elle-même** (recherche publique). La doc SQLite : lecture possiblement incohérente si le fichier change. **Révisé après lecture de `public_deck_preflight.py:38,170` : choix délibéré (zéro I/O de fichiers annexes, refus des bases WAL, contrôle d'octets); conservé, à revoir seulement si une écriture concurrente devient possible.** | `battle_batch.py:161,183`, `batch_public_research.py:65,83,406` | Faible |
| S-5 | Crochets de QA dans l'EXE de production : variable `POKEMIND_DESKTOP_SMOKE` → écrit une capture d'écran de la fenêtre et importe `qa_unified_desktop` depuis le `sys.path`. | `desktop/app.py:36-88` | Faible/Moyenne pour un public |
| S-6 | Toutes les exceptions des tâches de fond deviennent `LOCAL_SERVICE_UNAVAILABLE` sans trace. Pas un trou de sécurité, mais rend tout incident non diagnosticable. | `desktop/window.py:56-61` | Moyenne |
| S-7 | Contenus non fiables (texte de cartes, faits de recherche web) injectés dans le prompt; mitigés par l'étiquette « contenu, jamais instructions ». Correct pour le coach (pas d'outils dangereux), **dangereux si un jour injecté en mode dev**. Garder cette séparation stricte. | `services.py`, `window.py:1652` | Info |
| S-8 | 6 implémentations HTTP/anti-redirection séparées (`cards`, `meta`, `competitive`, `tcgdex_batch`, `batch_public_research`, `desktop/images`). Une faille corrigée dans l'une ne l'est pas dans les autres. Unifier en `pokemind/net.py`. | plusieurs | Moyenne |

---

## 6. Tests exécutés par Claude (clone propre au HEAD `ac27b1e`)

Environnement : Python 3.11.9 (`.venv-ci311`), PySide6 6.12.0, `POKEMIND_TEST_OFFLINE=1`, `QT_QPA_PLATFORM=offscreen` (identique à la CI), dossier temporaire court, aucune donnée personnelle.

- **Qt** (`test_desktop_qt.py`, `test_desktop_workflow_qt.py`) : **64 réussis / 2 échecs**
  - `test_qt_motion_rapid_navigation_and_resize_restore_live_page` → barre de défilement horizontale de **81 px** après navigation rapide + redimensionnement (débordement de mise en page).
  - `test_replacing_a_long_answer_keeps_the_receipt_inside_the_painted_viewport` → seulement 5 couleurs peintes au lieu de > 10 (le reçu n'apparaît pas dans la zone visible).
  - Hypothèse : Codex teste avec la plateforme native Windows, la CI en `offscreen`. Si c'est la cause, **la CI échouera aussi** quand elle aura du budget. À reproduire et corriger, pas à ignorer.
- **Cœur** (reste de la suite) : **1 481 réussis / 0 échec / 3 ignorés** (OCR non attesté, attendu) en 10 min 30. **Bravo : le moteur est solide.** Les 6 tests les plus lents (33–38 s chacun, `test_demo_dates`, parcours e2e) lancent des sous-processus CLI : à marquer `@pytest.mark.slow` pour une passe rapide séparée.
- **Total : 1 545 réussis, 2 échecs, 3 ignorés** (929 fonctions de test, ~1 550 cas paramétrés).
- **Observation annexe :** dans un chemin long (≈ 120 caractères), ~10 tests Qt et de nombreux tests cœur échouent avec `WinError 206` (chemin > 260). Les tests imbriquent `data/local/test-runs/<32 hex>/data/local/public-campaigns/…`. Un utilisateur public avec un profil Windows long ou un OneDrive le frappera. Activer la prise en charge des chemins longs n'est pas une solution produit : raccourcir l'arborescence.

---

## 7. Maintenabilité

- **Fonctions géantes** : `cli.main` 886 lignes, `cli.build_parser` 684, `version_evidence` 424, `sync_meta` 371; 53 fonctions > 100 lignes. `desktop/window.py` = 1 835 lignes, une seule classe qui fait tout.
- **Style compressé** : 442 lignes > 140 caractères, 36 > 250; plusieurs instructions par ligne (`stream.write(...); stream.flush(); os.fsync(...)`). Écrit pour économiser des jetons, pas pour être relu par un humain ou un contributeur public.
- **Aucun outil de qualité** : ni `ruff`, ni `mypy`, ni `pre-commit`. Ajouter `ruff` (format + lint) en CI, même en mode permissif au départ.
- **Zéro journalisation** : aucun module n'utilise `logging`. Ajouter un journal local rotatif (`%LOCALAPPDATA%\PokeMind\logs`, 5 × 1 Mo) avec masquage des chemins/noms, et un bouton « Copier le diagnostic » dans Réglages. Sans ça, « j'ai plein d'erreurs » est impossible à trier.
- **Accès à des fonctions privées entre modules** : `legacy_bridge._json`, `_bytes`, `_display`, `battle_coach._discover`, `_control`… utilisés partout. Ces « privés » sont en fait l'API → les rendre publics et documentés, ou créer un module `storage.py`.
- **État partagé entre threads** : `Services` est un seul objet muté par 4 threads du `QThreadPool` (`report`, `research_allowed`, `cancelled`, `selected_match`…) sans verrou (`desktop/services.py:19-31`, `window.py:154-155`). Une actualisation pendant une question peut mélanger les états. Rendre les requêtes immuables (objet `Request` par question).
- **Deux copies de skills** (`.agents/skills` et `.claude/skills`) identiques aujourd'hui; risque de dérive. Une seule source + lien ou script de synchro.

---

## 8. Processus d'orchestration (ChatGPT ↔ Codex)

C'est probablement le point le plus important pour la suite, et il est dit avec respect pour le travail fait.

- **Volume :** `.orchestrator/` + `docs/` = **3,1 Mo** vs **1,75 Mo** de code source. `NEXT_ACTION.md` = 2 912 lignes, `STATE.json` = 2 422 lignes, `RESULT.md` = 2 540, `HANDOFF.md` = 2 417, pour un **seul** mandat actif. 185 fichiers d'orchestration.
- **Ratio de commits :** 357 `docs:` contre 75 `feat:/fix:`. Chaque fonctionnalité génère 3 à 5 commits de rapport/audit.
- **Coût caché :** chaque nouvelle session doit lire des milliers de lignes avant de travailler → contexte brûlé, risque d'erreur de lecture, et **c'est ce qui épuise la CI** (chaque commit docs = run Windows).
- **Le protocole mesure le mauvais signal :** des centaines de lignes répètent « AWAITING_AUDIT, execute_now=false, V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE » mais personne n'a vu que la CI ne tourne plus depuis 3 jours, ni que la suite complète n'est pas verte.
- **Recommandations :**
  1. `NEXT_ACTION.md` ≤ 60 lignes, `STATE.json` ≤ 100 lignes, `RESULT.md` = dernier mandat seulement. Tout le reste → `.orchestrator/archive/AAAA-MM/`.
  2. Un rapport = **un** commit, pas trois (rapport, SHA, CI).
  3. Les preuves = sortie résumée de `scripts/gate.ps1` (suite **complète**), pas des paragraphes.
  4. Un fichier `CHANGELOG.md` lisible par un humain remplace les 50 fichiers `EVIDENCE_*`.
  5. Les audits ChatGPT devraient vérifier **au moins** : suite complète, CI verte, mesure mémoire. Ce sont des faits vérifiables, contrairement à « CODEX_LOCAL_REPORTED ».

---

## 9. Avant une mise en public (liste de contrôle)

- [ ] Données utilisateur hors du dépôt (P0-1) et chemin de données configurable.
- [ ] Licence réelle (`pyproject.toml` dit « Propriétaire ») + vérification des droits sur `source_material/` (4 volumes PDF/Markdown) : **ne pas publier** de contenu dont tu n'as pas les droits.
- [ ] Mentions légales : Pokémon/TCG Live sont des marques de tiers; avertissement « non affilié »; respect des CGU de TCGdex/Limitless (limites de débit, attribution).
- [ ] Historique Git : il est propre de données privées, mais contient des chemins/noms de branche et 3 Mo de rapports internes. Envisager un **nouveau dépôt public** à partir d'un instantané propre plutôt que de rendre celui-ci public.
- [ ] Retirer les crochets QA de l'EXE (S-5), ajouter journalisation (S-6).
- [ ] Installateur ou zip signé, documentation d'installation pour un tiers, désinstallation propre.
- [ ] Clés/jetons : aucune trouvée — garder ainsi; les sessions Codex/Claude restent dans leurs propres outils.
- [ ] `SECURITY.md` (comment signaler une faille), `CONTRIBUTING.md`, CI verte obligatoire sur PR.

---

## 10. Plan proposé (ordre recommandé, un mandat chacun)

1. **CI réparée** : `paths-ignore`, Windows sur PR/dispatch, `scripts/gate.ps1` local; corriger les 2 échecs Qt (+ échecs cœur s'il y en a). *Critère : suite complète verte localement ET en CI.*
2. **Journalisation locale** + bouton diagnostic. *Critère : une erreur volontaire apparaît avec sa trace dans le journal, sans donnée personnelle.*
3. **Mémoire** : M-1, M-2, M-3 (cache de rapport, pointeur `latest.json`, rendu incrémental du chat). *Critère : mesure avant/après (RAM au repos, RAM pendant une réponse longue, temps d'ouverture) sur fixture de 200 parties synthétiques, chiffres dans RESULT.*
4. **Données hors dépôt** (P0-1) avec migration par copie validée par toi.
5. **Mode développement v2** : terminal embarqué (option 1) ou client riche (option 2). *Critère : la même demande donnée dans PowerShell et dans la fenêtre produit un résultat équivalent.*
6. **Coach** : contexte minimal + outils, parité Codex/Claude, mode explicite au lieu des regex (A-7, A-8).
7. **Analyse incrémentale** (M-4).
8. **Allègement de l'orchestration** (§8).
9. Seulement ensuite : nouvelles fonctionnalités visuelles.

---

## 11. Questions directes à Codex (pour le « challenge »)

1. Pourquoi `baseInstructions` remplace-t-il le prompt natif de Codex en mode dev plutôt que d'utiliser seulement `developerInstructions`? Quel gain mesuré?
2. Pourquoi `project_doc_max_bytes=0` en mode dev, alors que le dépôt dépend entièrement d'AGENTS.md?
3. Combien de fois `saved_report()` est-il appelé à l'ouverture de l'app avec 30 rapports historiques? Mesure-le.
4. Quelle est la RAM de l'EXE au repos et après 20 questions au coach? (fixture synthétique)
5. Pourquoi « 160 tests distincts » plutôt que la suite complète (~1 550 cas)? Donne le résultat de la suite complète en `offscreen`.
6. Pourquoi les tests écrivent-ils dans `data/local/` plutôt que dans `tmp_path`?
7. Peux-tu reproduire les 2 échecs Qt de la §6 en `QT_QPA_PLATFORM=offscreen`?

---

*Audit produit par Claude Code (Opus 5.5) en lecture seule. Aucun fichier du dépôt modifié, aucun commit, aucune donnée personnelle ouverte. Les constats de code citent des lignes vérifiables au HEAD `ac27b1e`; les résultats de tests proviennent d'un clone jetable dans un dossier temporaire.*
