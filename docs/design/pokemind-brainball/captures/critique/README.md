# Planches avant / après — les 10 points de la critique (PM-UI-CRITIQUE-022, D-317)

Chaque image met côte à côte la même vue : **AVANT** (code du commit `3bf0ee3`, fin de la simplification 021)
et **APRÈS** (les 10 points de la critique du look premium, comparée à `references/decklab-premium-target.png`).

Tout est **inventé** : rapport de 18 parties, decks, cartes « Synthétique N », discussion du Coach. Aucune donnée
personnelle, aucune illustration Pokémon, aucun réseau, aucun modèle. Fenêtre de 1500 × 940 px, sauf les vues
« étroit » (1100 × 700 px). Les mêmes vues à 125 % sont dans `build/qa-simplification/` (non versionné).

| Image | Ce qu'il faut regarder (numéro du point) |
|---|---|
| `01-vue-ensemble-*` | Bannière d'environ 90 px (4); « À travailler » sous les tuiles (4); tuiles au gabarit unique (10) |
| `02-combats-*` | Tableau à la hauteur de ses rangées, sans boîte vide dessous (7); chiffres à droite, flèche de tri au-dessus du titre de colonne (9) |
| `08-combats-partie-sombre` | Détails visibles une fois l'adversaire choisi (7); un seul bouton plein (8) |
| `03-decklab-*` | Vignette et nom du deck en titre, bouton « Changer de deck » (3); Copier et Exporter dans le bandeau (8); cartes nues, ×N en pastille, code d'extension plus discret (5) |
| `03-decklab-etroit-*` | À 1100 px : « Ajouter mon deck… », « Copier » et « Exporter… » sur la même rangée (8) |
| `09-decklab-classement-sombre` | Style de tableau unique, sélection douce avec filet à gauche (9); dates « 18 octobre 2026 → 14 novembre 2026 » (10) |
| `05-apprentissage-sombre` | Trois tuiles de chiffres, « Mise à jour : 16 novembre 2026 » sous les tuiles (10) |
| `10-coach-vide-sombre` et toutes les vues | Bulles du Coach sans chevauchement (1); contours intérieurs discrets (2); casse normale, échelle typographique (6) |

La barre de titre Windows n'apparaît pas dans ces captures hors écran.

Pour les refaire (captures complètes dans `build/qa-simplification/`, ignoré par Git) :

```
python scripts/qa_premium_look.py --set simplification --label avant --baseline-ref 3bf0ee3
python scripts/qa_premium_look.py --set simplification --label apres
python scripts/qa_premium_look.py --set simplification --sheets
```

`--sheets` écrit dans `captures/simplification/` : déplacer ensuite les images ici et restaurer ce dossier
(`git checkout -- docs/design/pokemind-brainball/captures/simplification`).
