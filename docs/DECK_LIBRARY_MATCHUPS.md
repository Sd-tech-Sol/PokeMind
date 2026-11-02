# Bibliothèque PUBLIC, Observer et Matchup Analytics — fondation

Suite fonctionnelle : [Counter-Deck Lab PUBLIC et Learning Loop sur parties inventées](COUNTER_DECK_LEARNING_LOOP.md). Aucun import personnel ou nouveau GET autorisé; résultats pour audit indépendant.

Cette tranche relie la bibliothèque de listes publiques aux premiers moteurs
d'observation et de statistiques. La bibliothèque est consultable sur le cache
PUBLIC. **Observer et Analytics ont été développés et exécutés uniquement sur
des matchs inventés**; aucune partie, version personnelle ou collection réelle
n'a été ouverte. La validation réelle future demeure sur commande volontaire.

## Bibliothèque : chercher, consulter, comparer, exporter

Depuis la racine du dépôt :

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
$referenceDb = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind meta deck-library --db $publicDb --as-of 2026-10-23
python -m pokemind meta deck-library --db $publicDb --as-of 2026-10-23 --archetype Hydrapple --event 581 --since 2026-10-01 --until 2026-10-20 --json
python -m pokemind meta deck-knowledge --db $publicDb --reference-db $referenceDb --selector 581:7 --as-of 2026-10-23 --set-aliases
python -m pokemind meta competitive-compare --db $publicDb --left 581:1 --right 581:7 --as-of 2026-10-23 --json
python -m pokemind meta competitive-export --db $publicDb --event 581 --placement 7
```

`--version` accepte l'empreinte complète d'une composition affichée par la
bibliothèque. La version d'une composition PUBLIC est distincte de la version
attestée du deck personnel utilisé dans un match. Les dates de filtre de la
bibliothèque sont celles des tournois. Les dénominateurs de compositions et de
placements restent séparés, y compris après filtrage.

Le cache existant contient, selon la vérification locale Codex, **28 compositions
pour32 placements dans deux événements,15 étiquettes d'archétype**. Ce sont des
placements publiés sélectionnés, avec un biais top16; aucun « meilleur deck »
absolu, avantage de matchup ou winrate n'est déduit de ces places.

Les fiches reprennent les textes natifs vérifiés, rôles sourcés, évolutions,
coûts d'attaque, ressources, séquences conditionnelles et plans de K.O./Récompenses
de [Deck Knowledge](DECK_INTELLIGENCE.md). Elles proposent aussi jusqu'à trois
autres familles PUBLIC avec une différence quantitative de composition. Ces
alternatives sont des références à tester, pas des contres démontrés.

Le sérialiseur PTCGL existant reste celui historiquement `FIELD_VALIDATED`.
La liste source et la composition sont recontrôlées; chaque export doit faire
60/60. Copie **manuelle** du texte : aucune action presse-papiers ou jeu.
Les rapports détaillés, fiches et exports réels restent dans le nouvel espace
PUBLIC local ignoré `data/local/public-campaigns/lot-i-deck-library-matchup-20261023/`.
Les listes complètes et textes du corpus ne sont pas redistribués dans Git.

## Énergies MEE : preuve manquante conservée

L'examen local des sept impressions MEE pilotes confirme une catégorie Énergie,
un numéro et un ID de catalogue, mais pas une équivalence explicite des noms
avec/sans « Basic ». Le cache ne contient pas de page carte MEE de l'autre
fournisseur ni de texte d'effet corroborant cette équivalence. Les noms sources
restent intacts; aucune règle générale de suppression de « Basic » n'est ajoutée.
Les quatre pilotes conservent **87/97 lignes par option résolues,62/69 impressions
uniques,201/240 copies**; les quatre decks sont `unknown` en présentiel et Live.

Hiérarchie : Pokémon officiel pour les normes, TCGdex pour la description,
Limitless pour listes et résultats datés; suppléments communautaires FR séparés.
Identité, légalité, disponibilité Live et possession demeurent distinctes.

## Observer : faits partiels, hypothèses, références

Le moteur réutilise `battle_logs.parse_battle_log` et les événements normalisés
existants. Il garde la chronologie et les preuves du parseur séparées des
inférences. Une phrase reconnue par un ancien parseur reste un texte rapporté;
elle n'est pas automatiquement une carte adverse visible.

- `observed_partial` : cartes adverses effectivement jouées, attachées ou révélées,
  ou Pokémon nommé explicitement dans une action reconnue. Une pioche cachée,
  main générique, phrase de règle ou nom d'attaque ne devient pas une carte vue.
  Plusieurs mentions prouvent au moins un exemplaire; elles ne prouvent pas
  plusieurs copies. Les identités partielles ne sont pas additionnables.
- `archetype_hypothesis` : indices discriminants dans l'échantillon PUBLIC,
  alternatives et confiance prudente. Les cartes communes à toutes les familles
  disponibles ne départagent pas les archétypes. Pas de probabilité calibrée;
  ex aequo ou manque d'indices donnent `ambiguous` ou `unknown`. Les noms FR/EN
  supplémentaires exigent une traduction native présente, datée, non périmée,
  avec payload et provenance vérifiés pour la même impression.
- `public_reference_proxy` : une liste source60 de famille analogue, avec
  sélecteur, version et sources. **Ce n'est jamais le deck exact de l'adversaire.**
- `exact_confirmed_60` : seulement si un export adverse complet est explicitement
  fourni, valide à60 et cohérent avec les cartes observées et les participants.
  Cela ne certifie ni sa légalité ni son extraction indépendante depuis le jeu.
  Cette voie est exercée sur fixtures par l'API, sans lecture de fichier réel.

Les annotations de classification fournies explicitement à l'API sont datées,
versionnées et révocables : `classification_history` garde les révisions et la
première hypothèse du modèle. Un label observé par le propriétaire est distinct
d'une hypothèse et d'un export exact. Cette API ne sauvegarde pas d'annotation
dans une base existante et n'en fabrique pas automatiquement.

## Analytics : compter par version réellement attestée

Les groupes séparent **deck-version × label adverse × origine du label**.
Chaque groupe affiche `wins/losses/unknown`, `games` et `n` : `n` compte seulement
les issues W/L corroborées. Un gagnant incompatible avec les participants ou
un compteur d'événements incohérent produit des inconnus.

Le moteur réutilise `conservative_sample`, l'historique d'attestation de
`version_evidence`, la validation existante des versions exactes60 et
`battle_lessons`. Aucun lien n'est créé ou déplacé. Version courante, lien
legacy non attesté, confirmation future, révocation ou conflit ne permettent
pas d'attribuer une version. Un représentant de doublon n'hérite jamais de
l'attestation d'un autre enregistrement. Les fichiers et enregistrements restent
intacts; l'exclusion de doublons probables est une convention provisoire affichée.

Le ratio descriptif reste inconnu pour `n<5`, une version inconnue ou des
doublons probables. Quand il est affiché, ce n'est ni un taux prédictif ni une
preuve d'amélioration. Une comparaison v1/v2 montre seulement les comptes par
version; causes de défaite, efficacité d'une carte et bénéfice d'un changement
restent inconnus. Aucun combat ne partage son dénominateur avec les placements
de tournoi PUBLIC.

`--since/--until` filtre les matchs sur la **date de partie attestée**, pas la
date d'import. Une partie sans date connue est dénombrée comme exclue du filtre.
`--as-of` limite les preuves disponibles, confirmations et imports à cette date.
Les leçons du joueur sont une vue séparée à cette date; elles n'augmentent pas
les dénominateurs des matchups et ne servent pas à inventer une causalité.

## Scénario vérifiable entièrement inventé

```powershell
python -m pytest -q -s tests/test_deck_library_matchups.py::test_end_to_end_library_observer_and_matchups
```

Le test crée puis retire uniquement ses fichiers synthétiques isolés. Il ne
consulte pas les caches réels ou une partie personnelle.

| Groupe inventé | Victoires | Défaites | Issue inconnue | n W/L | Parties |
|---|---:|---:|---:|---:|---:|
| v1 / hypothèse Hydrapple | 0 | 2 | 1 | 2 | 3 |
| v2 / hypothèse Hydrapple | 1 | 0 | 0 | 1 | 1 |
| Version non attestée / adversaire ambigu | 0 | 1 | 0 | 1 | 1 |

Réponse démontrée : « v1 a deux défaites confirmées contre une **hypothèse**
d'archétype, n=2; une autre issue est inconnue. L'adversaire inventé a montré
Synthetic Delta, au moins un exemplaire malgré plusieurs mentions. Une liste60
PUBLIC synthétique sert de proxy; ses60 cartes ne sont pas celles de
l'adversaire. Aucune amélioration de v2 ni changement de carte n'est démontré. »

## Sélection volontaire future, sans activation dans cette tranche

Le propriétaire choisira lui-même le journal, le deck et la base autorisés
avant tout import réel. L'import existant est `log import <fichier choisi>
--deck <ID choisi> --db <base choisie>`; il écrit et exige donc cet ordre
ultérieur distinct. Une version jouée doit ensuite être attestée volontairement
par le mécanisme existant; un import seul ne l'atteste pas. Aucun de ces actes
réels n'a été lancé dans ce mandat.

Pour une future **lecture explicitement autorisée**, les nouvelles commandes
seront `battle opponent --battle-id <ID>` et `battle matchups --deck <ID>`, avec
`--db <base choisie> --as-of <date> --confirm-owner-read`, éventuellement
`--public-db <cache PUBLIC> --reference-db <catalogue PUBLIC>` pour les proxies.
Elles offrent humain/JSON. Sans base explicite ou opt-in, elles refusent avant
toute inspection de la base par défaut. Chemins hors du projet local,
redirections, alias de fichier et sidecars SQLite présents sont refusés; aucune
création, migration ou écriture implicite n'est effectuée.

L'[EPIC #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1) reste la feuille de
route. DKI-03/04 sont des **fondations testées sur fixtures**, sans validation
sur de vraies parties. DKI-05 Counter-Deck Lab et DKI-06 Learning Loop restent
ouverts, ainsi que les portes OCR, scheduler Windows et récupération A–J.
**0GET fournisseur; V1 NOT_RELEASE_READY. STOP audit indépendant ChatGPT.**
