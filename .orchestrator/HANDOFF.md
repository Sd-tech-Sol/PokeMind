# HANDOFF — 2026-11-02

- Branche : `work/pm-v1-lotj-final-readiness-windows`. Code : `a92e92529c66b4c187f6450cf5790f55d79f1ad4`, porte locale VERTE (Qt 81, cœur 1520/0/3); EXE installé depuis ce commit.
- Mandat actif : `PM-AUDIT-CLAUDE-PLAN` ([NEXT_ACTION](NEXT_ACTION.md)), exécuteur Claude Code, autorisation D-258.
- Fait aujourd'hui : étape 1 (EXE à jour) puis, sur demande du propriétaire, **coach avec les mêmes outils sous Codex,
  Claude et Ollama** (D-259, [RESULT](RESULT.md)); 2026-10-30 : bouton **Supprimer** une discussion (D-260);
  2026-10-31 : « fais-moi un deck » atteint le moteur au lieu d'un bilan local, file d'attente pendant l'analyse,
  limite coach 600 s, pont MCP sans coupure sur refus (D-261); le coach n'attend plus l'analyse des combats, liste
  des discussions lisible, étapes de l'analyse journalisées (D-262); journal collé → deck adverse reconstruit, nommé et
  enregistré dans « Mes decks » (`save_deck`), page **Terminal** (Codex yolo, Claude toutes permissions, PowerShell) (D-263).
  EXE recompilé depuis `62a5229` (796 fichiers, `OpenConsole.exe` requis par le terminal), anciens dossiers conservés sous `dist/`.
- Lenteur de l'analyse au démarrage (tout le corpus) : demander au propriétaire « Copier le diagnostic » et lire les
  lignes `Analyse · <étape> · <durée>` avant l'étape 5 (M-4).
- 2026-11-01 : **données hors du dépôt** (D-264, audit P0-1) : au démarrage, l'EXE propose une copie vérifiée de
  `data/local` vers `%LOCALAPPDATA%\PokeMind` (pointeur `location.json` par projet); original jamais touché, retour
  possible dans Réglages. **Après la bascule du propriétaire, ses données vivantes sont dans la copie**; `data/local`
  du projet devient un original figé, à ne jamais supprimer ni réutiliser sans son ordre. Le CLI `python -m pokemind`
  suit le même dossier (pointeur accepté ou `POKEMIND_DATA_ROOT`); les scripts autonomes de `scripts/` non.
- 2026-11-01 : **chat dans le dossier PokeMind par défaut** (D-265) : Codex / Claude démarrent à la racine du projet
  avec `AGENTS.md` / `CLAUDE.md`, outils natifs selon le mode et outils du coach (`chat_project`, canal `project:<mode>`).
  Un journal collé ne va jamais à un moteur doté d'un shell (coach isolé). Les tests gardent le coach isolé par défaut
  (`isolated_coach_chat` dans `tests/conftest.py`); les tests du mode dossier l'activent eux-mêmes.
- 2026-11-01 : **refonte visuelle (D-266)** à `45a49e2f0492ecaf5b2f01e7cdd21dccc0d7576d` : chat (activité animée, Entrée, grande fenêtre), logo Poké Ball +
  cerveau (`theme.ball_pixmap`, `scripts/make_icon.py`), Réglages en onglets (`setting_row`), Combats et Apprentissage en
  tuiles (`RecordBarDelegate`, `insights.learning_view`), classeur de cartes (`desktop/binder.py`, `cards.browse_cards`),
  Terminal aux couleurs de l'app, langue de Windows par défaut (`sessions.system_language`, conftest garde « fr »),
  assistant de premier lancement (`desktop/welcome.py`, `app.first_run`), README public, **plus de GitHub Actions**.
- 2026-11-02 : **version autonome installable (D-267)** à `40be3a06b65a90d1fcd856e8224b31d521d5a009` : `data_location.standalone`, mode autonome dans
  `desktop/app.launch` (`data_state='standalone'`, `MainWindow.standalone`), `catalog_download` (instantané TCGdex
  épinglé, 2 GET, import `public_catalog_snapshot`), `packaging/PokeMind.iss`, `scripts/Build-PokeMindInstaller.ps1`
  (Inno Setup 6 sous `%LOCALAPPDATA%\Programs\Inno Setup 6`). Fumée autonome : `POKEMIND_DATA_ROOT` obligatoire.
- 2026-11-02 : **pièces de publication (D-268)** à `5eb57ac` : licence MIT, logo original (`theme.logo_pixmap`,
  `motion.EmblemWidget`; plus de « ball » dans le code), audit de l'historique (arbre courant propre; anciens chemins
  avec le nom d'utilisateur dans l'historique; nom complet sur les commits).
- 2026-11-02 : **D-269** à `c8b453a` : export public vérifié (`scripts/export_public.py`, jamais de push), signature
  branchée (`-SignArguments`), procédure de publication, A-8 (mode Coach / Recherche web / Développement, plus de
  détection par mots) et A-7 (contexte allégé, envoi différentiel dans une même session).
- 2026-11-02 : **D-270** à `a334dec` : fichiers publics au standard des dépôts publics de `Sd-tech-Sol` (README EN +
  `README.fr.md`, Author, MIT au nom de l'auteur, AI_ASSISTANCE, SECURITY, PRIVACY, CONTRIBUTING, CODE_OF_CONDUCT,
  CHANGELOG, VISION, ROADMAP, avis, CODE_SIGNING, gabarits `.github`, guides, `docs/release-checklist.md` qui remplace
  `docs/PUBLICATION.md`); `scripts/scan_binary_personal_paths.py` branché dans l'installateur, fichier `.sha256`.
- 2026-11-02 : **D-271** : dépôt privé renommé **`Sd-tech-Sol/PokeMind-dev`** (`origin` mis à jour; liens vers ses
  commits et issues réécrits); `Sd-tech-Sol/PokeMind` est réservé au futur dépôt public. Pas de GitHub Actions publique
  (porte locale seulement), profil `Sd-tech-Sol` inchangé.
- Prochaine étape : réception propriétaire; au GO seulement, publication selon `docs/release-checklist.md` (sections A
  et C à E); sinon étape 5 (mémoire M-2 fin / M-4) ou étape 6 (maintenabilité).
- Pour reprendre : `git fetch && git pull --ff-only`, lire `AGENTS.md` → `SESSION_CONTINUITY.md` → `STATE.json` → `NEXT_ACTION.md`.
- Recompiler l'EXE : fixture `scripts/qa_unified_desktop.py --prepare-release`, `Build-PokeMindDesktop.ps1 -StagingRoot build/exe-upgrade-<32 hex>`,
  smoke `POKEMIND_DESKTOP_SMOKE=1` avec la fixture comme dossier courant, puis script de permutation local (sous `build/`, ignoré).
- Essayer le coach sans données personnelles : racine jetable contenant seulement des copies des deux caches de
  `SCOPED_PUBLIC_CACHES` et `.orchestrator/PROJECT_SPEC.md`, puis `Services.prepare_question` + `read_tool` avec le vrai moteur.
- Terminal : pywinpty 3.0.5 + pyte 0.8.2 + wcwidth 0.2.13 dans le Python système (porte) **et** `.venv-desktop` (EXE);
  ne pas rétrograder pywinpty (un autre paquet du PC exige 3.0.5). pyte lit mal `CSI >`/`CSI ? u` : filtre `IGNORED`.
- Pièges connus : tests imbriqués dans un chemin long → `WinError 206`, toujours passer par `scripts/local_gate.py`;
  Codex 0.163 exige `features.code_mode_host=true` pour les outils dynamiques; `claude --safe-mode` coupe tout MCP;
  permuter l'EXE avec PowerShell 7 (`pwsh`), Windows PowerShell 5.1 n'a pas `GetRelativePath`.
- Essayer la fenêtre réelle sans données personnelles : racine courte sous `%TEMP%` (chemins longs → `WinError 3`)
  avec les deux caches publics copiés, puis taper la question et Entrée par `QTest` (voir RESULT D-261).
- Historique : [archive/2026-10/HANDOFF_avant_2026-10-29.md](archive/2026-10/HANDOFF_avant_2026-10-29.md).
