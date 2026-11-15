# Audit indépendant ChatGPT — PM-UI-DECKLAB-REFERENCE-INTEGRATION-003
Date : 2026-11-08. Base `ecc06793d4f9c93ea04e8399a2572eff9d4eb314`, référence `2aa249c`, code `84214b9944a6361eef5d9a9a7a74e5825f7256f7`, rapport `bf5a932b0af488f71ad8e4e8f43ce2620bb486af`.

## Verdict
**VERIFIED_SOURCE / PNG_VERSIONED_PRIVATE / OWNER_ARTISTIC_REVIEW_PENDING / NOT_INTEGRATED / NOT_RELEASE_READY.** Référence visuelle enregistrée dans GitHub et preuve PySide6 distincte du produit. Tests, Windows, métadonnées de rendu et exports vidéo sont rapportés par Codex, **non exécutés ni visionnés indépendamment par ChatGPT**.

## Contrôles indépendants sur GitHub
- Compare `ecc0679...bf5a932` : trois commits, deux avant le rapport (référence `2aa249c`, code `84214b9`) puis rapport `bf5a932`. Aucun fichier de production `src/` modifié, aucun binaire d'installation ni publication.
- `docs/design/pokemind-brainball/references/decklab-premium-target.png` présent dans le diff; la page de référence donne dimensions 1672 × 941, 2 155 435 octets, SHA-256 `4e5888a7b22b6c7a84168b4aa779bd4eb526c031ee80cea0357aa26938ffd2b1` rapportés par Codex. Le dépôt contient la référence exacte vers laquelle l'utilisateur souhaitait guider Codex, sous réserve de ses contrôles d'identité locaux.
- `demos/premium_decklab/reference.py` crée `ReferenceWindow(QMainWindow)` séparé, avec 7 rubriques de navigation, panneau Deck Lab central, sélection de deck désactivée, 3 onglets fonctionnels, 6 illustrations fictives, bandeau, sélection de cartes et Coach docké à droite avec contrôles désactivés. Aucun constructeur de `MainWindow` production, aucun `Store`/`Services`, aucun modèle de chat ou accès réseau dans le prototype.
- Réutilise palette/logo/icônes Qt du produit, `DemoCard`, `AnimatedStack`, `ChatInput`, `QPropertyAnimation`. `record_preview.py` supporte une factory de fenêtre et sauvegarde via `window.grab()`; `reference_preview.py` déclenche cette factory. Les effets durent 220 ms (carte) et 180 ms (navigation entre onglets / détail). Mode mouvement réduit câblé.
- `tests/test_decklab_reference.py` : quatre cas (deux résolutions 1500 × 970 et 1100 × 900; dock, textes/onglets, défilement horizontal et largeur minimum; hover/interpolation, clavier et sélection; réduction d'animations; contrastes). Le test interdit `sqlite3.connect`, les connexions réseau usuelles et les ouvertures de chemins personnels pendant son exécution. Cette protection est ciblée, pas un bac à sable OS exhaustif.

## Mesures rapportées, pas rejouées
- Porte locale isolée `python scripts/local_gate.py` : **130 Qt + 1 649 cœur = 1 779 réussis, 3 ignorés, zéro échec, sortie 0**. Quatre cas ciblés et quatre essais Windows à 125 % passés. Pas de CI GitHub ni check disponible au SHA exact.
- Sorties locales `build/qa-decklab-reference/decklab-full.png` (1500 × 970), `decklab-1100.png` (1100 × 900), `preview.mp4` et `preview.gif` (120 images, 20 fps, 6 secondes) rapportées décodées par Codex. Ces sorties sont hors Git et ChatGPT ne les a pas inspectées.
- PNG privé est une maquette conceptuelle, contenant des cartes Pokémon stylisées non officielles, des chiffres, noms, fonctions et conseils fabriqués; le prototype ne doit pas les traiter comme fonctionnalités/observations vérifiées.

## Écarts et limites à soumettre au propriétaire
- Le prototype demeure une **adaptation** du vrai shell, non l'application principale : pas de galerie de production ni de cache d'art réel, six illustrations de démonstration, deuxième rangée partielle et défilement vertical. Aucun widget `src/` de production n'a changé.
- Maquette originale plus riche : illustration en bandeau et cartes réalistes, effets lumineux plus marqués, panneaux et fonctions supplémentaires. Codex a volontairement réduit la décoration et omis les fonctions fictives pour ne pas tromper. Aucun rendu « pixel perfect » établi.
- Thème sombre FR-CA seulement; dock de 355 px fixe en démo, petite fenêtre 1100 px testée, pas de DPI Windows réellement modifié (essai sous scaling Qt 125 %).
- L'acceptation technique ne vaut pas une acceptation esthétique. **Avant une intégration réelle, il faut faire visionner le PNG et la vidéo au propriétaire**, et décider s'il accepte ce niveau de fidélité ou veut une retouche encore ciblée.

## Prochaine action UNIQUE
Ouvrir sur le PC les fichiers `build/qa-decklab-reference/decklab-full.png` et `preview.mp4`. Pour audit visuel par ChatGPT, l'utilisateur peut téléverser la capture ou la vidéo ici. **Aucun nouveau mandat de développement ou d'intégration activé avant son jugement.** Préserver l'installation PokeMind 0.9.5 hotfix et ses sauvegardes; version publique 0.9.3, aucune publication autorisée.
