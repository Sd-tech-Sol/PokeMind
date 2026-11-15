> **2026-11-07 — PM-RELEASE-095-RECEPTION-HOTFIX-001 livré (D-294, `00eecb3`), STOP audit ChatGPT.** Réception 0.9.5 non acceptée : deux défauts corrigés. (1) Deck Lab « Image indisponible » : après la mise à jour du catalogue en soirée (UTC du lendemain), `build_aliases` comparait la date UTC de récupération à la date locale et refusait toutes les extensions jusqu'à minuit → aucune identité, aucune image; `database.local_day()` pour les dates de récupération du catalogue. Reproduit puis corrigé sur copies publiques du vrai catalogue et du vrai cache (0/13 → 12/13 images). (2) « Ce que le coach reçoit » : choix tronqué, sélection blanc sur bleu pâle en clair (style windows11), colonne étroite; liste dessinée par le thème, menus dimensionnés, menu sous l'explication longue. Porte VERTE (Qt 122, cœur 1639/0/3). Candidat isolé `dist/installer-candidate-0.9.5-00eecb3/` (`91993E84…C212`), **non installé**. Voir [RESULT](RESULT.md).

> **2026-11-07 — PM-RELEASE-095-OWNER-INSTALL-001 exécuté (D-293), STOP audit ChatGPT + inspection propriétaire.** Sauvegarde complète vérifiée avant toute modification (306/306 fichiers, SHA-256 identiques, restauration à blanc OK; privée, hors dépôt). Setup 0.9.5 SHA-256 **MATCH** `6E7E5CB2…68CB`, AppId de production = 0.9.4 installée. Assistant Inno normal (seulement `/LOG`), code 0; registre 0.9.5 (une clé), EXE installé `7121BBEB…E6FF` = candidat testé, 797/797 fichiers = distribution 0.9.5; fumée isolée de l'EXE installé : 7 pages. Données : 0 fichier préexistant perdu; changements attribués au PokeMind 0.9.5 lancé par l'assistant puis par le propriétaire (catalogue public, campagne publique, journal, état, réglage). Statut `INSTALLED_OWNER_VERIFICATION_PENDING`. Voir [RESULT](RESULT.md).

> **2026-11-07 — PM-RELEASE-095-WINDOWS-CANDIDATE-001 livré (D-292, `24e9cc5`), STOP audit ChatGPT.** Version 0.9.5 partout (0.9.4 jamais publiée, intégrée); porte VERTE sur `24e9cc5` (Qt 121, cœur 1635/0/3). Candidat local `dist/installer-candidate-0.9.5-24e9cc5/PokeMind-Setup-0.9.5.exe` (SHA-256 `6E7E5CB2…68CB`, non signé), EXE `build/exe-upgrade-f886…` (`7121BBEB…E6FF`); PE/Setup 0.9.5, icônes 9/9, `deck_public_stats` dans le PYZ, scan CLEAN. Fumées gelées isolées : 7 pages, Deck Lab › Statistiques FR/sombre (chiffres = oracle) et EN/clair (aucun pourcentage), aucun réseau ni processus enfant. AppId QA : 0.9.3 → 0.9.5 → désinstallation, données inventées identiques, installation du propriétaire inchangée. Export dry-run identique, non poussé. Voir [RESULT](RESULT.md).

> **2026-11-07 — PM-DECKLAB-STATS-REALITY-GATE-001 livré, STOP audit ChatGPT.** Aucun changement de code (`3a56023`). Porte complète sur l'arbre final : VERTE (Qt 121; cœur 1634/0/3), deux fois (HEAD `d1c06ed` et arbre du rapport), code de sortie 0. Essai réel Limitless borné (root synthétique hors dépôt) : 5 GET, API disponible, 1 tournoi PTCGL Standard BO1 du jour (23 joueurs, 56 matchs admissibles, archétypes publiés); rendu hors ligne et oracle conformes; seuils et ambiguïté respectés. `_snapshots` : limite non reproductible avec `max_tournaments=1`. Voir [RESULT](RESULT.md).

> **2026-11-07 — PM-DECKLAB-PUBLIC-STATS-001 livré (D-291, `3a56023`), STOP audit ChatGPT.** Deck Lab › Statistiques : chiffres publics par **archétype** (pas les 60 cartes exactes) depuis l'API Limitless via `research_matchups` + `meta_*` existants; BO1/BO3 jamais fusionnés, miroirs/byes exclus, seuils sans pourcentage; identification locale par les Pokémon de la liste; 1 tentative auto/jour partagée + Actualiser borné (≤ 2/jour, ≥ 10 min); contrôle `data/local/public-campaigns/deck-public-stats.json`. Porte : VERTE (Qt 121, cœur 1634/0/3). Rien construit, installé ni publié; 0.9.4 inchangée. Voir [RESULT](RESULT.md).

> **2026-11-07 — PM-RELEASE-094-FINAL-GATE-001 livré (D-290, `fae10da`), STOP audit ChatGPT.** Candidat 0.9.4 : liste du deck principal envoyée au coach seulement si la question parle de deck (texte de Réglages, assistant, PRIVACY et README fidèles; envoi cloud dit pré-coché); version 0.9.4 partout, y compris propriétés Windows de l'EXE et du Setup. Porte VERTE (Qt 119, cœur 1624/0/3), idem dans l'export dry-run. Installateur `dist/installer-candidate-0.9.4-fae10da/` (non signé, non publié); essai installation/mise à niveau/désinstallation avec AppId QA isolé (`PokeMind QA`), installation du propriétaire inchangée. Voir [RESULT](RESULT.md).

> **2026-11-06 — PM-COACH-LOSS-PRIORITY-001 livré (D-289, `5ee8c45`), STOP audit ChatGPT.** Un journal collé n'enregistre plus le deck adverse (question auto. selon l'issue; `save_deck`/`save_candidate` refusés dans ce tour sauf demande explicite); suivi des défaites `loss_watch` dérivé du rapport (aucun second stockage) donné au coach; anciens decks adverses gardés et identifiés. Porte VERTE (Qt 119, cœur 1621/0/3). EXE candidat local dans `build/exe-upgrade-ae54…/dist/PokeMind/`, non installé. Voir [RESULT](RESULT.md).

> **2026-11-06 — D-288 (`6cb86c4`)** : saison à 0 corrigée (`added_on` dans le rapport affiché), « Ajouter mon deck » et « Deck principal » au Deck Lab; porte VERTE (Qt 118, cœur 1611/0/3); installé chez le propriétaire. STOP audit ChatGPT.

> **2026-11-06 — D-287 (`358a551`)** : coach cloud avec statistiques anonymes autorisé par défaut (ordre du propriétaire); porte VERTE (Qt 116, cœur 1610/0/3); installé chez le propriétaire, ses préférences réglées (sauvegarde gardée). STOP audit ChatGPT.

> **2026-11-06 — PM-UI-BRAINBALL-BRANDING-002 livré (D-286), STOP audit ChatGPT.** Code `8570613` : la carte approuvée
> remplace le logo dessiné partout (UI, `.ico` de l'EXE, installateur, README). Dérivé embarqué reproductible
> `src/pokemind/desktop/branding/pokemind-card.png` (`scripts/make_icon.py --card`). Porte locale VERTE (Qt 115, cœur
> 1610/0/3). EXE local déployé dans `dist/PokeMind/` (retour arrière `dist/PokeMind-before-branding-e2ae…`), installateur
> candidat dans `dist/installer-branding-candidate/` (non signé). Rien de publié, rien d'installé. Voir [RESULT](RESULT.md).

> **2026-11-06 — nouveau mandat propriétaire PM-UI-BRAINBALL-BRANDING-002.** La carte verticale approuvée est désormais réellement présente dans le dépôt **privé** : `assets/branding/pokemind-tcg-coach-original.png` (SHA-256 `30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5`, Git blob `18abf6bccaecba8553556fbdbeeb8d980ff4eb45`). Le mandat actuel est le **premier bloc de NEXT_ACTION.md**, qui renvoie à `NEXT_PROMPT.md` (nouveau prompt intégral). Claude Code doit remplacer l'ancien logo dessiné dans les ressources UI/EXE/installateur en réutilisant les pixels exacts, tester et produire un candidat local; **pas de release 0.9.4 sans GO**, pas de donnée personnelle. Le précédent audit 0.9.3 reste historique; nouvelle tâche à auditer après livraison.

> **Audit ChatGPT 2026-11-06 :** source BrainBall et publication `v0.9.3` indépendamment vérifiées (arbre public `bb5beca` identique au privé `84426b8`; 18 contrastes de palette recalculés, tous ≥ 4,5:1). **Pas de preuve Windows utilisateur ni de réexécution indépendante des 114 Qt/1610 tests**. Aucun statut GitHub CI. Rapport : [VERIFICATION_PM-UI-BRAINBALL-THEMES-001_POST_093_2026-11-06.md](VERIFICATION_PM-UI-BRAINBALL-THEMES-001_POST_093_2026-11-06.md). **Prochaine étape : réception propriétaire v0.9.3; pas de nouveau mandat Claude ni publication 0.9.4 sans nouveau GO.**

# HANDOFF — 2026-11-05

- Branche : `work/pm-v1-lotj-final-readiness-windows`. Dernier code : `84426b8` (0.9.3 publiée, D-285; couleurs BrainBall D-284), porte locale VERTE (Qt 114, cœur 1610/0/3); EXE de `dist/PokeMind` construit depuis ce commit. Historique ci-dessous (2026-11-02 et suivants).
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
- 2026-11-05 : **D-285** : **PokeMind 0.9.3 publié** sur GO du propriétaire (« go »), avant l'audit ChatGPT de
  D-284 : `main` public `5629ae2` (parent `afdb0a3`, arbre du privé `84426b8`), préversion `v0.9.3` avec
  installateur non signé et `.sha256`, empreinte vérifiée sur le fichier téléchargé; le module de mise à jour
  annonce bien 0.9.3 à une 0.9.2. EXE 0.9.3 déployé (`dist/PokeMind-before-0.9.3-public-<id>` gardé).
  Porte VERTE au contenu de `84426b8` et dans l'export (Qt 114, cœur 1610/0/3).
  Porte finale VERTE sur l'arbre du rapport (Qt 114, cœur 1610/0/3); seule cette ligne a changé depuis.
- Prochaine étape :
  - **audit indépendant ChatGPT** du mandat BrainBall, a posteriori (déjà publié en 0.9.3) ;
  - puis, sur décision du propriétaire : corrections de l'audit (0.9.4 sur GO) ;
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
