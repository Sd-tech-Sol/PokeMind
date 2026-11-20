# Planches avant / après — texte des pages comme les boutons d'idées (2026-11-19, D-318)

Chaque image met côte à côte la même vue : **AVANT** (code du commit `5880563`, texte réglé comme les bulles du
Coach) et **APRÈS** (texte réglé comme les boutons d'idées du Coach : Segoe UI 14 px demi-gras, couleur `text`,
cadres en dégradé avec bordure bleue `neon_soft` et coins de 10 px, texte aligné à gauche).

Tout est **inventé** (mêmes données que `coherence/` : 18 parties, decks et cartes « Synthétique N », discussion
du Coach). Aucune donnée personnelle, aucun réseau, aucun modèle. Fenêtre de 1500 × 940 px, rendu hors écran.

| Image | Ce qu'il faut regarder |
|---|---|
| `01-vue-ensemble-*` | Résumé en demi-gras dans un cadre en dégradé à bordure bleue; « À travailler » dans la même graisse; titres et gros chiffres inchangés |
| `02-statistiques-bilan-*` | Libellés des barres (« Famille inventée A · 3 défaites sur 5 parties ») en demi-gras |
| `06-combats-*` | Résumé de l'adversaire et détails de la partie dans le cadre des boutons d'idées |
| `07-apprentissage-*` | Observations, plans, bilans et historique en demi-gras, cadres en dégradé à bordure bleue |

Le diagnostic « miroir » (l'archétype signalé) n'a pas d'image : il ne sort que des comptes, voir `.orchestrator/RESULT.md`.

Pour les refaire (captures complètes dans `build/qa-style/`, ignoré par Git) :

```
python scripts/qa_premium_look.py --set style --label avant --baseline-ref 5880563
python scripts/qa_premium_look.py --set style --label apres
python scripts/qa_premium_look.py --set style --sheets
```
