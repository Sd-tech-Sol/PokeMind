# PM-0006A — diagnostic personnel sourcé en lecture seule

## Commande et contrat

```powershell
python -m pokemind analyze deck <deck-id> --as-of YYYY-MM-DD --format standard --platform live --json
```

`standard|expanded` et `live|in_person` sont des contextes distincts. `--as-of` est
une date ISO stricte et signifie « preuves disponibles dans le cache local à cette
date ». Il borne les combats et, pour Limitless, exige à la fois une date d'événement
et une date locale de capture `fetched_at` au plus tard à `as_of`. Cette capture ne
constitue pas une date officielle de publication du fournisseur. Un événement ancien
capturé plus tard est donc exclu avec `SNAPSHOT_NOT_AVAILABLE_AS_OF`, sans être effacé
du cache ni rendu inaccessible aux diagnostics ultérieurs. Pour la méta, `live`
correspond à `PTCGL + online=true`; `in_person` correspond à
`TABLETOP + online=false`. La commande ne fait aucun appel réseau, n'initialise pas la
base, ne la migre pas et ne modifie aucune table. Une base absente ou trop ancienne
produit un état contrôlé `données insuffisantes`.

La sortie JSON expose toujours :

- `facts` : version sélectionnée, contraintes de quantité, statistiques descriptives,
  couverture des moteurs et contexte exact;
- `evidence` : type, date, source et identifiant local/public minimal;
- `unknowns` : lacunes codées sans transformer une absence en certitude;
- `next_evidence` : courte liste des prochaines preuves réellement utiles;
- `warnings`, `read_only:true` et `network_used:false`.

Le rendu humain reprend les mêmes compteurs et verdicts. Il est volontairement court.

## Composition des moteurs existants

Le module `analysis.py` ouvre SQLite avec `connect_readonly`. Il réutilise :

- `cards_coverage` et `resolve_deck_cards` pour la couverture et la résolution stricte
  code TCG Online + numéro + nom;
- `rules_status` et `rules.check_deck` pour le registre officiel et le garde-fou
  `DECK_STRUCTURE_NOT_VERIFIED`;
- les tables normalisées et filtres de contexte Limitless pour compter tournois,
  placements, archétypes publiés et matchs réellement classifiables;
- les liens `battle_deck_versions`, seuls capables de prouver qu'un combat appartient
  à une version précise.

Aucune nouvelle table, migration, architecture distante, synchronisation ou LLM n'a
été ajouté.

## Sémantique des preuves

La dernière version enregistrée est toujours sélectionnée. Si elle est incomplète,
non confirmée ou postérieure au contexte demandé, le rapport le dit; il ne revient pas
à une version antérieure plus favorable. Une version postérieure expose
`historical_applicability=not_applicable`, garde ses faits descriptifs, mais force le
verdict réglementaire global à `unknown` avec `LATEST_VERSION_OUTSIDE_AS_OF`. Un
combat antérieur ne compte pas comme preuve de la version future, même si une liaison
locale incohérente existe. Une version exacte indique seulement ce qui a été importé,
pas la collection complète, le support Live ou la légalité.

Les combats valides sont dédupliqués par leur identité locale, bornés à `as_of` et
ventilés en W/L/nul/ambigu. Le rapport affiche `n`, la période, le nombre dont le deck
est enregistré, le nombre relié à une version quelconque et le nombre relié à la
version sélectionnée. Chaque observation reçoit une référence opaque comme
`local-observation-001`; aucune empreinte, ligne brute, carte observée ou identité de
joueur n'est affichée. Un lien au deck n'est pas un lien à sa version.

La résolution TCGdex donne des fractions avec dénominateurs par ligne et par quantité.
`unresolved` et `ambiguous` restent explicites. Une absence de correspondance ne veut
jamais dire « carte absente de TCG Live ».

Le verdict des règles conserve `unknown` tant que structure, quotas, Énergies de base,
Pokémon de base, exceptions datées ou réimpressions ne sont pas tous prouvés. Le
rapport conserve format, plateforme, date, codes de raison, couverture du registre et
références publiques disponibles.

Limitless est filtré sur PTCG, format, plateforme, online/présentiel, visibilité,
snapshot complet, date d'événement et date de capture locale. Les dénominateurs,
placements, matchs et sources ne portent que sur les snapshots admissibles. Un
archétype publié n'est jamais assimilé au deck local. Sans mapping fiable — et
notamment avec zéro archétype publié — aucun matchup chiffré n'est produit.

Les défaillances techniques du catalogue ou du moteur de règles produisent seulement
`CATALOG_UNAVAILABLE` ou `RULES_UNAVAILABLE` avec un message fixe. Le texte brut de
l'exception n'est jamais copié dans la sortie JSON ou humaine : chemin local, pseudo,
token et donnée de deck y demeurent caviardés.

## Exemple synthétique abrégé

```json
{
  "read_only": true,
  "network_used": false,
  "assessment": "données insuffisantes",
  "facts": {
    "deck": {"version": 2, "exact_confirmed": false},
    "battles": {"valid_unique": 5, "with_selected_version_proven": 1},
    "catalog": {"entry_resolution": {"resolved": 1, "ambiguous": 1, "unresolved": 2, "denominator": 4}},
    "rules": {"status": "unknown"},
    "metagame": {"n_tournaments": 1, "n_published_archetypes": 0, "n_exploitable_matches": 0}
  }
}
```

Cet exemple est fictif et ne contient aucune donnée du joueur.

## Limites avant une recommandation personnalisée

PM-0006A ne propose pas de carte, de deck, d'achat, de fabrication ou d'export. Avant
une future recommandation, il faut au minimum résoudre les impressions, obtenir une
validation structurelle et réglementaire datée, relier explicitement suffisamment de
combats à la bonne version, disposer de données compétitives classifiables et recevoir
volontairement l'inventaire/coût lorsque la question l'exige. Un échantillon d'environ
cinq parties demeure exploratoire et ne justifie ni « 80 % de chances de gagner » ni
un avantage de matchup.

## Couverture des tests synthétiques

Les tests couvrent base et deck absents, dernière version non confirmée, version
passée ou future, 60/60, quantités incohérentes, impression interdite, impressions
ambiguës/non résolues, verdict structurel `unknown`, zéro et cinq combats,
W/L/nul/ambigu, doublon, lien vers une autre version, événement futur, snapshot ancien
capturé plus tard, date `as_of` invalide, Standard/Expanded, Live/présentiel, sortie
humaine/JSON, exceptions artificielles contenant chemin/token/carte, absence de
chemin/empreinte/liste privée et identité byte-pour-byte de la base avant et après la
commande.
