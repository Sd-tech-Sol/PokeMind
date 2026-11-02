# AUDIT CHATGPT — PM-0003T + nouvelle fonction importable, 2026-10-10

## Décision
PM-0003T est **livrée sur GitHub et acceptée pour poursuivre**, avec réserves de preuve pour les données strictement locales. La prochaine tranche PM-0003E autorise le **sens inverse** du flux de deck : préparer/exporter un vrai texte de 60 cartes que l'utilisateur collera dans « Créer un deck → Importer un deck du presse-papiers » de Pokémon TCG Live. PM-0003E est un pont d'export, **pas encore un optimiseur de métagame**.

## Preuves du dernier travail
- Branche `work/pm-0003t`, HEAD vérifié `b9678ac73a88c2f9a7fe3f3e8c5eb3c186a71a64`.
- Comparaison base `900f1435e7dbb339d7d85ee13df5c0eb033ce2aa` vers HEAD : un commit, **uniquement** `.orchestrator/{RESULT,HANDOFF,NEXT_ACTION}.md`. Aucun changement au code et aucun fichier privé ajouté dans ce commit.
- Codex rapporte prévol `53 passed`, schéma SQLite 3 et intégrité `ok`; trois journaux valides/uniques, rapport `n=5, W=4, L=1, inconnue=0` sur `principal`, 234 événements nouveaux; capture de profil convertie en un instantané JSON privé.
- Les chiffres, soldes, les journaux, la capture et la base SQLite locale ne sont **pas indépendamment vérifiables depuis GitHub**. Les cinq parties permettent un premier bilan exploratoire seulement.
- Rapport Codex : **trois faux positifs de noms de cartes** dans les observations. Aucun n'a été utilisé pour les constats; ce problème demeure à corriger dans une autre tranche de parsing avant de prétendre connaître le deck depuis les logs.

## Recherche externe : mécanisme et changements officiels
- Photo fournie par l'utilisateur : écran TCG Live « Créer un deck » avec « IMPORTER UN DECK DU PRESSE-PAPIERS » et un choix de mode « DIRECT ».
- Pokémon, article officiel du 21 avril 2026 : le nouvel éditeur peut sélectionner automatiquement les **cartes possédées** ou les **versions possédées les plus rares**; cartes non possédées, non fabricables et invalides distinguées dans le jeu. https://www.pokemon.com/uk/news/pokemon-tcg-live-landscape-layout-and-deck-editor-updates
- Pokémon, article officiel été 2026 : éditeur avec statistiques W/L des decks et « Exchange All » permettant de fabriquer les cartes manquantes admissibles en une opération. L'action réelle appartient au joueur, après vérification de son solde et des coûts. https://www.pokemon.com/us/pokemon-news/celebrate-play-pokemon-with-pokemon-tcg-lives-mid-year-event
- Exemple de listes `Pokémon: N`, `Trainer: N`, `Energy: N` et lignes `quantité nom CODE numéro` sur Pokémon.com (stratégies mars 2025) : https://www.pokemon.com/us/features/pokemon-trading-card-game-live-starter-deck-strategies-march-2025
- Attention : un problème de **comptage des intitulés uniques vs quantités** a été signalé sur forums officiels en déc. 2024 (pas établi s'il persiste en 2026). Tester le comportement réel avant de fixer le sérialiseur. https://community.pokemon.com/en-us/discussion/15230/decklist-export-incorrectly-lists-counts

## Architecture voulue
1. PokeMind collecte/analyse combats et profil, puis connaît les versions de decks confirmées lorsque l'utilisateur en exporte une.
2. Un générateur local formate un deck de 60 cartes validé, code d'extension et numéro si connus, en un `.txt` **importable dans TCG Live**, **sans annotation** dans le presse-papiers.
3. Dossier **privé et ignoré Git** : `data/local/decks/import_ready/`, un fichier par deck/version et métadonnées séparées (provenance, absence de preuve de collection, incertitudes).
4. L'utilisateur copie le texte, choisit « Importer » dans le jeu, peut sélectionner ses cartes possédées et vérifier ensuite les cartes manquantes/les crédits nécessaires dans TCG Live. **Aucun achat/fabrication automatique par Codex/PokeMind.**
5. Une fois que catalogue TCGdex et métagame/Limitless sont intégrés et vérifiés (ROADMAP), `$meilleur-deck` proposera des decks compétitifs optimisés et les exportera dans ce même dossier; ne pas annoncer cet algorithme comme déjà réalisé.

## Blocage de vérification
Ne pas promettre qu'un texte uniquement synthétique est accepté par le client réel : demander un test rond-trip avec un export réel de deck volontaire fourni localement. Aucun nom de carte issu de la base de l'utilisateur ni image dans GitHub. 
