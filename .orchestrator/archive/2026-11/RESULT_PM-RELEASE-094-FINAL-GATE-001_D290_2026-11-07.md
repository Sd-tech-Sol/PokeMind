# RESULT — PM-RELEASE-094-FINAL-GATE-001 : candidat PokeMind 0.9.4 complet, testé, non publié (D-290), 2026-11-07

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (`f8ee810`, activé
`e5b9504`). Statut : **IMPLEMENTED / REPORTED; AWAITING_CHATGPT_AUDIT**. `RELEASE_READY` : **non** (audit indépendant
et GO distinct du propriétaire requis). **STOP pour audit ChatGPT.**
Rapport précédent (D-289) : [archive/2026-11/RESULT_PM-COACH-LOSS-PRIORITY-001_D289_2026-11-06.md](archive/2026-11/RESULT_PM-COACH-LOSS-PRIORITY-001_D289_2026-11-06.md).

## Commits (branche privée `work/pm-v1-lotj-final-readiness-windows`)
- Prévol : `git fetch` + `git pull --ff-only` de `5296647` à `e5b9504`, arbre propre, aucune divergence.
- Code, tests, docs publiques : **`fae10da`** (`fae10daa7e4ad4cb1476a979c27b7a458e686836`), poussé; HEAD distant vérifié identique.
- Rapport : commit suivant (ce fichier, HANDOFF, NEXT_ACTION, NEXT_PROMPT consommé, STATE, DECISIONS D-290, archive).
- Dépôt public `Sd-tech-Sol/PokeMind` : **inchangé** (`main` = `5629ae2` = `v0.9.3`, vérifié par `git ls-remote`; aucun
  commit web du propriétaire depuis 0.9.3). Aucun tag, aucune release, aucune installation chez le propriétaire.

## 1. Audit local des changements 8570613, 358a551, 6cb86c4, 5ee8c45
| Commit | Relu | Constat |
|---|---|---|
| `8570613` branding D-286 | diff + artefacts | Carte originale intacte (SHA-256 `30824d84…f0f5` recalculé). Icône du nouvel EXE et du nouveau Setup : **9/9** entrées du `.ico` présentes dans le PE (`pefile`, script local). Carte visible dans la fumée gelée. |
| `358a551` consentement D-287 | diff | Défauts `cloud_consent=True`, `sharing='aggregates'` = ordre du propriétaire. **Défaut trouvé** : README/PRIVACY disaient encore « rien n'est envoyé sans ton accord », et l'assistant de premier lancement ne montrait pas le partage choisi. Corrigé (§2). |
| `6cb86c4` saisons, decks D-288 | diff | `added_on` dans le rapport affiché, `seasons.day_of` le lit : vérifié aussi dans l'EXE gelé installé (partie collée comptée dans « Saison actuelle · Delta Reign », n=1). « Ajouter mon deck » : création seule, `source='owner'`. **Défaut trouvé** : point d'audit `owner_main_deck.export` (§2). |
| `5ee8c45` défaites D-289 | diff + flux | Garde **côté hôte** confirmée : `deck_save_allowed = explicit_save or not log_followup`, `candidate_allowed = explicit_save`; `SAVE_REQUEST` est appliqué aux **seuls mots du propriétaire** (`ingestion.split_message` sépare le journal, non fiable, de la question). Aucun journal ne peut donc ouvrir l'écriture par son contenu. `loss_watch` dérivé du rapport, aucun stockage. Aucun défaut. |

## 2. Défaut corrigé (test reproducteur d'abord)
**Point d'audit `owner_main_deck.export`** : avec « + mes statistiques anonymes », la **liste complète** du deck principal
partait au coach à **chaque** question, alors que les autres decks personnels ne partent que si la question parle de
deck/liste (`private_decks_allowed`), et que l'UI parlait seulement de « statistiques anonymes ».
- Test `test_the_main_deck_list_follows_the_personal_deck_gate_and_the_consent_text_says_so` : **échouait** sur `e5b9504`.
- Correctif minimal (`services.prepare_question`) : le nom du deck principal part toujours; la liste seulement si la
  question parle de deck ou de liste (même règle que « Mes decks »), sinon `export_withheld` explique pourquoi.
  « Comment battre X avec mon deck? » et « Améliore ma liste » gardent la liste : la capacité « mon deck » est conservée.
- Contrat affiché fidèle : `SHARING_HINT` (une seule source) sous « Ce que le coach reçoit » dans Réglages et dans
  l'assistant de bienvenue, + ligne « Ce que le coach reçoit » dans son résumé; PRIVACY.md et README FR/EN disent que
  l'envoi cloud est **pré-coché** (D-287) et ce que contient chaque niveau de partage.

## 3. Version 0.9.4 cohérente
`src/pokemind/__init__.py`, `pyproject.toml`, README FR/EN (statut et « Limites exactes »), CHANGELOG `[0.9.4] —
unreleased (release candidate)`, ROADMAP, SECURITY, `docs/RELEASE_NOTES_0.9.4.md` (EN/FR). **Défaut trouvé** :
`PokeMind.exe` n'avait **aucune** ressource de version (propriétés Windows vides) et Setup pas de `FileVersion`.
Ajouts : `scripts/make_version_info.py` (`--version-file` de PyInstaller), `VersionInfoVersion` /
`VersionInfoProductVersion` dans `PokeMind.iss`; test `tests/test_version_metadata.py` (une seule version partout).
Vérifié sur les binaires : EXE `FileVersion=ProductVersion=0.9.4`, `pokemind.__version__` de l'archive PYZ = `0.9.4`;
Setup `FileVersion=ProductVersion=0.9.4`, nom `PokeMind-Setup-0.9.4.exe`.

## 4. Tests
- **Porte locale complète VERTE** sur l'arbre de `fae10da` : compilation, hygiène Git, **Qt 119 passés**, **cœur 1624
  passés / 0 échec / 3 ignorés** (569 s). Régressions D-286 à D-289 incluses (tests de branding Qt, `test_seasons`,
  tests « Ajouter mon deck / deck principal », `test_loss_watch` 11).
- **Export public dry-run** : voir §7.
- Pas de CI GitHub (retirée le 2026-11-01, D-271) : la porte locale n'est pas une CI.
- **Écart de procédure à signaler** : un test ciblé a été lancé une fois directement dans le dépôt (`pytest -k main_deck`),
  contrairement à AGENTS.md; son dossier temporaire `data/local/test-runs/<uuid>` est supprimé par le fixture; aucune
  donnée personnelle lue. Tous les autres essais sont passés par `scripts/local_gate.py`.

## 5. Binaires candidats (locaux, hors Git, non signés, non publiés)
| Artefact | Emplacement | Empreinte |
|---|---|---|
| EXE (797 fichiers) | `build/exe-upgrade-963e73678bc64dbd90d2588bd3293a61/dist/PokeMind/` | `PokeMind.exe` SHA-256 `E03C5BA696EE61E46F737508C29B613A671DE2A62200C302472C234D8E90490D` |
| Installateur | `dist/installer-candidate-0.9.4-fae10da/PokeMind-Setup-0.9.4.exe` (37,9 Mo) | SHA-256 `5DE0D9EF96B6014310AFDC7A02C210B16CFF5DF33E0E29FC239ACDE14E16EAC6` (+ `.sha256`) |
| Preuves QA | `dist/installer-candidate-0.9.4-fae10da/qa/` | rapport JSON, captures `smoke-093/094.png`, diff du script QA |

Construits depuis l'arbre propre de `fae10da` (`Build-PokeMindDesktop.ps1 -StagingRoot`, `Build-PokeMindInstaller.ps1`).
Signature : **absente** (déclarée, `CODE_SIGNING.md`). `dist/PokeMind` et la copie installée du propriétaire (`6cb86c4`) : **non touchées**.

## 6. Windows : installation, mise à niveau, désinstallation isolées; HTTPS; confidentialité
- **Isolation** : pas de Windows Sandbox sur ce PC. L'installateur de production a le même AppId que l'installation du
  propriétaire (clé de désinstallation et raccourci partagés) : il n'a **pas** été exécuté. Deux installateurs **QA** ont
  été compilés avec le même `.iss` dont seuls AppId, `AppName`, `UninstallDisplayName` et noms des raccourcis changent
  (« PokeMind QA »; diff conservé) : charge **0.9.3** = la distribution 0.9.3 conservée (`dist/PokeMind-before-branding-…`,
  `__version__` 0.9.3 lu dans son PYZ), charge **0.9.4** = le candidat. Dossiers d'installation et de données dans le
  dossier temporaire de la tâche, données **inventées** (une défaite collée, un doublon refusé, un deck entré par le
  propriétaire marqué principal), `POKEMIND_DATA_ROOT` explicite, proxy fermé (aucun réseau).
- Résultats (`qa-install-report.json`) : installation 0.9.3 QA (code 0) → fumée gelée **0** (fenêtre visible, plateforme
  `windows`, rapport, deck 60, galerie, **7 pages**, terminal) → mise à niveau 0.9.4 (code 0; fichiers installés =
  exactement la distribution 0.9.4, ancien `_internal` remplacé; 11 fichiers de données inventées **identiques**) →
  fumée **0** (mêmes contrôles, version 0.9.4) → raccourci QA pointe vers l'EXE installé → désinstallation (code 0 :
  clé, raccourci et 0 fichier programme restants; **données identiques**). Clé de désinstallation et raccourci du
  propriétaire : **identiques avant/après** (version 0.9.3, même date).
- **HTTPS** (pile TLS du build : `_ssl.pyd`, `libssl-3.dll`, `libcrypto-3.dll` de `_internal`, OpenSSL 3.0.21; code
  PokeMind de `fae10da`) : `app_update.check` sur l'API GitHub (`AVAILABLE 0.9.3` depuis 0.9.2, `CURRENT` depuis 0.9.4),
  dernier commit TCGdex et `api.tcgdex.net/v2/en/sets` OK; certificats expiré, auto-signé et mauvais hôte (badssl.com)
  **refusés** (`SSLCertVerificationError`). Le risque des DLL OpenSSL de Qt (D-286) est sans effet : PokeMind n'utilise
  pas QtNetwork. Requêtes publiques seulement, rien de personnel.
- **Scans** : `scan_binary_personal_paths.py --require-archive` sur la distribution : `CLEAN` (797 fichiers, 320 modules
  PYZ); refus des fichiers personnels du script d'installateur passé. Le Setup est compressé (lzma) : son scan direct
  n'est pas probant; c'est la distribution qui est contrôlée avant compilation.

## 7. Export public (dry-run, sans push)
`scripts/export_public.py` vers un dossier temporaire hors dépôt : `EXPORTED`, 663 fichiers, arbre `2db1f27` **identique**
à `fae10da`, 1 commit « PokeMind 0.9.4 » (auteur public noreply), **aucun remote, aucun push**.
Porte complète dans l'export (`python <export>/scripts/local_gate.py`) : **VERTE**, Qt 119 passés, cœur 1624 passés / 0 échec / 3 ignorés.

## 8. Matrice des 9 critères
| # | Critère | Verdict | Preuve |
|---|---|---|---|
| 1 | Journal collé : V/D/inconnu, doublon, Saison/Cumul, journal malformé | **PASS (synthétique)** | `test_loss_watch` (WIN→LOSS→doublon→WIN exacts), `test_desktop_ingestion` (incomplet/ambigu/contradictoire refusés, rien compté), Qt `test_incomplete_and_ambiguous_pastes…`, `test_seasons`; EXE gelé : saison actuelle n=1 |
| 2 | Aucun deck adverse auto; `loss_watch`; coach | **PASS hôte** / qualité des réponses **NON TESTÉE** (modèle réel) | garde hôte relue (§1), tests `save_deck`/`save_candidate` refusés, contexte `loss_watch` testé |
| 3 | Deck Lab : import 60, refus précis, deck principal, rien détruit | **PASS** | tests Qt 1318/1347, `test_loss_watch` (2 fichiers conservés); EXE gelé : deck 60 + galerie |
| 4 | Confidentialité, consentement fidèle | **PASS après correctif** | §2; journal jamais vers moteur à shell (Qt `test_a_pasted_log_never_reaches_the_project_engine…`); scans CLEAN |
| 5 | Branding | **PASS** (haute densité / thème clair : tests Qt et captures de D-286, non recapturés) | PE 9/9 EXE et Setup; captures fumée |
| 6 | Windows : autonome, 7 pages, HTTPS, reprise | **PASS** / coach dégradé : **tests Qt seulement** | §6; fermeture puis réouverture sur les mêmes données (0.9.3 puis 0.9.4) |
| 7 | Installateur : version, mise à niveau, désinstallation, SHA-256, non signé | **PASS (variante QA)** / Setup de production non exécuté (même AppId que le propriétaire) | §5, §6 |
| 8 | Porte complète, export dry-run, sécurité, docs FR/EN | **PASS** (voir §7 pour l'export) | §4, §7; CI désactivée |
| 9 | `release-checklist.md` | **PASS** | sections A faites; B/C/D non exécutées (GO requis) |

## 9. V1 complète
| Fonctionne (prouvé ici, synthétique) | Non prouvé | Bloquant | Hors périmètre |
|---|---|---|---|
| import/doublon/saisons, Deck Lab, gardes d'écriture, consentement, version, EXE installé, mise à niveau, désinstallation, HTTPS | parties réelles du propriétaire; réponses d'un vrai Codex/Claude; Setup de production sur une vraie 0.9.3; mise à jour silencieuse `/RELAUNCH` (dernière preuve D-283, chemin inchangé); 125 % et thème clair dans l'EXE | **aucun bloquant technique démontré**; publication = GO propriétaire après audit | signature de code, macOS/Linux, CI |

## 10. Résiduel et validation humaine
- `scripts/qa_unified_desktop.py` (QA de release synthétique) **non exécuté** : il attend 6 pages (l'application en a 7)
  et envoie des messages inventés aux **vrais** comptes Codex/Claude. À réparer dans un mandat distinct si on le garde.
- Anciens decks adverses nommés autrement restent « Mon deck » (limite D-289).
- Défaut de partage = cloud + statistiques (décision D-287) : désormais dit clairement, mais toujours activé par défaut.
- Validation humaine à faire après audit : installer `PokeMind-Setup-0.9.4.exe` par-dessus la vraie installation,
  coller un vrai journal (défaite puis victoire), vérifier Saison/Cumul, « Ajouter mon deck », le texte de Réglages ›
  Coach IA, une question « contre quoi je perds le plus? », et Réglages › Mises à jour.

## Données
Aucune lecture de `data/local` (hors le dossier temporaire de test signalé au §4), de `%LOCALAPPDATA%\PokeMind`, de
journaux, decks, conversations ou secrets réels. Seuls la clé de désinstallation (version) et la date du raccourci du
propriétaire ont été lus, pour prouver qu'ils restent inchangés.
