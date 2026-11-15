# Audit indépendant ChatGPT — PM-UI-DECKLAB-REAL-GALLERY-006
Date : 2026-11-09. Base `a661bd74f86d005209d0bb6c3a06c9951599310c`, code `d6efdd2ddbd2b804e1fc1689dfaa243567640005`, rapport `8abe2262031d4448d8bb8938e5a44d53bc5b94c3`. Dépôt privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`.

## Verdict
**VERIFIED_SOURCE / REPORTED_LOCAL_GATE_GREEN / OWNER_REAL_GALLERY_VISUAL_RECEPTION_PENDING / NOT_INSTALLED / NOT_RELEASE_READY.**

La première intégration dans la **vraie galerie Qt**, limitée aux composants UI existants, est cohérente avec le mandat. Les modifications fonctionnelles vérifiées dans les diffs ne montrent pas de blocage source justifiant un nouveau développement immédiat. ChatGPT **n'a pas exécuté le code ni les tests sur Windows**; résultats de QA, performances, métriques, fichiers média locaux, hashes et propreté locale sont **des déclarations de Codex**. Les deux PNG de capture demandés n'ont pas été téléversés dans ce clavardage et ne sont pas accessibles par GitHub.

## Audit de source indépendant (GitHub)
- Compare `a661bd7...8abe226` = 2 commits, code `d6efdd2` puis rapport `8abe226`. Modifications métier limitées à `src/pokemind/desktop/widgets.py`, `card_art.py`, `theme.py`; ajouts `scripts/qa_real_decklab_gallery.py`, `tests/test_desktop_qt.py` et suivis orchestrateur. **Pas de diff** dans `window.py`, services, stockage, catalogue, cache, permissions, statistiques publiques, Coach, installeur, version ou publication.
- `DeckGallery.reflow()` calcule 3/2/1 colonnes selon largeur réelle du viewport, au seuil de 814/428 px environ, plafonne les tuiles à 320 px, met à jour la largeur même si nombre de colonnes inchangé; conserve les sections par catégories avec lignes incomplètes naturelles.
- `CardTile(gallery=True)` garde la hiérarchie existante et réserve une hauteur d'art d'environ ratio 1:1,4 et libellés repliés; tuiles agrandies, QSS sections 16 px/noms 17 px, sélection distincte hover/focus. Aucune nouvelle dépendance ou moteur.
- `CardArt` conserve `KeepAspectRatio`, animation 220 ms depuis `CardTile`, les coins non coupés lors du hover; ajoute le raccourci Entrée / Retour du pavé numérique pour `galleryArt`, et un fallback multi-ligne peint dans le bouton (sans image) via style/palette.
- `DeckGallery.populate` et `window.py:deck_selected` réutilisent les flux existants (`generation`, `self.images.fetch`, identités de cartes, consentements sans changement).
- Les nouveaux tests du vrai `MainWindow` reposent sur données et images synthétiques, exercices de copie/export/favoris/deck principal, comparaison, zoom/provenance, mobilité clavier, thèmes/langues, réduction des animations, absence de fetch sur scroll, asynchronie A→B et nettoyage d'anciennes tuiles. Ils sont substantiellement plus probants qu'un test de la démo seule.
- Le nouveau script de QA copie l'arbre hors `data/local` via `local_gate.copy_tree`, lance des pytest sous Windows et conserve les captures sous `build/`. Avec `--baseline-ref`, il rétablit seulement les 3 modules de galerie comparés; adapté à une comparaison visuelle mais **pas** une comparaison bit à bit des arbres complets des deux versions.

## Preuves déclarées par Codex, non rejouées
- `python scripts/local_gate.py --keep` : **138 Qt + 1654 cœur = 1792 réussis, 3 ignorés, 0 échec, sortie 0**; tests ciblés Windows 16/16 à 100 % et 125 %, tests offscreen 16/16. Tentatives antérieures infructueuses et corrections détaillées dans RESULT.
- Fenêtre réelle de test avec menu et Coach présents : largeur viewport mesurée 852 px à 1500×970 (3 colonnes), 453 px à 1100×900 (2 colonnes). Largeur d'image rapportée 141→224 px (+59 %) et 147→164 px (+12 %). Le deuxième format gagne peu car menu, Coach et commandes prennent de la place.
- Horizontal-scroll = 0 dans la matrice; défilement vertical sensiblement accru, à prévoir dans l'expérience utilisateur.
- Captures à 125 % `build/qa-real-decklab-gallery/after-1.25/gallery-1500-dark-fr-14.png`, `gallery-1100-dark-fr-14.png`; autres thèmes et zoom ; vidéo/GIF hover synthétique. Les fichiers sont **locaux hors GitHub**, non visionnés par ChatGPT.
- Codex signale un problème **préexistant** : certains boutons de la rangée du sélecteur du deck sont tronqués à 1100 px / 125 %, hors de la galerie et hors périmètre du lot. À inspecter lors de la réception visuelle.
- Contraste mesuré par Codex sur 22 paires ≥5,35:1 ; ne constitue pas un audit pixel à pixel de tous les états/illustrations.
- GitHub revérifié par ChatGPT au SHA exact de code : combined status retourne `statuses: []` et liste de workflow runs accessible retourne `workflow_runs: []`. **NO_GITHUB_STATUS, non CI verte**.

## Réserves, prochaine décision
1. Aucune **réception visuelle propriétaire** à cette étape. Ne pas confondre photos des précédents prototypes et cette nouvelle galerie Qt réelle : l'utilisateur doit ouvrir et téléverser les deux nouvelles images (1500 et 1100), idéalement `hover.mp4`.
2. La grille est techniquement fidèle à l'architecture actuelle, mais ne copie pas le panneau Coach, le bandeau panoramique ni les détails repliables du prototype, conformément au mandat. La vraie UI 1100 px présente encore des contraintes d'espace, y compris un tronquage du sélecteur déclaré préexistant.
3. Le pipeline des images et l'état utilisateur n'ont pas été migrés ni touchés; seuls la compilation et les tests sur fixtures synthétiques sont rapportés. **Ne pas installer** sur le PC propriétaire ou restaurer des données sur cette seule base.
4. **Action unique recommandée : réception visuelle de la VRAIE fenêtre Qt** à 1500 et 1100 px. Après avis positif du propriétaire, décider séparément de la préparation du candidat/installateur et de ses sauvegardes/contrôles; aucun GO d'installation ni publication maintenant.
5. PokeMind 0.9.5 hotfix installé et sauvegardes antérieures restent tels quels; version publique 0.9.3, aucune publication autorisée.

**État : source auditée; attente des captures réelles du lot 006 et du verdict du propriétaire.** `NEXT_PROMPT.md` consommé; aucune tâche Codex suivante activée.

## Réception visuelle indépendante — deux captures utilisateur reçues (2026-11-09)

Le propriétaire a joint deux captures de la **vraie fenêtre Qt exécutée avec données et cartes synthétiques**, venant du lot 006. Leurs noms : `gallery-1500-dark-fr-14.png` et `gallery-1100-dark-fr-18.png`. Attention : la **deuxième est à police 18 px**, contrairement au fichier `gallery-1100-dark-fr-14.png` demandé initialement. Le cadrage de ces deux images a été inspecté directement par ChatGPT; la vidéo `hover.mp4` n'a pas été fournie dans ce tour.

**Observations vérifiées visuellement :**
- À 1500 px : trois grandes tuiles uniformes alignées, catégories lisibles, sélection jaune, aperçu des images fictives proportionnel, Coach conservé à droite. Les tuiles continuent verticalement derrière la limite visible du viewport; l'aire galerie défile naturellement.
- À 1100 px et police 18 px : la grille est bien à deux grandes colonnes, mais la rangée de **sélection/actions du deck est VISUELLEMENT TRONQUÉE** : le texte du sélecteur n'affiche qu'une partie du titre, « Deck principal » est tronqué et « Ajouter mon deck… » perd une partie de son intitulé. Cette dégradation rend les contrôles difficiles à identifier et ne doit pas être installée telle quelle dans une application censée prendre en charge les polices agrandies. État antérieur aussi signalé par Codex, mais désormais démontré par l'image utilisateur.
- Les cartes présentent des rectangles/carrés de couleurs parce que la fixture QA utilise une image artificielle à quatre coins; **ce n'est pas un échec de chargement TCGdex**, ni un visuel attendu en production. Aucun test avec les vraies images/cache utilisateur n'a été autorisé.
- Le bandeau du prototype et la modernisation du Coach ne sont pas intégrés, **conformément** au mandat ciblé 006. La galerie de production reste plus sobre que la maquette complète et ses contrôles hors galerie demeurent présents.

**Verdict révisé : REAL_GALLERY_006_SOURCE_VERIFIED / 1500_VISUALLY_ACCEPTABLE / 1100_18PX_RESPONSIVE_DEFECT / INSTALLATION_BLOCKED_PENDING_RESPONSIVE_FIX.** Ce n'est pas un échec de la galerie 006, mais un défaut réel dans l'écran Deck Lab qui empêche la réception globale à largeur réduite. Les tests de source demeurent verts selon Codex; le défaut a échappé aux assertions visuelles automatisées sur les libellés de cette rangée.

**Prochaine action recommandée (unique) : un correctif UX limité aux contrôles sélecteur/actions de `window.py:_decks()`** : conserver les mêmes boutons/slots/fonctions et les réorganiser de façon adaptative en 1 rangée à 1500 px, 2 rangées si nécessaire à 1100 px / 18 px / échelle 125 %. Vérifier aussi FR/EN, thème sombre/clair, clic/focus et aucune perte de hauteur excessive ou défilement horizontal. Ne pas toucher au pipeline des cartes, à la grille, au Coach, aux données, aux consentements ni aux sauvegardes. Refaire captures du vrai `MainWindow` avec fixtures synthétiques et tests d'absence de troncature; porte complète verte avant push privé. **Aucune installation, publication ou nouvelle version autorisée.**
