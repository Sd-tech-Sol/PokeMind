# Audit TCGdex — PM-0004B

Contrôle documentaire et essais bornés effectués le **2026-10-11**. Les réponses
externes ont été validées comme données non fiables; aucune donnée de deck, combat,
crédit, profil ou identifiant utilisateur n'a été envoyée.

## Documentation et droits contrôlés

- <https://tcgdex.dev/rest> confirme REST v2, HTTPS, GET et réponses JSON.
- <https://tcgdex.dev/rest/filtering-sorting-pagination> documente
  `pagination:page`, 100 éléments par défaut lorsqu'elle est activée, ainsi que
  `sort:field` et `sort:order`.
- <https://tcgdex.dev/rest/card> confirme le détail public d'une carte par ID.
- <https://github.com/tcgdex/cards-database> décrit la base multilingue et renvoie
  à l'API publique.
- <https://github.com/tcgdex/cards-database/blob/master/LICENSE> déclare la base
  sous licence MIT. Les marques, textes et images Pokémon gardent leurs droits
  distincts; PokeMind ne télécharge aucune image et ne publie aucun dump.

Aucun quota chiffré ou endpoint différentiel/ETag confirmé n'a été trouvé. PM-0004B
n'en suppose donc aucun : scan paginé, intervalle minimal, timeout, budget strict
incluant les retries, `Retry-After`, cache privé et reprise durable seulement.

## Machine à états livrée

- La découverte initiale reste dans `catalog_sync_state`; le refresh manuel utilise
  `catalog_refresh_state` avec un curseur et des dates séparés.
- `--phase index|details|balanced` permet de consacrer le budget à la découverte,
  aux détails ou aux deux. `--refresh-index` n'est jamais déclenché en arrière-plan.
- Le refresh trie par ID, sonde une fois la première page après interruption, puis
  reprend son curseur. Une page abrégée devient un candidat de fin; seule la page
  vide suivante termine le scope.
- Les upserts sont transactionnels par page/détail. Aucun objet n'est supprimé parce
  qu'il manque dans une page. Un bref modifié conserve l'ancien détail et le marque
  possiblement périmé jusqu'à revalidation.
- `--recheck-absent` recontrôle explicitement les 404 antérieurs. Sans cette option,
  `absent`, `not_fetched` et `network_error` restent distincts.
- `--prioritize-deck` ne fait qu'ordonner localement les IDs TCGdex déjà résolus par
  code de set, numéro et nom exacts; la requête HTTP ne contient jamais le deck.

## Essais réels bornés

Deux essais seulement, **12 tentatives maximum chacun**, sur
`https://api.tcgdex.net/v2/{en|fr}` :

1. `--phase index --refresh-index --max-requests 12` : 12/12, aucune erreur/429;
   scan pages 1 et 2 avec sonde de tête; cache passé à 223 sets et 502 impressions.
2. `--phase balanced --refresh-index --max-requests 12` : 12/12, aucune erreur/429;
   pages 3, puis huit détails; état final 223 sets, 602 impressions, 973 traductions,
   4 détails EN et 4 FR.

État final honnête : découverte initiale incomplète, refresh en cours, 598 impressions
sans détails bilingues complets, aucune erreur réseau de traduction. Le refresh a
observé des ajouts et changements de brefs, mais les compteurs d'un premier cycle
incluent l'établissement des nouvelles empreintes et ne constituent pas un changelog
normatif du fournisseur.

## Limites

Le tri stable et la sonde de tête réduisent les omissions lors d'un décalage de pages,
mais une API paginée qui change pendant le parcours ne fournit pas un instantané
atomique. `refresh.finished` n'est vrai qu'après la confirmation de fin des quatre
scopes EN/FR. Une couverture locale complète ne signifie ni catalogue mondial
exhaustif, ni disponibilité TCG Live, légalité, possession, coût ou qualité méta.

Le cache, la base, sa sauvegarde v4, les journaux, decks et profils restent sous
`data/local/`, ignorés par Git. Aucun planificateur, serveur, PM-0005 ou automatisme
quotidien n'a été installé.
