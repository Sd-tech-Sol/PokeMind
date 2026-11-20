# Captures « look premium » (synthétiques)

Refonte visuelle de la vraie `MainWindow` vers la cible
[`decklab-premium-target.png`](../../references/decklab-premium-target.png), branche `work/ui-premium-look`.

Produites par `python scripts/qa_premium_look.py --label avant|apres` : copie isolée du dépôt, rendu hors écran,
polices de Windows. Rapport, deck, images de cartes et discussion **inventés** : aucune donnée personnelle,
aucune illustration Pokémon, aucun réseau, aucun modèle.

- `avant/` : état 0.9.5, avant la refonte (`--baseline-ref work/pm-v1-lotj-final-readiness-windows`); refait à
  l'étape 4 seulement pour montrer, comme dans `apres/`, la première carte de la galerie sélectionnée.
- `apres/` : état de la branche, remplacé à chaque étape (l'historique Git garde chaque étape).

Chaque dossier contient les sept pages en thème sombre (1500 × 940), trois pages en thème clair, Deck Lab en
fenêtre minimale 1100 × 700 dans les deux thèmes, et deux pages à 125 % (`QT_SCALE_FACTOR=1.25`).
