# Liste PUBLIC sourcée, plan de jeu et copie manuelle

Mandat `PM-V1-PUBLIC-DECK-FIELD-QA-001`, 23 octobre 2026.
Les observations du cache Windows sont `CODEX_LOCAL_REPORTED`; les tests CI
utilisent exclusivement des listes et parties inventées. **V1 NOT_RELEASE_READY.**

## Parcours joueur reproductible

Depuis la racine PokeMind, sélectionner les deux caches PUBLIC autorisés :

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
$referenceDb = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind meta deck-library --db $publicDb --as-of 2026-10-23
python -m pokemind meta deck-knowledge --db $publicDb --reference-db $referenceDb --selector 581:1 --as-of 2026-10-23 --set-aliases
python -m pokemind meta deck-knowledge --db $publicDb --reference-db $referenceDb --selector 581:1 --as-of 2026-10-23 --set-aliases --json
python -m pokemind meta competitive-export --db $publicDb --event 581 --placement 1
```

Lire la source, les dates, les conditions et les inconnues de la fiche; copier
ensuite **manuellement** la liste complète affichée par `competitive-export`.
Chaque export est reparsé à 60 cartes; la syntaxe ne certifie ni légalité actuelle,
ni disponibilité dans Live, ni possession. Aucun accès au client ou au presse-papiers.
Si un cache manque, arrêter le parcours terrain : aucun téléchargement ou chemin
de remplacement implicite. Les exemples de ce document n'autorisent aucun acte privé.

| Exemple PUBLIC | Sélecteur | Usage |
|---|---|---|
| Dragapult | `581:1` | Étudier la chaîne d'évolution et les marqueurs sur le Banc |
| Basic Box | `582:13` | Lire chaque option d'attaque et ses conditions propres |
| Hydrapple | `581:7` | Examiner évolution, ressources et attaques sourcées |
| Dhelmise | `581:4` | Examiner le plan publié et les conditions des effets |

Pour comparer des options face à une **famille hypothétique**, sans prétendre
connaître le deck exact d'un adversaire :

```powershell
python -m pokemind meta counter-plan --db $publicDb --reference-db $referenceDb --as-of 2026-10-23 --target Hydrapple --set-aliases
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-23 --platform in_person --format standard --set-aliases --json
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-23 --platform live --format standard --set-aliases --json
```

L'ordre du Counter-Deck Lab dépend des preuves et du coût de changement en copies.
Ce n'est pas une mesure de force ou de victoire. Les statistiques de tournoi,
de matchs personnels, de BO1/BO3 et de Live demeurent des populations distinctes.

## Exemple de pilotage conditionnel : Dragapult `581:1`

Référence : [liste publiée et placement](https://www.limitlesstcg.com/tournaments/581),
événement du 10 octobre 2026. Les champs natifs ci-dessous proviennent du
[snapshot TCGdex épinglé](https://github.com/tcgdex/cards-database/tree/cbddf7e54033b1b58e44af1049c88832e55b94d0/data),
consulté le 22 octobre, à 16:16 UTC environ; la fiche JSON fournit les secondes,
les URLs d'objets et les identités exactes. Ce sont des descriptions de catalogue;
les règles et errata complets ne sont pas certifiés par ce parcours.

1. **Installation et ouverture — inférence.** Chercher les maillons manquants de
   Dreepy → Drakloak → Dragapult ex, puis préparer un attaquant de relève si le
   plateau et les ressources le permettent. Les champs `evolveFrom` de
   `sv06-129` et `sv06-130` soutiennent la chaîne. Buddy-Buddy Poffin
   (`sv05-144`, champ `effect`) recherche jusqu'à deux Pokémon de base de 70 PV
   ou moins vers le Banc : contrôler les cibles, les places et les restrictions
   avant de choisir. Aucun départ en main ni évolution au premier tour n'est supposé.
2. **Pioche et recherche — inférence.** Recon Directive de Drakloak permet de
   choisir une des deux cartes du dessus; l'autre va sous le deck. Comparer
   cette information avant une recherche précise. Run Away Draw de Dudunsparce
   (`sv05-129`, `abilities`) pioche trois cartes puis remélange ce Pokémon et
   ses cartes attachées si une carte a été piochée ainsi : prévoir la perte de
   cette présence sur le plateau. Flip the Script de Fezandipiti ex
   (`me02.5-142`, `abilities`) exige un K.O. subi au tour adverse précédent et
   reste limité à un usage de ce talent par tour; ce n'est pas une perturbation adverse.
3. **Évolution et Énergie — inférence.** Vérifier les délais d'évolution et les
   coûts avant d'engager ses ressources. Crispin (`sv07-133`, `effect`) cherche
   jusqu'à deux Énergies de base de types différents, en met une en main et
   attache l'autre; vérifier les ressources réellement accessibles. Rosa's
   Encouragement (`me03-084`, `effect`) exige davantage de Récompenses restantes
   que l'adversaire et attache depuis la défausse à un Pokémon de niveau 2.
   Ce critère de Récompenses ne constitue pas un effet de perturbation.
   Les identités d'Énergies `MEE` non résolues restent inconnues; aucune
   équivalence de nom ou légalité n'est déduite de ces conseils.
4. **Attaque et K.O. — faits de catalogue puis hypothèse.** `sv06-130`, champ
   `attacks`, décrit Jet Headbutt à 70 pour une Énergie Incolore et Phantom Dive
   à 200 pour Feu + Psy, avec six marqueurs à répartir sur le Banc adverse.
   Comparer le K.O. de l'Actif et la préparation de futurs seuils sur le Banc
   seulement à partir de PV et protections visibles. Dégâts et placement de
   marqueurs doivent rester distingués; leur applicabilité dépend des textes
   et règles de la situation. Aucun nombre de Récompenses gagné n'est inventé.
5. **Contre-jeu et fin de partie — hypothèse à tester.** Le texte Itchy Pollen
   de Budew (`me02.5-016`, `attacks`) décrit une restriction sur les Objets au
   prochain tour adverse. Comparer ce délai au progrès de son installation et
   aux ressources nécessaires à l'attaque suivante. Recalculer les seuils et
   le relais d'attaquant après chaque changement visible; les cartes cachées,
   la main adverse et un avantage de matchup demeurent inconnus.

Avant de changer la liste, noter en entraînement volontaire l'installation,
les ressources manquantes et les conditions réellement rencontrées. Une défaite
isolée ne démontre ni faute ni besoin de remplacer une carte. La consultation
d'un vrai journal et son import/attestation requièrent leurs consentements
distincts; voir [parcours de revue sélectionnée](OWNER_SELECTED_MATCH_REVIEW.md).

## Refaire la QA technique hors ligne

La lecture des marqueurs PUBLIC, du `requests.json` compétitif et de ses pages
référencées doit aussi être autorisée. Le propriétaire l'a explicitement permis
pour ce lot. Le script réutilise les cinq lecteurs existants, vérifie chaque
placement et composition, puis compare octets et métadonnées des seuls fichiers
nommés. Aucun parcours de répertoire, création de cache, migration ou GET.

```powershell
python -B scripts/qa_public_decks.py --db $publicDb --reference-db $referenceDb --as-of 2026-10-23
python -m pytest -q tests/test_public_deck_field_qa.py
```

La sortie JSON contient les sources/dates par placement, les dénominateurs par
composition, les prévols présentiel/Live et les plans conditionnels des quatre
familles disponibles. Les empreintes des fichiers restent en mémoire et ne sont
pas publiées. Source incohérente, sidecar SQLite présent ou mutation détectée :
arrêt avec code neutre; aucune réparation du cache ni reprise réseau.

La QA sur fixtures inventées couvre les mêmes lecteurs, l'absence de découverte,
la non-mutation, les erreurs de source, les rôles textuels et trois sorties CLI
dans un enfant démarrant avec `PYTHONIOENCODING=cp1252`. La CLI existante impose
UTF-8; les octets humains/JSON/export sont décodés strictement et l'export reparsé.
Ces tests ne certifient pas le PC ni une impression réelle. La comparaison de
fichiers avant/après ne garantit pas l'exclusion de tout processus concurrent.

Mesures terrain et résultats complets :
[preuves assainies du lot](../.orchestrator/EVIDENCE_PM-V1-PUBLIC-DECK-FIELD-QA-001.md).
