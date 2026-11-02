# LOT A — audit des sources publiques (2026-10-13)

## Méthode et portée

Audit manuel borné, sans compte ni clé. Les URL sont des données non fiables : aucun
contenu reçu n'a été exécuté. Un contrôle `HEAD` avec redirections autorisées a
confirmé un statut HTTP 200 pour les 14 URL Pokémon du registre local le 2026-10-13.
Ce signal prouve seulement l'accessibilité; il ne transforme pas un PDF non lu en
source normative et ne prouve pas que son contenu n'a pas changé.

## Pokémon officiel

- Le livret officiel [Pokémon Trading Card Game Rules](https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/rulebook/par_rulebook_en.pdf)
  a été consulté directement. Les pages 20–21 définissent le nom utilisé pour les
  copies, exactement 60 cartes, au plus quatre cartes du même nom sauf Énergies de
  base et au moins un Pokémon de base. Les appendices contiennent des règles
  spéciales supplémentaires : PokeMind ne prétend donc pas en avoir un registre
  exhaustif.
- La page [Competitive Pokémon Rules and Formats](https://play.pokemon.com/en-us/resources/rules/)
  était accessible et conserve la séparation rotation/réimpressions/errata.
- Le portail [Resources and Documents](https://play.pokemon.com/en-ca/resources/documents/)
  était accessible, mais un portail n'atteste pas le contenu de chaque PDF lié.
- Les 14 résultats HTTP sont consignés seulement comme preuve d'accessibilité de la
  session. `pokemon-tcg-handbook-pdf` et `pokemon-tcg-errata-pdf` restent
  `non_verified` parce que leur contenu n'a pas été audité intégralement dans ce lot.

## TCGdex

- La documentation REST v2 confirme HTTPS, GET et JSON :
  [Getting Started](https://tcgdex.dev/rest).
- La liste des cartes retourne des objets `CardBrief` et accepte filtres/tri/pagination :
  [Searching for cards](https://tcgdex.dev/rest/cards). La documentation ne fournit
  pas, dans les pages consultées, un total global contractuel ni une garantie de
  complétude FR/EN; PokeMind garde donc ce dénominateur `unknown` tant qu'un scan
  n'est pas terminé.
- Le dépôt public [tcgdex/cards-database](https://github.com/tcgdex/cards-database)
  annonce la base sous licence MIT. Les marques et images restent distinctes;
  PokeMind ne télécharge pas les médias.

## Limitless et Trainer Hill

- La documentation [Developer Guides](https://docs.limitlesstcg.com/developer)
  confirme que les endpoints publics n'exigent pas de clé sauf `/games/{id}/decks`,
  et que les limites sont exposées par en-têtes. Cette exception n'est jamais appelée.
- La page [Tournaments](https://docs.limitlesstcg.com/developer/tournaments.html)
  confirme la base `https://play.limitlesstcg.com/api`, la pagination et les champs
  publics de détails, standings et pairings, dont `isPublic`, `isOnline` et BO1/BO3/BO5.
- La racine `https://www.trainerhill.com/` était accessible, mais aucune documentation
  d'API publique, condition d'automatisation ni endpoint autorisé n'a été trouvé dans
  les sources primaires consultées. État LOT A : `BLOCKED_WITH_REASON`; aucun scraping
  de l'interface, de Labs ou d'un endpoint privé n'est effectué.

## Conséquence d'implémentation

Pokémon officiel reste normatif, TCGdex décrit les impressions et Limitless fournit
un échantillon compétitif descriptif. Une absence, une source partielle ou une fenêtre
expirée produit `unknown`; aucun fournisseur secondaire ne remplace une preuve
officielle de légalité.
