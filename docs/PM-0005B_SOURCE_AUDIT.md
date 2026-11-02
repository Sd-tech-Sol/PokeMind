# PM-0005B — audit de la source Limitless

**Consultation :** 2026-10-12 UTC

**Source primaire :** documentation et API de la Limitless Tournament Platform.

## Pages vérifiées

| URL | Fait utilisé | Limite retenue |
|---|---|---|
| https://docs.limitlesstcg.com/developer | Les endpoints de tournoi sont accessibles sans clé; des limites s'appliquent et sont annoncées par en-têtes. | `/games/{id}/decks` exige une clé, non destinée aux projets privés : interdit dans PokeMind. |
| https://docs.limitlesstcg.com/developer/tournaments.html | Origine `https://play.limitlesstcg.com/api`; `/tournaments`, pagination, `details`, `standings`, `pairings` et champs documentés. | Les résultats proviennent de la plateforme; les participants et résultats peuvent être incomplets ou corrigés. |
| https://docs.limitlesstcg.com/developer/games | `/games` publie codes de jeu, formats, plateformes et disponibilité d'une catégorisation automatique. | `PTCGL` (plateforme) ne remplace pas `isOnline` (type de tournoi). |
| https://docs.limitlesstcg.com/organizer/reference | Tournois publics/non publics, listes ouvertes/fermées, archétypes publics possibles, formats personnalisés, règles et bans personnalisés. | Un format déclaré ou un résultat n'est pas une norme Pokémon officielle. |
| https://play.limitlesstcg.com/tos | Conditions générales de la plateforme, contenu utilisateur et restrictions de contenu. | Aucun droit général de republication massive n'est supposé; cache local minimal et attribution par URL. |
| https://play.limitlesstcg.com/privacy | Les données de compte et identifiants de jeu ont une finalité opérationnelle. | PokeMind évite la réplication permanente des noms, pays, pseudos, identifiants publics et decklists. |

La documentation ne publie pas de nombre de quota fixe durable. Le 2026-10-12 UTC,
un petit essai a observé `RateLimit: "50-in-5min"; r=49; t=300` et
`RateLimit-Policy: "50-in-5min"; q=50; w=300`. Ces valeurs sont une observation datée,
pas une promesse du fournisseur. Le client respecte `Retry-After`, limite chaque
réponse à 8 Mio, bloque les redirections hors hôte et compte chaque retry dans le
budget utilisateur.

## Endpoints réellement appelés

Essai borné : **5 GET**, sans authentification, sans cookie et sans clé.

1. `GET /api/games`;
2. `GET /api/tournaments?game=PTCG&format=STANDARD&limit=3&page=1`;
3. `GET /api/tournaments/{id}/details`;
4. `GET /api/tournaments/{id}/standings`;
5. `GET /api/tournaments/{id}/pairings`.

Résultat local privé : 1 tournoi public PTCGL Standard, date fournisseur
2026-10-11T22:30:00Z, 5 placements, 16 appariements, 9 matchs admissibles et aucun
archétype publié. Le nom du tournoi et l'ID public ne sont pas reproduits dans Git.
Les données brutes, participants et instantanés SQLite restent sous `data/local/`.

## Couverture et conclusions autorisées

- Couverture obtenue : un échantillon minuscule d'un tournoi de la Tournament
  Platform; aucune prétention sur tous les tournois mondiaux ou physiques.
- Archétypes : seulement `standing.deck.id` quand il existe. Aucun appel aux règles
  privées de classification et aucune inférence TCGdex.
- Matchups : jointure intra-tournoi; bye, double perte et résultat douteux exclus;
  BO et phase séparés; nul conservé.
- Légalité : aucune. Les résultats Limitless ne remplacent pas Pokémon officiel.
- Attribution/provenance : URL d'endpoint, UTC de récupération et SHA-256 conservés.
- Données personnelles : références HMAC locales par tournoi; noms, pays, pseudos et
  decklists ignorés lors de la validation et jamais écrits en base.

Une extraction large demeure hors périmètre tant qu'une politique d'usage et de quota
plus précise n'est pas publiée ou confirmée. PM-0005B reste manuelle et bornée.
