# RESULT — PM-RELEASE-095-WINDOWS-CANDIDATE-001 : candidat Windows PokeMind 0.9.5, isolé, non installé, non publié (D-292), 2026-11-07

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (`8efe909`, activé
`c33cf40`), sur l'audit ChatGPT [`VERIFICATION_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md`](VERIFICATION_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md) (`7f7fcbb`).
Statut : **IMPLEMENTED / REPORTED; AWAITING_CHATGPT_AUDIT**. Pas VERIFIED, pas `RELEASE_READY`.
Rapport précédent : [archive/2026-11/RESULT_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md](archive/2026-11/RESULT_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md).
**STOP pour audit ChatGPT.**

## 0. Prévol
- `git fetch` + `git pull --ff-only` : `1a75bdd` → `c33cf40` (3 commits docs ChatGPT), arbre propre, aucun reset/rebase/force.
- Lus : AGENTS.md, SESSION_CONTINUITY, STATE, NEXT_ACTION, NEXT_PROMPT, HANDOFF, RESULT, DECISIONS, les deux audits,
  `docs/release-checklist.md`, `Build-PokeMindDesktop.ps1`, `Build-PokeMindInstaller.ps1`, `export_public.py`,
  `packaging/PokeMind.iss`, `app.py` (mode fumée), le rapport QA 0.9.4 (méthode AppId QA réutilisée).
- `scripts/qa_unified_desktop.py` **non exécuté** (6 pages attendues, vrais comptes Codex/Claude), comme exigé.

## 1. Commits (branche privée `work/pm-v1-lotj-final-readiness-windows`)
- Code/docs de version : **`24e9cc5`** (`24e9cc5d05b4debc7a3f6c3ad245f3f36cdfb068`), poussé. Aucun changement de
  `src/` hors `__version__`; code de la fonction Statistiques = `3a56023`, inchangé.
- Rapport : commit suivant (ce fichier, HANDOFF, NEXT_ACTION, NEXT_PROMPT consommé, STATE, DECISIONS D-292, archive).
- Dépôt public `Sd-tech-Sol/PokeMind` : **inchangé** (`HEAD` = `v0.9.3` = `5629ae2`, lu par `git ls-remote`). Aucun tag,
  release, PR ni push public.

## 2. Version 0.9.5 cohérente (`24e9cc5`)
`src/pokemind/__init__.py` et `pyproject.toml` 0.9.5; README FR/EN (statut « 0.9.4 jamais publiée », « Limites exactes
de la version 0.9.5 » avec une ligne **Statistiques du Deck Lab** : par archétype, un tournoi récent par collecte, pas de
chiffres mondiaux, aucun pourcentage sous les seuils; Deck Lab et usage réseau); CHANGELOG : une section
`[0.9.5] — unreleased (release candidate)` avec **tous** les changements depuis 0.9.3, `[0.9.4] — never published`;
SECURITY `v0.9.5`; ROADMAP; `docs/RELEASE_NOTES_0.9.5.md` EN/FR (0.9.4 jamais publiée, cumul depuis 0.9.3, seuils,
limites d'échantillon); `RELEASE_NOTES_0.9.4.md` porte « Never published ». PRIVACY déjà à jour (D-291).
Test `tests/test_version_metadata.py` : version unique (app, pyproject, README ×2 statut et limites, SECURITY, CHANGELOG,
notes EN+FR, `.sha256`) + nouveau test « 0.9.4 intégrée à 0.9.5, jamais présentée comme publiée ».
Métadonnées PE (EXE) et Inno (Setup) dérivées de `__version__` par les scripts existants : vérifiées au §4.

## 3. Portes
| Porte | Arbre | Résultat |
|---|---|---|
| `python scripts/local_gate.py` (complète, hors dépôt) | `24e9cc5` (code final) | **VERTE**, code 0 : compilation, hygiène, **Qt 121 passés**, **cœur 1635 passés / 0 échec / 3 ignorés** (512 s) |
| Même porte, 2ᵉ exécution | arbre du rapport (code `24e9cc5` + docs d'orchestration, avant l'inscription de cette ligne) | **VERTE**, code 0 : **Qt 121**, **cœur 1635 / 0 / 3** (507 s) |
| Porte dans l'export public dry-run | export de `24e9cc5` (arbre `d1ab63b`) | **VERTE**, code 0 : **Qt 121 passés**, **cœur 1635 passés / 0 échec / 3 ignorés** (504 s) |
Aucun test lancé directement dans le dépôt. Pas de CI GitHub (D-271) : la porte locale n'est pas une CI.

## 4. Candidat (local, hors Git, non signé, non publié)
| Artefact | Emplacement local | SHA-256 |
|---|---|---|
| Distribution EXE (797 fichiers) | `build/exe-upgrade-f886329deff24c7f853fbcd4f1f0ec35/dist/PokeMind/` | `PokeMind.exe` `7121BBEB277594164621DDEECD6FAA3331FAFFB87EABD55024BB2BD6E0E9E6FF` |
| Installateur (37,9 Mo) | `dist/installer-candidate-0.9.5-24e9cc5/PokeMind-Setup-0.9.5.exe` (+ `.sha256`) | `6E7E5CB2D63FA05BB96123E3A9DF6CFACEB37E90D21C9CD7417564526C0D68CB` |
| Preuves QA | `dist/installer-candidate-0.9.5-24e9cc5/qa/` | rapports JSON, diff `.iss` QA, 5 captures |

- Construits depuis l'arbre propre de `24e9cc5` : `Build-PokeMindDesktop.ps1 -StagingRoot` (staging neuf),
  `Build-PokeMindInstaller.ps1 -DistDir <staging> -OutputDir dist/installer-candidate-0.9.5-24e9cc5`.
- Version : EXE `FileVersion = ProductVersion = 0.9.5`, fixe `0.9.5.0`, `OriginalFilename PokeMind.exe`; Setup
  `FileVersion = ProductVersion = 0.9.5` (Inno complète par des espaces), nom `PokeMind-Setup-0.9.5.exe`; `pokemind.__version__`
  lu dans le PYZ de l'EXE = `0.9.5`; titre et 7 pages dans l'UI gelée; clé de désinstallation QA `DisplayVersion 0.9.5`.
- Icônes : **9/9** images du `.ico` présentes dans l'EXE et dans le Setup (`pefile`).
- PYZ : 321 modules dont 86 `pokemind.*`; **`pokemind.deck_public_stats`**, `desktop.charts`, `desktop.insights` présents;
  `qa_unified_desktop` absent.
- Confidentialité : `scan_binary_personal_paths.py --require-archive` → `CLEAN` (797 fichiers, 321 modules, 0 constat);
  refus des fichiers personnels du script d'installateur passé; aucun `.json/.sqlite/.db/.log/.env` dans la distribution.
- **Candidats 0.9.4 intacts** : `PokeMind-Setup-0.9.4.exe` `5DE0D9EF…6EAC6` et EXE `build/exe-upgrade-963e…` `E03C5BA6…490D`
  recalculés identiques; `dist/PokeMind` non touché.

## 5. Fumées sur l'exécutable gelé (données inventées, isolées)
Environnement de chaque lancement : `POKEMIND_DATA_ROOT` = root synthétique du dossier temporaire de la tâche; `PATH`
réduit à System32/Windows/PowerShell, `APPDATA`/`LOCALAPPDATA`/`TEMP` redirigés vers un bac à sable (Codex et Claude
**introuvables**, `%LOCALAPPDATA%\PokeMind` jamais ouvert); proxys HTTP(S) fermés (`127.0.0.1:9`); préférences
synthétiques : mises à jour et illustrations désactivées. Processus enfants surveillés pendant chaque lancement : **aucun**.
Roots : deux journaux inventés (`SAVED` puis `DUPLICATE`), un deck inventé « Ajouter mon deck » (`SAVED_DECK`), et pour
A/C/D un instantané public **fictif** collecté par le vrai collecteur avec le serveur inventé des tests (en mémoire,
5 « GET » jamais sortis du PC), contrôle du jour déjà enregistré → aucune tentative automatique possible.

| Fumée | Résultat |
|---|---|
| Mode fumée intégré (`POKEMIND_DESKTOP_SMOKE=1`), EXE du staging | code **0** : gelé, fenêtre visible, plateforme `windows`, rapport, deck 60, galerie, **7 pages**, terminal |
| UI Automation, **FR / thème sombre**, Deck Lab › **Statistiques** | onglets `Galerie · 60/60`, `Liste texte`, `Statistiques`; « Archétype public : Alphamon Betadrake — correspondance par les Pokémon de ta liste (indice…) … pas de tes 60 cartes exactes »; « Taux de victoire BO1 : 54 % (IC 95 % 38–69 %) · 20 V / 12 D / 5 N · n=37 matchs admissibles (miroirs exclus : 1) »; représentation 36 % (8/22, 1 tournoi); source Limitless + docs, fenêtre 28 j, « date de récupération, pas date des matchs »; matchups 19/13/5. **Égal à l'oracle indépendant** des tests (20/12/5, n=37, miroir 1, 19/13/5). Fichier de contrôle **identique** après (aucune tentative réseau). Fermeture code 0. |
| UI Automation, **EN / thème clair**, root sans instantané | `Statistics`, `Refresh`; « No public snapshot available yet. “Refresh” starts a bounded collection. »; « No public matchup to show »; **aucun pourcentage**; contrôle identique, aucun dossier de campagne créé. Code 0. |
| Copie **installée** 0.9.5 (§6) : fumée intégrée + Statistiques FR | code 0, 7 pages; mêmes lignes d'archétype et de taux; contrôle identique |
Aucune demande d'identifiants, aucun appel Codex/Claude (aucun processus enfant, exécutables introuvables). « Actualiser »
n'a pas été cliqué dans l'EXE (il ferait une collecte réelle; la validation Limitless réelle est déjà faite, `1a75bdd`).

## 6. Installation, mise à niveau, désinstallation isolées (AppId QA)
Méthode de la 0.9.4 réutilisée : `.iss` de production dont seuls `AppId` (`{A4B3E0A0-B19F-4AAE-8CE2-30C3A1B6B811}`),
`AppName`, `UninstallDisplayName` et noms des raccourcis changent (« PokeMind QA »; diff dans `qa/qa-iss-diff.txt`),
compilé hors dépôt. Charge 0.9.3 = distribution conservée `dist/PokeMind-before-branding-e2ae…` (`__version__` 0.9.3 lu
dans son PYZ); charge 0.9.5 = le candidat. Installation silencieuse avec **`/DIR` dans le dossier temporaire de la tâche**
(vérifié : `InstallLocation` QA = ce dossier). Root de données inventé D.
- 0.9.3 QA : code 0, 801 fichiers → fumée 0 (7 pages) → **mise à niveau 0.9.5 QA** : code 0, fichiers installés =
  **exactement** la distribution 0.9.5 (0 différence, hors `unins000.*` et `LICENSE.txt`), EXE `ProductVersion 0.9.5`;
  **15 fichiers de données inventées identiques** avant/après → fumée 0 + Statistiques (§5) → raccourci QA pointe vers
  l'EXE installé → désinstallation code 0 : clé QA et raccourci retirés, 0 fichier programme restant, **données identiques**.
- Installation du propriétaire : seules sa clé de désinstallation (`DisplayVersion`) et la date de son raccourci ont été
  lues : `0.9.4`, raccourci daté 2026-11-07 06:27 UTC (installé **avant** cette session), **identiques avant/après**.
- **Écart à signaler** : un premier essai s'est arrêté sur une erreur de mon script (regex), après l'installation 0.9.3 QA
  et sa fumée (code 0). Cette installation QA a été désinstallée (code 0, clé et raccourci retirés, 0 fichier), puis tout
  l'essai a été refait depuis zéro sur un root neuf : ce sont ces chiffres qui sont rapportés.
- Le Setup de **production** (AppId du propriétaire) n'a **pas** été exécuté : il remplacerait l'installation réelle.

## 7. Export public (dry-run, sans push)
`scripts/export_public.py` vers le dossier temporaire de la tâche : `EXPORTED`, 672 fichiers, arbre `d1ab63b` **identique**
à `24e9cc5`, 1 commit « PokeMind 0.9.5 » (auteur public `noreply`), **aucun remote, `pushed: false`**. Contrôle
indépendant de l'export : aucune occurrence du nom de compte Windows, d'un courriel personnel ni d'un chemin `C:\Users\`;
seul fichier sous `data/local` : `.gitkeep`. Porte complète dans l'export : voir §3.

## 8. Non testé / limites
- Setup de production sur la vraie installation; mise à jour silencieuse `/RELAUNCH` depuis l'application (dernière
  preuve D-283, chemin inchangé); SmartScreen; 125 % / haute densité; HTTPS non rejoué (pile TLS du build non modifiée
  par ce mandat, dernière preuve D-290).
- « Actualiser » réel dans l'EXE et nouvelle collecte Limitless : volontairement non refaits.
- Réponses d'un vrai Codex/Claude; `qa_unified_desktop.py` (obsolète, à réparer dans un mandat distinct).
- Échantillon public : un tournoi par collecte et par jour, petits n; jamais des statistiques mondiales (écrit dans
  README FR/EN, notes et CHANGELOG). Les cas « Box/Control » restent non identifiés; `_snapshots` : limite documentée.
- Petit défaut cosmétique non bloquant observé : en anglais, le nom de source affiche « (API publique) » (constante
  `SOURCE_NAME`). Non corrigé (mandat : pas de changement hors bloquant V1).
- Signature de code absente (déclarée, `CODE_SIGNING.md`).

## 9. Données
Aucune lecture de `data/local` du dépôt, de `%LOCALAPPDATA%\PokeMind`, de journaux, decks, conversations, comptes ou
secrets réels. Roots, installations QA et bacs à sable : dossier temporaire de la tâche, données inventées. Aucune
requête réseau réelle vers Limitless pendant ce mandat (serveur inventé en mémoire, proxys fermés); seule requête
publique : `git ls-remote` du dépôt public (lecture).
