# RESULT — PM-UI-PREMIUM-DECKLAB-DEMO-002 — AWAITING_AUDIT (2026-11-08)

**Démo Qt interactive et aperçus animés produits; décision esthétique au propriétaire. STOP audit ChatGPT.**
Code `f5f751ffa5b333a33ce4908217b22eb0835be312`, base `da77207abd8109463cbcb721639b35a3c410f1e2`;
branche privée `work/pm-v1-lotj-final-readiness-windows`. [D-296](DECISIONS.md).
[Ancien RESULT archivé](archive/2026-11/RESULT_PM-UI-PREMIUM-DECKLAB-001_1084484_2026-11-08.md).

## Ouvrir la démonstration et les aperçus

Depuis la racine du dépôt : **`python demos/premium_decklab/demo.py`**.
Sources/guide : [demos/premium_decklab/README.md](../demos/premium_decklab/README.md).
Survol, clic, Tab/Espace, onglets et bouton « Voir les effets » fonctionnels; contrôle « Réduire les animations ».
Lecture Windows : **`Start-Process .\build\qa-premium-decklab-demo\preview.mp4`**, ou ouvrir le GIF dans un lecteur animé.

| Livrable local, hors Git | Vérification |
|---|---|
| `build/qa-premium-decklab-demo/preview.gif` | 1280 × 880, 120 frames, 6 000 ms, 794 933 octets |
| `build/qa-premium-decklab-demo/preview.mp4` | H264, 1280 × 880, 20 i/s, 120 frames, 6 s, sans audio, 271 032 octets |
| `build/qa-premium-decklab-demo/decklab-complete.png` | Fenêtre Qt complète 1280 × 880, décodage OK |
| `build/qa-premium-decklab-demo/decklab-1100.png` | Fenêtre Qt complète 1100 × 880, décodage OK |
| `build/qa-premium-decklab-demo/art-*.png` | Six illustrations originales 480 × 672, toutes décodées |

Art : `art-dragon.png`, `art-fox.png`, `art-ray.png`, `art-stag.png`, `art-owl.png`, `art-crystal.png`.
Même dossier : `frames/frame-0000.png` à `frame-0119.png`, `recording.json` et `verification.json`.
FFprobe et décodage FFmpeg de toute la vidéo réussis; Pillow a décodé les huit PNG et les 120 frames GIF.
Images intermédiaires 13/15 différentes, progression réelle du hover 0 → 0,5386 → 0,8377 → 0,9678 → 1.
Le film montre le vrai QWidget : Enter Qt, sélection de Flamaris, détails puis onglet Statistiques et retour Galerie.
Horloge Qt pilotée et échantillonnée, curseur circulaire ajouté uniquement au film; aucun diaporama ni capture du bureau.

## Périmètre et réalisation

- Fetch/pull **fast-forward** `1084484` → `da77207`, arbre initial propre, dépôt confirmé privé. Mandat complet,
  audit précédent et continuité relus. La validation source de `b4d0360` ne vaut pas acceptation esthétique.
- Démo indépendante : navigation contextuelle, en-tête/collection, galerie 3 × 2, liste fictive, composition fictive,
  panneau de carte et aperçu Coach sans modèle. Six concepts QPainter originaux, code/art MIT; aucune carte TCG réelle.
- Palette/emblème BrainBall autorisés réutilisés; `CardArt` hérité (hover 220 ms) et `AnimatedStack` (onglets/détails
  180 ms). Zoom/lift/glow à la peinture, pixmaps en mémoire, voisins immobiles. Sélection or distincte et focus clavier.
- Aucun timer de boucle; séquence bornée sur demande. Mouvement réduit, masquage et fermeture arrêtent les effets.
- **Cinq fichiers ajoutés seulement**, dans `demos/premium_decklab/` et `tests/test_premium_decklab_demo.py`.
  Diff nul sur `src/`, `scripts/`, version et dépendances. Aucun changement ni intégration au programme de production.

## Tests et limites

| Passe isolée | Résultat |
|---|---|
| Ciblée `python scripts/local_gate.py -k premium_demo --keep` | 6 cas démo passés; 130 Qt existants non sélectionnés; sortie 0 |
| Native Windows, même copie isolée, échelle Qt 125 % | 6/6 passés, sortie 0; démarrage `--smoke` visible, six cartes, trois onglets |
| **Porte complète `python scripts/local_gate.py`** | **130 Qt + 1645 cœur passés, 3 ignorés, zéro échec, sortie 0** |

**PORTE LOCALE VERTE** : compilation/hygiène vertes; Qt 82 s, cœur 637 s, **1775 passés au total**.
Source testée identique au commit de code. Tous les pytest dans les copies du gate, sans données personnelles.
Cas : démarrage hors ligne, SQLite/réseau/chemins privés bloqués par le test, images distinctes, frames intermédiaires,
clavier/sélection/détails, onglets, durée, mouvement réduit, arrêt des timers au masquage, grille stable à 1100/1500 px.
Essai natif complémentaire : largeur logique 1100, DPR **1,25**, capture 1375 px, défilement horizontal **0**.
Python 3.13.15 / PySide6 6.11.2 existants; FFmpeg/Pillow déjà disponibles, aucune installation.
Limites : sombre seulement; barre latérale contextuelle; défilement vertical pour voir toutes les cartes;
repli d'encodage Pillow seul non exercé. Aucun réglage DPI Windows modifié. Pas de réception de l'app installée.

## Confidentialité, Git et STOP

Prévol RUNTIME_READY : base propriétaire non ouverte, zéro écriture/réseau par le prévol. Démo sans Services/Store,
SQLite, compte, LLM, collecte ou root personnel. Captures uniquement de la fenêtre synthétique et art fictif.
Installation 0.9.5 hotfix et sauvegardes conservées sans accès; public 0.9.3 inchangé. Aucun Setup, build binaire,
tag, push/release public ou version modifiée. Aperçus restent locaux ignorés; aucune donnée privée dans les commits.

Code poussé privé et HEAD distant vérifié au SHA exact `f5f751f`; GitHub **0 statut, 0 check, 0 run**.
Agrégat `pending` faute de statuts, aucun run en attente; aucune CI verte revendiquée. Un commit de rapport assaini;
HEAD distant et statuts au SHA final contrôlés après push. **AWAITING_AUDIT / NOT_RELEASE_READY** : STOP audit
ChatGPT et jugement visuel propriétaire. Aucune intégration, autre page, installation ou publication autorisée.
