# Connaissances publiques — preuves et limites du LOT G

Date : 2026-10-14. Données publiques seulement; aucune base personnelle utilisée.
La suite QA est entièrement synthétique. La courte observation publique ci-dessous
est distincte de la QA et n’est pas une mesure de couverture de la base du joueur.

## Changements techniques, tests hors ligne

- `cards_coverage` refuse `complete` si un détail FR/EN est périmé. Les GET restant
  sur les détails déjà présents mais périmés sont comptés séparément et exactement.
- Le total fournisseur demeure `unknown_without_snapshot_membership` : les lignes
  de traductions peuvent venir de détails d’une autre langue ou d’une extension,
  elles ne prouvent pas la composition d’un index fournisseur terminé.
- Un cycle profond reprend la découverte initiale jusqu’aux quatre scopes terminés;
  ensuite il rafraîchit. Le cycle quotidien garde le rafraîchissement des changements.
- `normative_coverage` mesure les rotations par plateforme/date/source; il refuse
  source non vérifiée, consultation future et exemples pris pour registres complets.
  Restrictions, structure/exceptions, reprints, promos, errata, Expanded et Live
  conservent des dimensions distinctes et les lacunes explicites.
- `official_validation_queue`, exposée par `knowledge status/audit`, conserve les
  dernières observations publiques et leurs prochaines validations. Hash de préfixe
  tronqué, HTTP 200/304 et changement ne certifient aucune assertion normative.

Preuve locale : `test_lot_g_knowledge.py`, suites cartes/règles/updates/knowledge,
**90 passed** sur Windows. Provenance : exécution Codex, pas audit indépendant.

## Sources primaires relues

[Pagination et tri TCGdex](https://tcgdex.dev/rest/filtering-sorting-pagination) :
paramètres de pagination explicites et tri paramétrable.
[Licence de la base TCGdex](https://github.com/tcgdex/cards-database/blob/master/LICENSE) :
MIT, avec droits des marques/illustrations distincts; aucun dump ni image versionné.
[Documentation développeur Limitless](https://docs.limitlesstcg.com/developer) :
endpoints publics sans clé sauf catégorisation `/games/.../decks`, quotas par en-têtes.
Ces consultations ne donnent aucune permission d’aspiration massive ni d’API privée.

## Observation publique bornée, sans conservation

TCGdex, budget **4 GET**, intervalle 0,5 s et timeout 10 s :
`/v2/en/cards` et `/v2/fr/cards`, page 1 de 3 éléments; puis détail public
`/v2/en/cards/base1-1` et `/v2/fr/cards/base1-1`. Les quatre réponses sont validées
par les parseurs existants. Une SQLite jetable a reçu 4 impressions distinctes et
2 traductions détaillées; `integrity_check=ok`. Aucun nom/texte de carte versionné.
Les 4 GET ont été consommés; total fournisseur **unknown**, aucune légalité inférée.

Limitless, budget **2 GET**, intervalle 0,5 s et timeout 10 s : `/api/games`, puis
`/api/tournaments?game=PTCG&format=STANDARD&limit=3&page=1`. Options PTCGL/Standard
présentes et 3 briefs validés; quota restant annoncé 48. Aucun standings/pairing,
participant, pseudo, decklist, clé ou snapshot de tournoi importé. Les 2 GET ont été
consommés. Ces briefs ne fournissent ni matchup ni taux de victoire.

Le répertoire de campagne sous `data/local/test-runs/` a été supprimé par le contexte
temporaire après fermeture des connexions. Rien de cette campagne n’a été importé
dans la SQLite personnelle. Sources officielles non rafraîchies; Trainer Hill
`BLOCKED_WITH_REASON` faute d’accès automatisé autorisé établi.

## Rattrapage conservé pour LOT H

Finir les scopes historiques FR/EN et les détails via fenêtres bornées et reprise;
établir les membres/denominators d’un snapshot distinct de l’union locale. Faire
valider les contenus officiels complets, dates, restrictions/exceptions, réimpressions,
promos, errata et support Live. Augmenter l’échantillon public Limitless contextualisé
sans prétendre couvrir la totalité du métagame. L’accès Trainer Hill requiert une
source primaire et une permission vérifiables; aucun scraping compensatoire.
