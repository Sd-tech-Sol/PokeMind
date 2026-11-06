# HANDOFF — 2026-11-05

- Branche : `work/pm-v1-lotj-final-readiness-windows`. Dernier code : `cdd2fc6` (D-284, couleurs BrainBall), porte locale VERTE (Qt 114, cœur 1610/0/3); EXE de `dist/PokeMind` construit depuis ce commit. Historique ci-dessous (2026-11-02 et suivants).
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
- 2026-11-02 : **D-272 — PokeMind 0.9.0 publié** sur GO du propriétaire : dépôt public `Sd-tech-Sol/PokeMind` (un seul
  commit, arbre de `3d4af78`) et préversion `v0.9.0` (installateur + `.sha256`). Le dépôt privé de travail reste
  `Sd-tech-Sol/PokeMind-dev`; **ne jamais pousser l'historique privé vers le dépôt public**. Mise à jour publique :
  nouvel export (`scripts/export_public.py`) appliqué dans un clone du dépôt public, commit « PokeMind x.y.z », sur GO.
- 2026-11-02 : **D-273** à `9a9c6b4` : règle 1 ACE SPEC / 1 Radieux (`rules.special_card_class`, rareté du catalogue,
  repli `NULL AS rarity` pour les anciens catalogues); `save_deck` sans détection de mots, refus si règle violée;
  bandeau de chargement (`MainWindow.show_loading` / `hide_loading`); « Tout supprimer »
  (`delete_all_conversations`); rendu du chat (`message_html` par blocs, `tool_chip`, `inline_html`). Écrire les
  correctifs de code par scripts Python (outil Write), jamais par heredoc Bash : les barres obliques inverses y sont altérées.
- 2026-11-03 : **D-274 — PokeMind 0.9.1 publié** sur GO : commit public `a6446e1` (arbre de `bc90012`) et préversion
  `v0.9.1`. Le propriétaire modifie parfois le dépôt public dans l'interface GitHub : **avant chaque mise à jour
  publique, `git fetch` du dépôt public et reporter ses commits dans le dépôt privé** (checklist C.0).
- 2026-11-03 : **D-275** à `c7f8271` : coach local d'abord puis web (`provider.WEB_GUIDANCE`, `WEB_TOOLS`,
  Codex `web_search="live"`), mémoire web locale (`pokemind.web_memory`, outils `web_memory` / `remember_web`),
  « Recherche web » garde la réponse du modèle + `receipts.public_memory_summary`, modèle du terminal pour
  Claude (`provider.terminal_model`; neutralisé dans les tests par `conftest.no_terminal_model`).
- 2026-11-03 : **D-276** à `1593f0b` : réinitialisation complète (`pokemind.data_reset`, demande écrite par
  `MainWindow.reset_application`, appliquée par `desktop.app.launch` avant toute ouverture de `data/local`;
  copie datée par défaut, retour complet si verrou).
- 2026-11-03 : **D-277** à `b53eee3` : réinitialisation au choix (`data_reset.CATEGORIES` / `selection`,
  fenêtre `desktop.reset_dialog`); tous les types cochés = complet.
- 2026-11-03 : **D-278** à `c4338f5` : diagnostic du propriétaire traité : plantage `ingest_done`
  (suppression pendant un import), échantillon public mémorisé (`competitive._advisor_snapshot`), partage
  entre plans (`counter_plan(shared=…)`), diagnostic qui garde les lignes récentes et liste les erreurs.
- 2026-11-05 : **D-279** à `4cf50ea` : 2e diagnostic : gain D-278 confirmé (environ 85 s → 31 s); `decks` et
  `research` ne dépassent plus le plafond d'outil (liste compacte + un deck par numéro, reçu borné, filet
  `truncated`); plans contre-deck et contexte public réutilisés d'un import à l'autre tant que les fichiers
  publics ne changent pas.
- 2026-11-05 : **D-280** à `1cdb9cd` : « Réinitialiser » ne faisait rien pendant une analyse ou une réponse
  (seule une ligne d'état) : il arrête l'opération puis s'applique; scripts `archive_data` / `reset_data` /
  `restore_data` (`pokemind.data_archive`, zip vérifié de tout `%LOCALAPPDATA%\PokeMind`), exécutés sur
  demande explicite; saisons TCG Live (`pokemind.seasons`, saison actuelle depuis 2026-11-05, passées, cumul).
- 2026-11-05 : **D-281** à `b3c533c` : « Archiver… » et « Restaurer… » dans Réglages → Données (boîtes
  natives de Windows; archive en arrière-plan relue entière; restauration au relancement, données actuelles
  archivées d'abord à côté du zip). Les scripts restent pour le dépannage.
- 2026-11-05 : **D-282** : **PokeMind 0.9.2 publié** sur GO du propriétaire : `main` public `afdb0a3` (parent
  `a6446e1`, arbre du privé `b329028`), préversion `v0.9.2` avec installateur non signé et `.sha256`, empreinte
  vérifiée sur le fichier téléchargé.
- 2026-11-05 : **D-283** à `caa3548` : **mises à jour en un clic**.
  - Bandeau et Réglages → Mises à jour.
  - Cartes : `pokemind.catalog_update` (dernier commit TCGdex, `catalog-staging-*` puis renommage, ancien
    catalogue dans `catalog-previous`, `apply_pending` au lancement).
  - Programme : `pokemind.app_update` (préversions publiques, SHA-256 vérifié, `/RELAUNCH=1`, verrou
    `PokeMindDesktopRunning` attendu par `packaging/PokeMind.iss`).
  - Vérification limitée à une fois par 12 h (`data/local/update-check.json`), jamais en tests (`MainWindow(check_updates=…)`
    seulement depuis `app.launch`, hors QA et fumée).
  - Version 0.9.3 préparée (EXE déployé, installateur dans `dist/installer/`), **non publiée**.
  - Porte finale VERTE au HEAD du rapport (Qt 113, cœur 1603/0/3).
- 2026-11-05 21 h 37 : le propriétaire a poussé le mandat **PM-UI-BRAINBALL-THEMES-001** (premier bloc de
  NEXT_ACTION, READY_FOR_EXECUTION). D-283 l'a intégré par une fusion, sans l'exécuter, car une modification
  GitHub n'autorise pas seule une exécution. Pour ce mandat : D-283 ajoute `QFrame#updateBanner` (bordure
  `#4fb98f`), la teinte et l'icône `updates`, et les onglets des Réglages sur deux rangées (`QGridLayout`).
- 2026-11-05 : **D-284** à `cdd2fc6` : **couleurs BrainBall** (mandat PM-UI-BRAINBALL-THEMES-001, déclenché
  par le propriétaire). État **IMPLEMENTED/REPORTED, non VERIFIED** ([RESULT](RESULT.md)).
  - `theme.py` : `PALETTES` = jetons de `palette.json` tels quels + `DERIVED` déclarés (dont `field_border`);
    `OBJECTS` (classeur, terminal) communs aux deux thèmes; `contrast()`/`luminance()` WCAG; `theme_of()` pour
    les peintres; chevron des listes (`_chevron`, PNG dans `%TEMP%\pokemind-theme`).
  - Feuille de style sans couleur codée en dur (test). Boutons destructeurs : propriété `destructive` (pas le
    nom d'objet, que `compact` écrase). Icônes redessinées au changement de thème : `MainWindow.themed_icons`.
  - Tests : `tests/test_desktop_theme.py` (7) et `test_qt_theme_switch_redraws_the_drawn_icons_and_the_chat`.
    Captures synthétiques : `docs/design/pokemind-brainball/captures/`.
  - EXE reconstruit et déployé dans `dist/PokeMind` (ancienne copie `dist/PokeMind-before-brainball-<id>`);
    installateur 0.9.3 remplacé dans `dist/installer/` (le précédent : `-mises-a-jour`). Rien de publié.
  - Porte finale VERTE sur l'arbre du rapport (Qt 114, cœur 1610/0/3); seule cette ligne a changé depuis.
- Prochaine étape :
  - **STOP : audit indépendant ChatGPT** du mandat BrainBall (au SHA du rapport) ;
  - puis, sur décision du propriétaire : corrections de l'audit, ou GO pour publier 0.9.3 (D-283 + D-284 ;
    checklist C.0 à C.2 ; passer README et SECURITY à 0.9.3 et dater le CHANGELOG au moment de publier) ;
  - réception propriétaire (Réglages → Mises à jour, nouvelles couleurs ; Delta Reign arrivera par « Mettre à
    jour les cartes » quand TCGdex l'aura publié) ;
  - sinon étape 5 ou étape 6.
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
