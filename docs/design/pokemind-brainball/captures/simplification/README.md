# Planches avant / après — simplification (PM-UI-SIMPLIFICATION-021, D-316)

Chaque image met côte à côte la même vue : **AVANT** (code du commit `e8479cb`, fin du look premium) et
**APRÈS** (textes simplifiés, mise en page allégée, mode avancé).

Tout est **inventé** : rapport de 18 parties, decks, cartes « Synthétique N », discussion du Coach. Aucune donnée
personnelle, aucune illustration Pokémon, aucun réseau, aucun modèle. Fenêtre de 1500 × 940 px, sauf les vues
« étroit » (1100 × 700 px).

| Image | Ce qu'il faut regarder |
|---|---|
| `01-vue-ensemble-*` | « Dernière mise à jour : 16 novembre 2026 », bouton ⓘ, « Adversaire non identifié », V/D plus répétés |
| `02-combats-*`, `08-combats-partie-sombre` | Colonnes « Deck adverse », V, D, ?, « Parties »; frise sans « inconnu » |
| `03-decklab-*` | Nom du deck d'abord, pastilles « Mon deck » et « Légalité à vérifier », 5 cartes par rangée, deux rangées |
| `09-decklab-classement-sombre` | Le rang et le taux public restent ici seulement |
| `04-cartes-meta-sombre`, `05-apprentissage-sombre` | Une phrase d'aide; légende « Bleu : victoires · Rouge : défaites » |
| `06-reglages-sombre` | Cases à cocher avec bordure; nouvelle option « Mode avancé » (décochée) |
| `07-terminal-sombre` | « Codex », « Claude Code (sans confirmations) »; page visible seulement en mode avancé |
| `10-coach-vide-sombre` | Menu « ⋯ » et trois idées de questions quand la discussion est vide |

Dans les vues « après », le menu de gauche n'a plus l'entrée Terminal (mode avancé décoché), sauf sur `07`.
La barre de titre Windows n'apparaît pas dans ces captures hors écran.

Pour les refaire (captures complètes dans `build/qa-simplification/`, ignoré par Git) :

```
python scripts/qa_premium_look.py --set simplification --label avant --baseline-ref e8479cb
python scripts/qa_premium_look.py --set simplification --label apres
python scripts/qa_premium_look.py --set simplification --sheets
```
