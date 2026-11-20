# PM-UI-CRITIQUE-022 — TERMINÉ / EN ATTENTE DU PROPRIÉTAIRE

2026-11-18, Québec. GO direct du propriétaire dans la session Claude Code (**D-317**) pour appliquer les 10 points
de la critique en lecture seule du look premium (comparaison avec `references/decklab-premium-target.png`).
Apparence et mise en page seulement. Branche `work/ui-premium-look`, après `3bf0ee3`. **Rien n'est poussé.**
Rapport 021 archivé : `archive/2026-11/RESULT_avant_022_3bf0ee3_2026-11-18.md`. L'audit ChatGPT de 019 reste
attendu, indépendamment.

## Commits (un par point, lot A puis lot B)

| Point | Commit | Contenu |
|---|---|---|
| 1 | `7324933` | Coach : bulles sans chevauchement ni coupure (marge 12 px, 10 px entre bulles, étiquette dedans, 85 % au plus) |
| 2 | `4d4e059` | Un seul contour lumineux par panneau; cadres intérieurs en surface, bordure à 30 % |
| 6 | `74f2762` | Échelle typographique (titre 28, sous-titre 15, corps 14, notes 12 atténuées), casse normale |
| 9 | `0363daf` | Un seul style de tableau; en-têtes alignés comme leur colonne, chiffres à droite |
| 10 | `e230c19` | Un seul gabarit de tuile; dates « 16 novembre 2026 » partout; « Mise à jour » hors des tuiles |
| 3 | `21d11cc` | Deck Lab : vignette et nom du deck en titre, bouton « Changer de deck » |
| 5 | `c760564` | Galerie : cartes nues, cadre au survol et à la sélection, ×N en pastille, code atténué |
| 7 | `2f99ea3` | Tableaux à la hauteur de leurs rangées; détails de Combats après le choix d’un adversaire |
| 8 | `eff8ecd` | Un seul bouton plein par page, boutons de 36 px, Copier et Exporter dans le bandeau |
| 4 | `f368ad1` | Vue d’ensemble : bannière d’environ 90 px, « À travailler » sous les tuiles |
| 10 | `536acc9` | Suite du point 10 : un test du cœur attendait encore une période ISO (trouvé par la porte) |

Aucune logique, aucun service, aucune donnée modifiés. Les éléments « pas faisables proprement en Qt Widgets »
de la critique (halo diffus et verre, contours en dégradé, barre de titre intégrée, transitions de survol et
lueur de texte en QSS, menus déroulants arrondis avec ombre, illustrations) restent hors périmètre.

## Réponse à la question posée (point 8)

**Copier et Exporter tiennent dans le bandeau du deck à 1100 px** : à 1100 × 700, ils sont sur la même rangée
que « Ajouter mon deck… » (le bandeau a trois rangées : titre et pastilles; Changer de deck, Favori, Deck
principal; Ajouter, Copier, Exporter); à 1500 px, les six commandes tiennent sur une rangée sous le titre. Pour y arriver,
leurs mots sont courts : « Copier » et « Exporter… »; les libellés complets (« Copier les 60 cartes »,
« Exporter en fichier texte… ») sont dans leurs infobulles et leurs noms accessibles. La rangée sous la galerie
ne garde que la comparaison.

## Choix à signaler au propriétaire

1. Tri des tableaux : la flèche de tri est **au-dessus** du titre de colonne (comme l'Explorateur Windows). La
   flèche native de Qt se dessinait par-dessus un titre aligné à droite (« D▾ »); placée à droite, Qt effaçait le
   titre de la colonne triée.
2. Apprentissage : les tuiles « Parties observées » et « Adversaires suivis » sont grises, « Plans à tester »
   jaune; le bleu et le rouge restent réservés aux victoires et aux défaites.
3. Vue d'ensemble : les chiffres des tuiles passent de 35 à 28 px (gabarit unique, comme Combats et Apprentissage).
4. Cartes & méta : « Rechercher » n'est plus un bouton plein (Entrée lance aussi la recherche); le seul bouton
   plein de la page est « Télécharger le catalogue », quand le catalogue est absent.
5. Combats : le séparateur vertical déplaçable entre le tableau et les détails est retiré; les détails
   apparaissent sous le tableau dès qu'un adversaire est choisi, et la frise défile.
6. Dates en toutes lettres partout, y compris dans la note du Coach pour un deck adverse ajouté
   (« PUBLIC · 18 novembre 2026 » au lieu de « PUBLIC/2026-11-18 ») et l'heure de la dernière vérification des
   mises à jour (« 18 novembre 2026 · 14:05 »).
7. Bannière : la carte PokeMind y est dessinée à 62 px (au lieu de 104); son animation est mise à l'échelle.
8. Deck Lab à 1100 px : le bandeau garde trois rangées, comme avant; la rangée Copier / Exporter sous la galerie
   a disparu, la galerie gagne donc un peu de hauteur.

## Vérifications

- **Thème clair, 1100 × 700 et 125 %** : captures de toutes les pages dans les deux thèmes, aux deux tailles et
  à 125 %, relues image par image; aucun débordement horizontal (tests de défilement latéral verts à 1100 et 1200).
- **Contraste** : tests verts. Les bordures intérieures à 30 % (`inner_line`, environ 1,6:1) sont décoratives et
  jamais porteuses d'information; les notes atténuées (12 px, code d'extension 11 px) gardent la couleur
  `muted`, testée à 4,5:1 au moins dans les deux thèmes; texte sur sélection de tableau ≥ 4,5:1.
- **Mouvement réduit inchangé** : aucune animation ajoutée; tests du mouvement réduit verts.

## Preuves

| Porte complète isolée | Qt réussis | Cœur réussis | Échecs | Ignorés | Total réussi |
|---|---:|---:|---:|---:|---:|
| `python scripts/local_gate.py` | 200 | 1700 | 0 | 3 | 1900 |

Compilation et hygiène vertes, exit 0, sur l'arbre final du code (`536acc9`). **Une première porte complète était
rouge** (1 échec sur 1700 au cœur : `test_deck_public_stats.py` attendait encore « 2026-11-01 → 2026-11-01 » dans le
volet Sources des statistiques publiques); l'attente a été alignée sur le format unique du point 10 (`536acc9`)
et la porte relancée en entier. Résultat local, **pas une CI GitHub**. Nouveaux tests : bulles du Coach, cadres intérieurs, échelle typographique, style de tableau, gabarit
de tuile et dates, galerie, hauteur des tableaux et détails de Combats, bouton plein unique et boutons de 36 px,
bannière et « À travailler ».
Planches avant/après : `docs/design/pokemind-brainball/captures/critique/` (15 images, « avant » = `3bf0ee3`),
produites par `scripts/qa_premium_look.py --set simplification`; tout est inventé, aucune donnée personnelle,
aucune illustration Pokémon, aucun réseau, aucun modèle.

## Limites

Aucune lecture de données personnelles, de l'application installée ou du compte du Coach; aucun build, aucune
installation, aucune publication. Les largeurs (Copier et Exporter à 1100 px) sont mesurées dans les captures hors
écran avec les polices Windows, pas sur l'écran du propriétaire. **Prochaine action : le propriétaire regarde les
planches ou l'application depuis la branche, puis décide (corrections, push, suite).**
