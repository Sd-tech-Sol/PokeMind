# Vérification indépendante ChatGPT — PM-UI-PREMIUM-DECKLAB-001
Date : 2026-11-08. Code `b4d03600ce7d133a403e5d362a5924837f0514b9`, rapport `1084484889a0c8f873762b44143f6c4352b6e1a0`; base `da7efc1458b3b4388c0e782a3454b42d3bacf402`.

## Verdict
**VERIFIED_SOURCE / VISUAL_OWNER_REVIEW_PENDING / CODE_PRIVATE_ONLY / NOT_RELEASE_READY.** Le périmètre autorisé de personnalisation « gaming premium » (première tranche Deck Lab > Galerie) est respecté. Pas de blocage source identifié sur les diffs consultés. Les résultats de tests, mesures et captures Windows sont des preuves **rapportées par Codex**, pas une exécution indépendante par ChatGPT.

### Audit Git indépendant
Compare `da7efc1...1084484` : deux commits, l'un code/tests et l'autre suivi; modules modifiés `desktop/card_art.py`, `desktop/motion.py`, `desktop/theme.py`, `desktop/widgets.py` et `tests/test_desktop_qt.py`. Aucun fichier de service, cache/catalogue, migration, version, workflow, installateur, donnée personnelle ou publication.
- `CardArt` réemploie `QPropertyAnimation`, passe à 220 ms seulement en galerie, applique zoom de 1,8 % et translation verticale de 2 px à la peinture, sans reflow des voisins, arrête/neutralise l'animation à la désactivation et au masquage.
- `DeckGallery` crée des `CardTile(gallery=True)` avec marges de groupe, alignement des colonnes, sections et noms/impressions repliables. `CardTile` réserve la hauteur nécessaire, dessine un liseré animé via l'état du `CardArt`, et conserve une sélection visuelle `focus` indépendante du hover. Focus/clavier Espace et agrandissement conservés par conception.
- `MotionEffects` ignore les cartes/illustrations de la galerie afin de ne pas superposer un deuxième effet. QSS galerie limitée à `QScrollArea#deckGallery` et tokens existants BrainBall ; palette JSON inchangée. Aucune nouvelle dépendance ni 3D.
- Tests ajoutés pour image aux coins, géométries, clavier, animation réduite, navigation/fermeture, thèmes/langues, fenêtres/police agrandie, défilement/repopulation et absence de requêtes image au hover. La revue du code ne révèle pas de régression évidente nécessitant de bloquer ce lot.

### Preuves déclarées par Codex
- `python scripts/local_gate.py` dans copie synthétique isolée : **130 Qt + 1639 cœur réussis, 0 échec, 3 ignorés, sortie 0**; compilation/hygiène vertes.
- Douze captures natives Windows synthétiques avant/après sous `build/qa-premium-decklab/`, ignorées de Git; illustrations géométriques fictives; FR/EN, sombre/clair, 1100/1500 px, police 14/18 px.
- Mesure exploratoire non normative 60 tuiles : création 662,3→635,3 ms; 120 scrolls 1029,2→869,5 ms. Aucun benchmark officiel ni garantie de performance.
- CI GitHub non exécutée, aucun check/run vert. Copie du PC installée non touchée et non testée. Aucun accès aux données personnelles.

### Réserves non bloquantes et prochain contrôle
- Les captures natives sont restées **locales** sur le PC de l'exécuteur, pas observées indépendamment par ChatGPT. Valider le rendu final avec le propriétaire avant toute intégration de la tranche suivante; vérifier contraste sur le thème réellement utilisé et avec des cartes reconnaissables dans une future QA isolée.
- DPI physique Windows non exercé (uniquement police agrandie). Tester avant installation.
- Le rendu galerie `CardArt` ne clippe plus explicitement le pixmap au chemin arrondi pour ne pas tronquer les quatre coins : inspecter visuellement la qualité des angles lors de la réception; ce choix est esthétique, pas identifié comme régression fonctionnelle.
- L'ancienne 0.9.5 hotfix `00eecb3` installée et acceptée reste inchangée. Sauvegardes D-293 et pré-hotfix conservées; réserve de delta postinstall antérieur inchangée. Version publique 0.9.3; aucun GO publication/install.

## Prochaine action unique recommandée
**Révision visuelle propriétaire des 12 captures synthétiques locales** `build/qa-premium-decklab/before-*.png` et `after-*.png` (aucune donnée privée). Comparer avant/après, marges, liserés, typographie et impression de profondeur; choisir ensuite une seule tranche du storyboard à prioriser. Pas d'exécution d'agent maintenant, pas de nouveau prompt activé, tant que le propriétaire n'a pas rendu son avis.
