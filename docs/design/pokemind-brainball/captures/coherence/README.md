# Planches avant / après — cohérence des barres et des textes (2026-11-19, D-318)

Chaque image met côte à côte la même vue : **AVANT** (code du commit `617642c`) et **APRÈS** (une seule barre
arrondie partout, texte courant des pages réglé comme les bulles du Coach).

Tout est **inventé** (mêmes données que `simplification/` : 18 parties, decks et cartes « Synthétique N »,
discussion du Coach). Aucune donnée personnelle, aucun réseau, aucun modèle. Fenêtre de 1500 × 940 px, rendu hors
écran : Windows n'y donne que la famille « Segoe UI Variable »; dans l'application, la police est « Segoe UI
Variable Text ».

| Image | Ce qu'il faut regarder |
|---|---|
| `01-vue-ensemble-*` | Résumé dans un cadre de bulle, police et interligne du Coach; ligne « À travailler » comme les boutons d'idées |
| `02-statistiques-bilan-*` | « Défaites par deck adverse » : barres arrondies de 10 px avec piste, comme Combats |
| `03-statistiques-adversaires-*` | Barres empilées arrondies, petit espace entre victoires, défaites et sans résultat |
| `04-statistiques-tours-*`, `05-statistiques-actions-*` | Même barre, en bleu, même épaisseur |
| `06-combats-*` | Résumé de l'adversaire dans un cadre de bulle; détails de la partie dans le même genre de cadre |
| `07-apprentissage-*` | Observations dans un cadre de bulle; « Tes bilans par adversaire » avec la barre de Combats |

Pour les refaire (captures complètes dans `build/qa-coherence/`, ignoré par Git) :

```
python scripts/qa_premium_look.py --set coherence --label avant --baseline-ref 617642c
python scripts/qa_premium_look.py --set coherence --label apres
python scripts/qa_premium_look.py --set coherence --sheets
```
