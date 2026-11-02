# Prévol des listes PUBLIC : preuves de légalité hors ligne

`meta competitive-preflight` recoupe une liste publique de tournoi avec le
catalogue et les règles déjà présents dans une seconde base PUBLIC. Le résultat
distingue les 60 cartes observées, l'identité de chaque impression, la structure
du deck et la légalité réglementaire au jour et sur la plateforme choisis.

## Commandes PowerShell

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
$referenceDb = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-22 --format standard --platform in_person
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-22 --format standard --platform live --json
```

Les deux chemins PUBLIC, la date, le format et la plateforme sont explicites.
Aucun chemin personnel par défaut n'est consulté. Les bases peuvent être
distinctes : elles restent ouvertes en lecture seule, sans fusion, import,
création ou migration. Aucun fournisseur n'est appelé. Un cache indispensable
absent ou incomplet produit `BLOCKED_WITH_REASON` et des pistes de preuve
manquante; il n'est pas téléchargé ou réparé.

Sans `--select`, la commande utilise les 2 à 4 compositions du
[conseiller existant](OFFLINE_COMPETITIVE_ADVISOR.md), réglables avec `--options`.
Pour consulter une option précise, ajouter `--select 581:1`. On peut répéter
`--select` jusqu'à quatre fois pour des compositions différentes. Les références
invalides, absentes, ambiguës ou réutilisant la même composition sont refusées.
La sélection descriptive existante ne devient pas un classement de force.

## Lire le résultat

Le résumé humain compare les options, les totaux, les impressions résolues et
les raisons bloquantes. `--json` fournit les détails par ligne d'impression :
quantité, nom/set/numéro source, identifiants TCGdex possibles, statut
`legal` / `not_legal` / `unknown`, raisons et données manquantes, marque de
régulation, références des textes de catalogue et assertions officielles
applicables avec source, publication, consultation et période d'effet.
Un errata individuel présent dans le registre est cité avec sa date et son
contenu structuré; sa présence n'atteste pas une couverture complète des errata.

L'identité exige la concordance exacte du code TCG Online, du numéro et du nom
normalisé avec une traduction `present`. Un numéro différent, une traduction
absente ou plusieurs correspondances restent une lacune ou une ambiguïté.
Les codes d'extension manquants sont distingués des numéros et noms non résolus.
Le programme ne devine pas un code de set, une réimpression ou une équivalence
de langue. Le type de carte déclaré est aussi comparé au catalogue.

Le moteur `rules` existant évalue les impressions et les quotas sur les entrées
en mémoire. Il ne crée aucune version de deck. Une structure ne devient
`legal` que si les identités, classifications de base, quotas et exceptions sont
attestés. Une source future, une règle absente ou incomplète conserve `unknown`.
Une restriction explicite ou une violation démontrée donne `not_legal`.
Une rotation H/I/J et l'absence de bannissements ne suffisent pas à elles seules.

Chaque option distingue le nombre de lignes d'impression et les **60 copies**.
Les compteurs `identity`, `printing_legality`, `copy_legality` et
`missing_evidence_counts` affichent leurs dénominateurs. Les mêmes cartes
peuvent apparaître dans plusieurs options; les compteurs interoptions ne sont
pas un inventaire d'impressions distinctes.

Le verdict réglementaire est séparé de la disponibilité d'une impression dans
Live et de la préparation à l'import. `live_availability`, possession, crédits,
fabrication et matchups restent `unknown`. Un deck réglementairement `legal`
sur une fixture peut donc conserver `readiness_status=unknown`. Une liste
publiée en tournoi ne démontre pas son acceptation dans le client Live.
Les textes de catalogue sont des observations mises en cache; ils ne prouvent
pas à eux seuls une identité historique ou une revue complète des errata.

## Résultat local rapporté le 22 octobre 2026

**CODEX_LOCAL_REPORTED**, à partir des caches PUBLIC explicitement sélectionnés.
Le catalogue contient 23 864 impressions et 223 extensions, dont 118 avec un
code TCG Online renseigné. Aucun des codes demandés par les lignes des quatre
options n'a de correspondance dans cette table locale. Ce constat ne signifie
pas que ces cartes sont absentes du catalogue historique.

| Option du conseiller | Copies | Lignes d'impression | Identités résolues | Légalité présentiel / Live |
|---|---:|---:|---:|---|
| Dragapult 581:1 | 60 | 24 | 0/24 | unknown / unknown |
| Basic Box 582:13 | 60 | 28 | 0/28 | unknown / unknown |
| Hydrapple 581:7 | 60 | 23 | 0/23 | unknown / unknown |
| Dhelmise 581:4 | 60 | 22 | 0/22 | unknown / unknown |

Les **97 lignes**, comptées séparément par option, portent
`SET_CODE_MAPPING_MISSING`; les 240 copies cumulent `unknown`. Il n'y a aucune
preuve permettant ici de les déclarer `not_legal`. Les règles de structure
signalent aussi les exceptions de quota et limites spéciales non exhaustives.
La prochaine preuve utile est une correspondance sourcée des codes demandés
vers les extensions PUBLIC, puis une nouvelle évaluation des impressions et
des règles manquantes. Aucun nouveau lot ou téléchargement n'est lancé.

Les JSON détaillés restent locaux. Les quatre appels humain/JSON, sur les deux
plateformes, ont conservé les **52 fichiers PUBLIC contrôlés** (deux bases,
marqueurs, journal de pages et corps référencés), octets et dates inchangés.
Réseau, client de collecte, connexions d'écriture et résolveurs personnels
étaient interdits pendant les appels. Aucun appel interdit n'a été observé.
Ce contrôle Windows est rapporté par Codex et n'est pas certifié par GitHub.

Les exports déjà disponibles restent accessibles par leur référence, par exemple :

```powershell
python -m pokemind meta competitive-export --db $publicDb --event 581 --placement 1
```

Le prévol ne touche pas aux exports, au presse-papiers ou au jeu. Le test
historique d'import texte `FIELD_VALIDATED` n'est pas rejoué.

## Preuves et limites

Les fixtures inventées testent deux bases PUBLIC séparées, 60 cartes,
identités uniques/ambiguës, réimpression, errata, sources futures, règles
incomplètes, restrictions et quotas, erreurs de sélection, refus des chemins
privés, absence de mutation et interdiction du réseau. La preuve CI
`public_deck_preflight_evidence` exige quatre decks synthétiques `legal` en
présentiel et quatre `unknown` sur Live sous les règles **inventées du test**.
Elle ne certifie aucune impression réelle, les bases du PC ou la légalité de
ces quatre listes publiques. Voir les
[preuves assainies](../.orchestrator/EVIDENCE_PM-V1-PUBLIC-DECK-LEGALITY-PREFLIGHT-001.md).

**V1 NOT_RELEASE_READY.** Les autres objectifs visuels, tâches Windows et
récupération demeurent ouverts; STOP pour audit indépendant ChatGPT.
