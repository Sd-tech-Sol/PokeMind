# Planches avant / après — le style des boutons d'idées partout (2026-11-19, D-318)

Chaque image met côte à côte la même vue : **AVANT** (code du commit `811f8b4`, style des boutons d'idées
appliqué à quelques endroits seulement) et **APRÈS** (style des boutons d'idées par défaut dans toute
l'application : Segoe UI 14 px demi-gras, couleur du texte normal). Seules exceptions : les titres de page et de
section et les gros chiffres des tuiles et des anneaux (même police, taille et graisse inchangées). Les textes
d'aide gardent leur gris, à la même police et à la même graisse.

Tout est **inventé** (mêmes données que `coherence/` : 18 parties, decks et cartes « Synthétique N », discussion
du Coach). Aucune donnée personnelle, aucun réseau, aucun modèle. Rendu hors écran avec les polices Windows.
Les images sans suffixe sont à la taille habituelle (1500 × 940); celles en `-1100x700` sont à la plus petite
fenêtre, où la carte Deck actif prend sa forme courte.

| Image | Ce qu'il faut regarder |
|---|---|
| `01-vue-ensemble-*` | Libellés des tuiles, liste Saison, « À travailler », carte Deck actif (nom, « 60 cartes · Mon deck », « 18 parties », « 8 V · 9 D », « Toutes mes parties, tous decks ») |
| `01-vue-ensemble-statistiques-1…4-*` | Les quatre onglets (Bilan, Adversaires, Tours, Actions) : onglets, liste « Vues détaillées », libellés et nombres des barres, mot sous le chiffre de l'anneau |
| `02-combats-*` | Grille (Deck adverse, V, D, ?, Parties et toutes les lignes), champ de filtre, tuiles, badge de la partie, frise; à 1100 × 700 la page défile et le résumé de l'adversaire est entier |
| `03-decklab-1…4-*` | Galerie (noms et codes des cartes, « ×N »), Liste texte (plus en Consolas), Statistiques, Classement; pastilles et boutons |
| `04-cartes-meta-*` | Classeur, champs de recherche, fiches |
| `05-apprentissage-*` | Tuiles, observations, bilans, plans, historique |
| `06-reglages-1…6-*` | Les six onglets : libellés, explications grises, listes, cases |
| `07-terminal-*` | Boutons de lancement (à 1100 × 700 ils passent à la ligne au lieu d'être coupés) |

Le Coach, le menu de gauche, la barre d'état et la carte Deck actif sont visibles sur chaque image.

Pour les refaire (captures complètes dans `build/qa-global/`, ignoré par Git) :

```
python scripts/qa_premium_look.py --set global --label avant --baseline-ref 811f8b4
python scripts/qa_premium_look.py --set global --label apres --baseline-ref 43e7678
python scripts/qa_premium_look.py --set global --sheets
```

**Refaites le 2026-11-20 (D-320)** : les quatre `06-reglages-4-data-*`. Leur champ « Dossier de données »
montrait un chemin du dossier temporaire du profil Windows, donc le nom du compte. Le script travaille maintenant
dans un dossier neutre (`C:\PokeMind-demo\…`) et refuse toute capture dont un widget visible contient le profil,
le chemin du dépôt ou le nom du compte. Les 72 autres planches, régénérées de la même façon, sont restées
identiques (octet pour octet, ou à quelques pixels d'animation près) : elles ne montraient pas ce chemin.
