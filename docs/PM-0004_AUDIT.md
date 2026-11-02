# Audit TCGdex — PM-0004

Consultation et témoins HTTP effectués le **2026-10-11**. Les réponses externes ont
été traitées comme données non fiables; aucune donnée de deck, combat, crédit ou
identifiant utilisateur n'a été envoyée.

## Sources primaires consultées

| Source | Constat vérifié le 2026-10-11 |
|---|---|
| <https://tcgdex.dev/rest> | API REST V2, racine documentée `https://api.tcgdex.net/v2/{lang}`. |
| <https://tcgdex.dev/rest/cards> | `GET /v2/{lang}/cards` retourne un tableau de `CardBrief`; détail par ID. |
| <https://tcgdex.dev/rest/sets> | `GET /v2/{lang}/sets` retourne des `SetBrief`; détail par ID. |
| <https://tcgdex.dev/reference/card> | Champs communs et champs Pokémon, Dresseur et Énergie; plusieurs sont optionnels. |
| <https://tcgdex.dev/rest/filtering-sorting-pagination> | Pagination activée par `pagination:page`; `pagination:itemsPerPage` vaut 100 par défaut lorsqu'activée. |
| <https://tcgdex.dev/status> | Couverture variable selon les langues; le site renvoie vers `api.tcgdex.net/status`. Ce dernier a retourné du HTML, pas du JSON, lors de l'audit. |
| <https://github.com/tcgdex/cards-database> | Dépôt multilingue, branche `master`, licence déclarée MIT; avertissement d'absence d'affiliation Nintendo/The Pokémon Company. |
| <https://github.com/tcgdex/cards-database/blob/master/LICENSE> | Texte MIT, copyright TCGdex 2021. |

Les pages de documentation secondaires peuvent être imprécises; le code n'accepte
que les réponses réellement validées de `api.tcgdex.net`. Aucun quota ou taux
chiffré, aucune politique `robots` propre à l'API et aucune condition séparée de
service API n'ont été trouvés dans les pages consultées. Cela **n'autorise pas** une
collecte agressive : PM-0004 limite l'essai réel et impose budgets, intervalle,
cache, reprise, taille maximale et `Retry-After`.

## Témoins publics bornés

- `GET /v2/en/cards?pagination:page=1&pagination:itemsPerPage=3` : HTTP 200,
  JSON, trois éléments; même comportement en `fr` avec noms localisés.
- `GET /v2/en/sets?...itemsPerPage=3` et `fr` : HTTP 200, trois éléments.
- `GET /v2/en/cards/base1-1` et `fr` : HTTP 200; même ID/local ID, objets détaillés
  avec catégories localisées et champs optionnels.
- Langue fictive et ID inexistant : HTTP 404 JSON. Page très éloignée : HTTP 200,
  tableau vide.
- `GET /v2/en/sets/base1` : champs `tcgOnline` et `abbreviation` observés dans le
  détail, absents du bref; ils seuls peuvent soutenir un diagnostic de code de deck.

L'essai du logiciel a ensuite consommé deux tranches de **8 requêtes** chacune,
sans erreur ni 429. Il a progressé des pages 1 à 2 et a conservé deux détails de
cartes en FR/EN. Les décomptes sont ceux du cache local à cet instant, pas ceux du
catalogue mondial TCGdex.

## Choix et droits

L'API REST est l'unique pipeline. Le dépôt `cards-database` a été comparé seulement
comme origine/licence : son miroir complet dépassait environ 100 000 Kio selon les
métadonnées GitHub consultées et ferait double emploi avec la reprise REST. Aucun
clone ni deuxième synchroniseur n'a été créé.

La licence MIT déclarée couvre le dépôt de base de données, mais les marques,
illustrations et autres droits Pokémon demeurent distincts. PokeMind ne télécharge
pas d'images, n'inclut aucun dump de cartes dans Git et conserve textes/cache
uniquement dans la SQLite privée avec attribution URL/date/empreinte. En l'absence
de quota API publié, une synchronisation massive non bornée n'a pas été exécutée.

## Limites explicites

- TCGdex n'est pas une preuve de disponibilité dans Pokémon TCG Live, de légalité
  Standard/Expanded, de possession, de coût, de méta ou de puissance.
- Les langues ont des couvertures différentes. `absent`, `not_fetched` et
  `network_error` ne sont jamais confondus.
- Une impression garde son ID TCGdex même si une autre porte le même nom. Aucune
  équivalence fonctionnelle ou réimpression n'est affirmée dans PM-0004.
- Le statut de l'API et ses conditions peuvent changer; ils devront être revérifiés
  avant toute automatisation future.
