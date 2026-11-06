# RESULT — PM-AUDIT-CLAUDE-PLAN : mises à jour en un clic (D-283), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Demande du propriétaire : un bouton qui va chercher les nouvelles cartes
(Delta Reign) et une alerte de mise à jour du programme, « on clique sur mise à jour, puis ça fait tout le
reste »; « tu as carte blanche ». Session précédente (D-282) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D282_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D282_2026-11-05.md).

## Fait (`caa3548`)
- **Bandeau « Mise à jour disponible »** au-dessus de toutes les pages : nouvelles cartes et/ou nouvelle version.
  « Mettre à jour » fait les cartes d'abord (sans redémarrer), puis le programme; « Plus tard » le cache
  jusqu'au prochain lancement.
- **Réglages → Mises à jour** : version de PokeMind, catalogue (nombre de cartes, nouveautés), « Vérifier
  maintenant », « Vérifier au démarrage » (préférence `update_check`, activée par défaut). Onglets des Réglages
  sur deux rangées (six onglets lisibles à côté du coach).
- **Cartes** (`pokemind.catalog_update`) :
  - vérification par deux petites requêtes : dernier commit TCGdex (API GitHub), puis liste des extensions de
    l'API TCGdex ; elle signale les nouvelles extensions et les 20 extensions récentes qui ont gagné des cartes ;
  - mise à jour : construction dans `data/local/catalog-staging-*`, refus si le nouveau catalogue a moins de
    95 % des cartes, mise en place par renommage, ancien catalogue gardé une fois dans
    `data/local/catalog-previous/` ;
  - si les fichiers sont occupés, la mise en place se fait au lancement suivant (`apply_pending`).
- **Premier catalogue** : commit TCGdex le plus récent, repli sur l'instantané épinglé s'il ne s'importe pas.
- **Programme** (`pokemind.app_update`) :
  - préversions du dépôt public ; installateur et `.sha256` exigés ; hôtes GitHub seulement (redirections
    filtrées) ; taille et SHA-256 vérifiés avant tout lancement ;
  - copie installée : installateur silencieux `/RELAUNCH=1`, qui attend le verrou `PokeMindDesktopRunning`
    (90 s au plus), installe puis rouvre PokeMind ;
  - autre copie (`dist/`, sources) : ouverture de la page de la version.
- **Vérification au démarrage** :
  - au plus toutes les 12 h ; refaite si PokeMind ou le catalogue a changé depuis ;
  - échecs non mémorisés ; rien des données de l'utilisateur n'est envoyé ;
  - jamais lancée dans les tests, les fumées ou la QA.
- Réinitialisation « données publiques » : inclut `catalog-previous` et `catalog-staging-*`. L'archive exclut
  `catalog-previous`. `update-check.json` est classé technique.
- Documents publics : PRIVACY, README FR/EN (usage du réseau), CHANGELOG `[Unreleased]`, ROADMAP, brouillon
  `docs/RELEASE_NOTES_0.9.3.md`. Version **0.9.3** dans `pyproject.toml` et `__version__`, **non publiée**
  (README et SECURITY restent à 0.9.2 jusqu'au GO).

## Preuves
- Porte locale **VERTE sur la suite complète** : Qt 113, cœur 1603 réussis, 3 ignorés. Contenu de `caa3548`,
  sauf l'attente du script Inno passée de 60 à 90 s ; aucun test pytest ne lit ce script. Porte finale au HEAD
  du rapport : voir HANDOFF.
- Tests sans réseau : faux TCGdex à deux versions, fausses versions GitHub, empreinte ou taille fausse,
  redirection hors GitHub, catalogue plus petit ou cassé, fichiers occupés, alerte, clic unique, copie installée.
- Captures hors écran du bandeau et de l'onglet « Mises à jour » : textes lisibles.
- EXE recompilé depuis `caa3548` :
  - 83 modules `pokemind` identiques aux sources, aucun module QA ; recherche de chemins personnels dans les
    binaires passée ;
  - fumées en mode projet, en mode autonome et en copie installée : sortie 0 ; installation et désinstallation
    propres ;
  - `PokeMind-Setup-0.9.3.exe` non signé, SHA-256
    `A8642AEB5B95803AA898FB2305EE3A9C663A04F26B983757D47BC2383034BFAA`.
- **Mise à jour réelle**, sur une installation temporaire et une fixture synthétique :
  - verrou tenu 8 s par `app_update.mark_running` ; installateur lancé avec les arguments exacts de l'application ;
  - il a attendu la fermeture (6,2 s), installé (sortie 0) et rouvert PokeMind (preuve de fumée), en 12,7 s ;
  - désinstallation propre ; dossier de données du propriétaire inchangé.
- Déployé dans `dist/PokeMind/` (796 → 798 fichiers ; l'ancien est conservé sous
  `dist/PokeMind-before-0.9.3-<id>`). Installateur et `.sha256` copiés dans `dist/installer/` (hors Git).

## Limites
- **Delta Reign** n'est pas encore dans TCGdex (demande d'ajout ouverte, 33 cartes révélées, sortie du
  6 novembre 2026). Le bouton l'apportera dès que TCGdex le publiera.
- Les copies 0.9.0 à 0.9.2 n'ont pas ce mécanisme : 0.9.3 s'installe une fois à la main, puis tout passe par
  l'application.
- Une mise à jour télécharge l'installateur complet (environ 37 Mo), pas un différentiel. C'est un choix voulu :
  simplicité et empreinte vérifiée, données conservées.
- La copie `dist/PokeMind` du propriétaire n'est pas installée : son bouton ouvre la page GitHub de la version.
- Installateur non signé. V1 NOT_RELEASE_READY. Publication de 0.9.3 : **GO du propriétaire requis**.

## Intégration
Pendant cette session, le propriétaire a poussé six commits : palette BrainBall et mandat
**PM-UI-BRAINBALL-THEMES-001**, READY_FOR_EXECUTION. Le push du rapport a d'abord été refusé (avance rapide
impossible). Fusion sans force ni rebase : leur mandat reste le premier bloc de NEXT_ACTION et la tâche
courante de STATE ; la suite du plan d'audit est dans `paused_task`. Ce mandat **n'a pas été exécuté**. Porte
complète VERTE refaite sur l'arbre fusionné avant le push.
