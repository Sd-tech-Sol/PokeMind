# Sources publiques H — campagne bornée distincte de la QA

Observation Codex : 2026-10-14 Québec, 2026-10-15 03:37 UTC. Campagne reproductible
`python scripts/lot_h_public_campaign.py --execute-public-campaign` dans une base
neuve jetable sous le répertoire privé local. Aucune ouverture de la base du joueur,
aucune image, collection, deck, journal ou information de compte envoyée au réseau.
Les participants publics sont normalisés localement par le collecteur existant;
ni noms, identifiants ni listes de cartes ne figurent dans ce rapport ou dans Git.

Budget global 32 GET, timeout 10 s, intervalle 0,5 s; réellement **29 GET** :

| Source | GET / budget | Observation agrégée | Limite |
|---|---:|---|---|
| TCGdex | 16 / 16 | 117 sets et 140 impressions dans l'union locale; 3 détails EN et 3 FR; 100 membres de page 1 dans chaque index cartes | découverte incomplète, dénominateurs inconnus; détails FR/EN de l'union ne sont pas ceux du snapshot |
| Limitless | 11 / 14 | 3 snapshots publics Standard/PTCGL/online; 553 pairings, 497 éligibles et classifiables; 246 placements classifiés | fournisseur status unknown; échantillon sélectionné, aucun winrate ni finalisation inférée |
| Pokémon officiel | 2 / 2 | rotation non lisible par client; portail HTTP 200 non tronqué | contenu normatif complet non revu, aucune assertion ajoutée |

Limitless : événements observés entre 2026-10-14 22:30 et 2026-10-15 01:00 UTC.
Swiss BO1 : 521 pairings / 2 tournois; Swiss BO3 : 32 / 1 tournoi.
Exclusions : 25 byes/pertes automatiques et 31 doubles défaites. Le quota fournisseur
restant affichait 44. Ce n'est pas le métagame mondial ni une estimation de rendement
personnel. La base de campagne est fermée puis retirée par le contexte temporaire;
ces résultats n'actualisent aucune connaissance personnelle persistante.

## Provenance et droits

[Pagination TCGdex](https://tcgdex.dev/rest/filtering-sorting-pagination) et
[licence de la base](https://github.com/tcgdex/cards-database/blob/master/LICENSE),
consultées pendant H : MIT pour le dépôt, droits des marques/illustrations séparés;
aucune image ni copie de textes de carte dans Git.
[API Limitless](https://docs.limitlesstcg.com/developer.html) et
[tournois](https://docs.limitlesstcg.com/developer/tournaments.html) : endpoints
publics allowlistés, quotas/redirections comptés, aucun `/games/.../decks` protégé.
Trainer Hill demeure `BLOCKED_WITH_REASON` : accès automatisé autorisé non établi,
aucun grattage de remplacement tenté.

[Rotation officielle](https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement)
et [portail de règles](https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources)
ont aussi été consultés; le rendu disponible ne fournit pas une revue complète des
documents normatifs. Un HTTP 200 peut contenir un simple portail/iframe. **Aucune
nouvelle règle verified** n'est créée par ces observations.

## Logiciel livré et suite

Les pages d'index sont enregistrées avec membres, dates et empreinte dans metadata,
transactionnellement avec le checkpoint. Reprise héritée sans page 1 = scan partiel;
doublons/gaps = dénominateur inconnu. Une fin confirmée fournit seulement le total
des membres du scan observé; pagination mouvante ≠ snapshot atomique fournisseur.
Le ratio des détails du snapshot exclut stale; les 404 restent séparées. Ni Live,
ni légalité, ni variants/reprints complets ne sont inférés de ces compteurs.

`knowledge review-official` lie une déclaration de revue intégrale au SHA d'une
réponse entière HTTP 200 non tronquée, avec version, décision et audit conservé.
Une modification rend la revue stale. Elle ne change pas les assertions; la file
demande encore leur réconciliation dans le registre versionné. Les gates restent
conservatrices pour rotations, structure 60/exceptions, bans, Expanded, promos,
réimpressions, errata et compatibilité Live. Les observations futures sont exclues
de la couverture normative et de la couverture méta datée.
