# Counter-Deck Lab PUBLIC et Learning Loop fictive

Mandat `PM-V1-COUNTER-DECK-LEARNING-LOOP-001`, 23 octobre 2026.
Implémentation livrée pour audit indépendant, **V1 NOT_RELEASE_READY**.
Les listes PUBLIC proviennent du cache existant. Les parties et les deux
versions utilisées dans la simulation sont **entièrement inventées**. Aucun
vrai journal, deck joué, collection, crédit, client ou compte n'est consulté.

## Choisir quoi tester contre un archétype

PowerShell, à la racine du dépôt, deux caches PUBLIC explicitement désignés :

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
$referenceDb = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind meta counter-plan --db $publicDb --reference-db $referenceDb --target Hydrapple --as-of 2026-10-23 --options 4 --set-aliases
python -m pokemind meta counter-plan --db $publicDb --reference-db $referenceDb --target 'Basic Box' --as-of 2026-10-23 --options 4 --set-aliases --json
```

`--base événement:placement` peut sélectionner une liste Dragapult PUBLIC
précise. Sans sélection, le médoïde de ses compositions distinctes est choisi
par le comparateur existant : proximité de construction, jamais force de jeu.
`--options 1` à `4` limite les listes renvoyées, en incluant la base conservée.
Si disponibles, les trois autres options représentent Basic Box, Hydrapple et
Dhelmise; d'autres familles sourcées complètent seulement les familles absentes.

Chaque option contient son **export publié exact60/60**, ses URLs, dates,
placements/échantillon, empreinte de composition, sa fiche sourcée, et la
différence complète des impressions/copies ajoutées ou retirées. Les différences
de sections Pokémon/Dresseurs/Énergies sont calculées depuis les listes; les
stades viennent des textes identifiés. Consistance, couleurs utilisables,
échange de Récompenses et courbe ne sont pas inférés de simples totaux.

Les rôles de pioche, recherche, accélération, perturbation, soins, changement
d'Actif et attaques proviennent de la fiche `deck_knowledge` : payload TCGdex
identifié, daté, hash contrôlé et provenance présente. Ces rôles sont des indices
textuels conditionnels. Les questions visant le proxy adverse citent séparément
nos cartes et ses cartes : par exemple, comparer une perturbation à son moteur
de pioche/recherche, ou nos soins aux attaques citées. Coûts, restrictions,
cibles et fenêtre réelle doivent toujours être vérifiés. Un texte TCGdex
descriptif ne certifie ni errata effectif ni effet légal sur un plateau précis.

L'ordre favorise les interactions à tester soutenues par des textes, la
couverture descriptive puis le coût de changement en copies. Il n'est ni un
classement de force ni une prédiction de victoire. Les attaques imprimées sont
consultables; aucune ligne de K.O. n'est affirmée sans PV, protections, règles,
Énergies et plateau attestés. Le proxy PUBLIC n'est **jamais** l'adversaire exact.

Les trois décisions demeurent visibles : garder la liste et tester une séquence,
tester une autre liste publiée, ou recueillir davantage de parties avant de
conclure. Une adaptation non validée reste `hypothesis_to_test`, **sans export**.
Possession, crédits, craftability, disponibilité Live et avantage de matchup
restent inconnus. Le prévol présentiel est transmis avec ses preuves/blocages;
un export syntaxiquement valide n'autorise aucune déclaration de légalité.
Les sept identités MEE non prouvées demeurent inconnues; pas d'heuristique
d'équivalence de nom d'Énergie. Aucun renouvellement réseau ou repli personnel.
Cache absent/invalide ou base non PUBLIC : `BLOCKED_WITH_REASON`, code neutre,
retour2, aucune collecte de remplacement.

## Démontrer le cycle sans ouvrir une partie réelle

```powershell
python -m pokemind meta learning-simulate --db $publicDb --reference-db $referenceDb --target Hydrapple --as-of 2026-10-23 --set-aliases
python -m pokemind meta learning-simulate --db $publicDb --reference-db $referenceDb --target Hydrapple --as-of 2026-10-23 --set-aliases --json
```

Cette commande n'accepte **aucun chemin de journal ni de base de combats**.
Elle valide les deux caches PUBLIC, crée un répertoire temporaire neuf
`data/local/synthetic-learning-*`, y utilise le schéma/importeur/parseur et
les attestations existants avec des données générées, puis retire uniquement
ce répertoire neuf. Les dates d'attestation artificielles ne sont pas des
déclarations du propriétaire. Les deux versions de deck sont celles de la démo
synthétique existante; les victoires fictives ne mesurent donc pas les alternatives
PUBLIC présentées dans le plan.

Cycle démontré :

1. Deux défaites et une issue inconnue fictives FR/EN sous v1; observation
   partielle et hypothèse adverse, suggestion PUBLIC et protocole de test.
2. Une victoire et une défaite sous v2, puis une défaite sans version attestée
   ni classification certaine; les groupes demeurent séparés.
3. Réimport exact idempotent et variante interparseur reconnue comme doublon
   probable. Six parties retenues sur sept enregistrements, sans supprimer ni
   transférer les faits ou attestations. Petits ratios masqués.
4. Comparaison des deux évaluations ordonnées au même jour : W/L/unknown,
   `n=W+L`, versions, dates attestées, parseurs et références de parties conservés.
   Les deltas décrivent aussi retraits/reclassifications possibles. Ni progrès
   causal ni supériorité de v2 démontrés.
5. Revue inconclusive, retrait d'une conclusion prématurée, réouverture avec
   question plus précise et rejet d'une affirmation causale non prouvée.

Si aucune carte discriminante de la cible n'est présente dans le cache,
l'observation fictive et l'archétype demeurent inconnus; aucun indice inventé.
La simulation emprunte `opponent_observer`, `matchup_analytics`,
`battle_sample.conservative_sample` et `lessons.battle_lessons`; elle ne crée
aucun second moteur de statistiques.

## Journal de connaissances et corrections

`learning_loop` travaille sur une valeur JSON locale fournie par l'appelant.
Il n'ouvre aucun fichier et n'écrit dans aucune base existante. Le résultat JSON
du CLI contient le journal complet, pouvant être conservé volontairement dans
un fichier local ignoré. Aucun stockage automatique ou service résident.

| Type de fiche | Preuve et sens |
|---|---|
| `source_fact` | Observation d'une source citée; pas de promotion en règle normative |
| `observed_game_event` | Événement avec provenance et référence de partie/parseur |
| `derived_statistic` | Vue calculée par le moteur existant, échantillon et versions explicites |
| `hypothesis_to_test` | Question conditionnelle; jamais fait automatiquement confirmé |
| `test_plan` | Protocole, version, cible hypothétique et preuves manquantes |
| `outcome_review` | Évaluation datée, raison et références aux fiches précédentes |
| `withdrawn` / `rejected` | Révision explicite; les preuves d'origine restent présentes |

Chaque entrée possède ID, date stricte, type, références, parent de révision et
chaîne de digests déterministes. Ces digests détectent une modification d'une
valeur, **ne sont pas une signature ou une attestation externe**. Rejouer un ID
identique est idempotent; un contenu différent sous le même ID est refusé.
Les faits/événements/statistiques sont immuables; nouvelles observations et
calculs deviennent d'autres entrées. Révisions sur le dernier parent seulement,
raison obligatoire, références antérieures et ordre des dates contrôlés.
`view(..., as_of=...)` retrouve l'état connu à une date et garde tout l'historique.
Un retrait peut être révisé par une nouvelle hypothèse, sans effacer son motif.
Une nouvelle fiche n'entraîne ni modèle ni modification de poids.

## Contrat d'import réel futur — conception seulement

`future_import_contract()` expose ce contrat sans exécuter d'import :

- Chaque journal doit être fourni **un par un**, par chemin précis ou ID déjà
  local, avec base sélectionnée, deck/numéro de version attesté ou `unknown`,
  date jouée connue/inconnue, joueur de référence et but/consentement.
- Utiliser le CLI existant `log import <fichier> --deck <id> --db <base>`
  seulement après un ordre explicite pour ce fichier. Confirmer séparément la
  paire via `deck link-battle`, avec date et confirmation propriétaire; aucun
  rattachement à la version courante par défaut.
- Lecture, import, attestation et correction sont des actes distincts.
  Une correction datée/révocable s'ajoute aux preuves; aucun scan de dossier,
  suppression des originaux, modification de collection ou transmission Git/API.
- Un proxy PUBLIC de60 reste un modèle de référence; un résultat inconnu ne
  devient pas victoire/défaite et une carte vue ne prouve pas sa possession.

Ce lot n'autorise **aucun import réel**. DKI-05/06 sur parties personnelles,
les règles/Live, le visuel, le scheduler et les autres portes V1 restent ouverts.
Audit ChatGPT indépendant requis après publication et CI au SHA exact.
