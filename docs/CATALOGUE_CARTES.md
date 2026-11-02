# Catalogue progressif des cartes — PM-0004/PM-0004B et LOT A

Complément2026-10-22 : [enrichissement français publié](ENRICHISSEMENT_TEXTES_FR.md),
15 439 champs sourcés /10 556 cartes, aucune traduction générée par l'agent,
aucune carte d'extension japonaise importée; 798 lacunes de champs restent explicites.

Mise à jour2026-10-22 : **catalogue PUBLIC descriptif complet pour un instantané officiel épinglé** :23 864impressions/223extensions,23 771détailsEN/22 192FR. Absences par langue préservées, V1 NOT_RELEASE_READY, AWAITING_AUDIT. Voir le [guide du snapshot](CATALOGUE_TCGDEX_SNAPSHOT.md) pour la base explicite et les limites; les mécanismes progressifs historiques ci-dessous restent distincts.

## Objectif
Créer un lexique local **visant la totalité des impressions/cartes connues de TCGdex**, avec un indicateur de couverture et sans fausse promesse d'exhaustivité absolue. Identifier séparément (a) le catalogue historique, (b) les cartes présentes ou compatibles dans Pokémon TCG Live selon les sources disponibles, (c) la légalité par format et par date, y compris réimpressions/errata. Les listes autorisées ne peuvent pas être déduites d'une simple marque de régulation ni de la seule date d'impression.

## Source principale réutilisable
- https://github.com/tcgdex/cards-database : base multilingue (MIT pour le dépôt, sous réserve des droits distincts sur marques/images et des conditions de réutilisation).
- https://tcgdex.dev/fr : API REST avec séries, extensions, cartes, filtres/pagination, données françaises et anglaises; traductions parfois incomplètes.
- https://www.pokemon.com/us/play-pokemon/about/card-dex/ et https://play.pokemon.com/en-ca/resources/documents/ : règles officielles, errata, formats, bannissements. Pour les cartes jouables dans Live, marquer non vérifié sans confirmation actuelle.
- Ne PAS bâtir sur l'ancienne PokemonTCG API, fermeture annoncée pour mars 2027.

## Modèle livré

- `catalog_sets` : ID TCGdex, noms FR/EN, série, date, compteurs, code
  `tcgOnline` seulement lorsqu'il est fourni par le détail du set, provenance et états.
- `catalog_printings` : une ligne par ID TCGdex d'impression, set, numéro local,
  catégorie normalisée, PV, stade, rareté, marque de régulation, types et variantes.
- `catalog_translations` : une ligne reliée par impression et langue, noms, texte,
  attaques, talents, types Dresseur/Énergie, provenance URL/date/SHA-256 et état.
- `catalog_sync_state` : découverte initiale, page suivante, confirmation de fin,
  compte d'appels, derniers succès et échecs.
- `catalog_refresh_state` : cycle manuel distinct, curseur reprenable, sonde de tête,
  ajouts/modifications vus et dates de début/fin. Les index FTS5 du catalogue sont
  séparés de l'index des quatre volumes.

Les états de traduction sont `present`, `absent`, `not_fetched` et
`network_error`. `NULL` signifie que le champ n'était pas fourni, jamais une valeur
inventée. Une extension inconnue découverte dans un détail devient un stub sourcé.
Le schéma ne crée aucun `functional_card_id` : l'équivalence de réimpressions est
reportée jusqu'à une preuve officielle.

## Synchronisation livrée

1. `--dry-run` : zéro écriture et zéro réseau.
2. Une vraie exécution migre au schéma 5 après `sqlite3.backup()` cohérent, puis
   consulte seulement `https://api.tcgdex.net/v2/{en|fr}/...`.
3. `--phase index|details|balanced` choisit la progression. Les index utilisent des
   pages de 100; une page abrégée doit être confirmée par la page vide suivante.
4. Le budget compte les retries; réponse maximale 8 Mio, timeout 15 s, intervalle
   minimal, trois essais au plus, backoff et `Retry-After` plafonné à 30 s.
5. Chaque page/détail est validé avant transaction. Un échec ne remplace pas le
   dernier contenu valide. La prochaine exécution reprend les checkpoints.
6. Les images ne sont ni demandées séparément ni téléchargées. Le cache et les
   sauvegardes restent dans `data/local/`, hors Git.
7. `--refresh-index` démarre ou reprend manuellement un cycle séparé, avec tri par ID
   et une sonde de la page 1 après interruption. Aucun scan paginé ne constitue un
   instantané atomique si la source change pendant son parcours; aucune absence sur
   une page ne supprime une entité locale.
8. Un bref modifié conserve le dernier détail sain et le marque possiblement périmé.
   Un ancien `absent` reste protégé même si le bref change ou devient périmé; il
   n'est recontrôlé qu'avec `--recheck-absent`.

## Commandes livrées
- `python -m pokemind cards sync --dry-run --json`
- `python -m pokemind cards sync --phase balanced --lang en,fr --max-requests 12 --json`
- `python -m pokemind cards sync --phase index --refresh-index --max-requests 12 --json`
- `python -m pokemind cards sync --phase details --recheck-absent --max-requests 4 --json`
- `python -m pokemind cards sync --phase details --prioritize-deck principal --max-requests 4 --json`
- `python -m pokemind cards search "Dragapult" --lang all --json`
- `python -m pokemind cards show 2011bw-1 --lang fr --json`
- `python -m pokemind cards reprints 2011bw-1 --as-of 2026-10-13 --json`
- `python -m pokemind cards coverage --json`
- `python -m pokemind cards resolve-deck principal --json`

La légalité datée est maintenant séparée dans `rules check-card` et `rules
check-deck` (PM-0005A). Elle ne dérive jamais du seul champ `legal`, du set ou du nom
TCGdex; une identité non résolue ou une couverture normative incomplète reste
`unknown`. Voir `docs/REGLES_LEGALITE.md`.

## Renforcement LOT A

- Les noms sont rapprochés en Unicode NFC + `casefold`; une collision de nom ne
  fusionne jamais deux impressions. Les alias FR/EN restent reliés à l'ID TCGdex et
  à leur URL/date de détail.
- `cards show` expose l'identité stable, set/numéro/date, variantes, langues et champs
  manquants. L'identité fonctionnelle reste `unknown` sans assertion officielle.
- `cards reprints` ne lit que les assertions `reprint_equivalence` dont l'assertion
  et la source sont vérifiées et actives à la date demandée.
- La priorité des détails utilise uniquement les IDs publics résolus du deck local,
  puis les marques Standard couvertes par une assertion officielle, puis le reste.
  Aucune ligne de deck, collection ou journal n'est transmise.
- La couverture fournit pour chaque langue l'état du scan d'index, le nombre
  découvert, le total visible uniquement après scan terminé, et le ratio de détails
  sur les impressions découvertes. Sans total fournisseur publié ou scan terminé,
  la quantité restante de pages demeure `unknown`.

## Acceptation
Les fixtures synthétiques couvrent mêmes IDs FR/EN, traduction absente, noms
identiques d'impressions distinctes, ancienne série, Pokémon/attaque/talent,
Dresseur, Énergie, champs optionnels, set inconnu, réponse vide/malformée, timeout,
429, pagination, insertion décalant les pages, nouveau nom FR, bref modifié, ancien
détail préservé, refresh partiel/repris/idempotent, petit budget, confidentialité de
la priorité locale et migration/restauration. L'essai réel est volontairement petit
et ses comptes figurent dans `.orchestrator/RESULT.md`.
