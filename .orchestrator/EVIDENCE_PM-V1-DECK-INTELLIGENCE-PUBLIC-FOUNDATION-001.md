# Preuves — PM-V1-DECK-INTELLIGENCE-PUBLIC-FOUNDATION-001

## Portée et point de départ

Démarrage manuel propriétaire; décision D-196, mandat READY et STATE concordants.
Branche `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre;
fetch puis pull ff-only sans perte de `e1c6b75` vers
`affe7ce4a153633bcb8c43ab3c972ce5198e2305`.
[Actions39897884108](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39897884108)
au SHA exact : Windows job120232422923 **846 passed/2 skipped**, Ubuntu
job120232422746 **845 passed/3 skipped**, deux completed/success, logs et preuves
`ci_evidence` / `public_deck_preflight_evidence` lus avant travail fonctionnel.
Prévol local Python3.13.15 : `RUNTIME_READY`, SQLite/FTS5 sans base personnelle.

## Livraison fonctionnelle

- Pont optionnel `public-set-code-bridge-v1`, séparé en mémoire et rapport local,
  depuis les payloads TCGdex déjà vérifiés. Alias univoque, provenance d'import,
  langue, sortie/consultation, abréviation, appartenance, numéro et nom croisés.
  URL canonique de l'objet de set du snapshot conservée; la colonne historique
  de set peut pointer à une carte membre et n'est pas utilisée comme preuve du
  champ d'abréviation. Aucun nom ou alias inventé, aucune nouvelle source réseau.
- Résolveur commun `rules._resolve_structure_identity` et
  `check_deck_entries`, activés pour le prévol PUBLIC avec `--set-aliases`.
  Mode historique sans flag inchangé. Les IDs et DB historiques sont préservés.
- `meta deck-knowledge --selector --as-of --db --reference-db [--set-aliases]`,
  sortie humaine/JSON avant toute sélection implicite de DB. Schéma1/version et
  empreinte de contenu; observations de textes, rôles conditionnels, évolutions,
  attaques/coûts, ressources, setup, séquences à tester, Récompenses et limites.
- `fact`, `inference`, `hypothesis_to_test`, `uncertainty` séparés et sourcés;
  pas de texte carte/traduction généré, pas de nouvelle base/service/framework.
  Export existant, composition publiée recontrôlée et reparsée à 60/60.
- [Guide](../docs/DECK_INTELLIGENCE.md). Données détaillées/exports/rapport alias
  uniquement dans le nouvel espace PUBLIC local ignoré. Git ne contient que
  code, fixtures inventées, documentation et résultats agrégés assainis.

## Mesures réelles sur PC — CODEX_LOCAL_REPORTED uniquement

| Dénominateur | Avant, sans pont | Après, avec pont |
|---|---:|---:|
| Impressions uniques | 0 resolved / 0 ambiguous / 69 unresolved | 62 / 0 / 7 |
| Lignes comptées séparément par option | 0 / 0 / 97 | 87 / 0 / 10 |
| Copies cumulées sur les quatre options | 0 / 0 / 240 | 201 / 0 / 39 |
| Decks legal / not_legal / unknown présentiel | 0 / 0 / 4 | 0 / 0 / 4 |
| Decks legal / not_legal / unknown Live | 0 / 0 / 4 | 0 / 0 / 4 |

Quatorze codes ont une correspondance de métadonnées prouvable dans le cache.
Les sept impressions uniques non résolues sont des Énergies `MEE` : noms
publiés sans « Basic », catalogue avec « Basic ». Le nom n'est pas réécrit et
aucune équivalence n'est promue. Une identité résolue n'est pas une légalité.

| Pilote | Texte natif sourcé / lignes | Attaques observées | Liens d'évolution | Export |
|---|---:|---:|---:|---:|
| Dragapult | 21/24 | 12 | 3 | 60/60 |
| Basic Box | 23/28 | 14 | 0 | 60/60 |
| Hydrapple | 22/23 | 13 | 4 | 60/60 |
| Dhelmise | 21/22 | 12 | 4 | 60/60 |

Quatre fiches `PARTIAL_WITH_EVIDENCE`, JSON et humains, quatre exports identiques
aux sorties compétitives existantes; date2026-10-23. Texte TCGdex descriptif,
normes Pokémon séparées, liste/classement Limitless descriptif; aucun taux de
victoire, classement absolu, capacité Live ou collection fabriqué. Les
suppléments communautaires FR ne sont pas utilisés pour combler le pilote.

Deux caches PUBLIC explicitement connus, marqueurs/namespace validés;
**94 fichiers contrôlés inchangés** (octets, taille et mtime). Instrumentation
pendant les vraies CLI : lecture seule `query_only`, DB autorisées limitées aux
deux caches, réseau/socket/URL, connexion writable, repli DB et presse-papiers
interdits; **0 appel interdit**. Rapports détaillés restent locaux.
**Aucune certification indépendante du PC par GitHub.**

## Collecte et données privées

Enveloppe neuve autorisée30GET/16Mio/1Mio/12découvertes, ≥1s, 1tentative/URL,
STOP refus fournisseur : **non utilisée**. GET fournisseurs0, octets0,
découvertes0; aucun ancien budget repris, aucun reliquat transféré.
Git/GitHub de synchronisation et CI sont distincts du budget de collecte.
Aucun deck principal, DB privée, collection, crédits, journal, capture, client
jeu, tâche OS/scheduler, OCR, backup, migration/restauration/purge ou merge.

## Validation technique

Tests inventés : codes présents/absents/faux/ambigus; conflit natif; préfixes et
remplissage décimal; nom/membership/hash/ID/date/langue/source manquants ou
discordants; provenance épinglée et source unsupported; textes absents/futurs/
périmés; aucune stratégie créée depuis le seul nom; version différente après
changement sourcé; quatre exports60; humain/JSON; refus du privé; réseau interdit.
Les tests prévol/rules/competitive existants conservent les scénarios
réimpression/errata/structure et Live unknown.

Le nouveau marqueur `deck_knowledge_evidence` est issu d'une propriété JUnit
unique et bornée. Le publieur refuse absence, doublon, mauvais scope, faux
compteurs, accès réseau ou promotion du vrai cache; il filtre les champs libres.
Fixtures uniquement : quatre fiches/export60, pont sourcé, ambiguïté bloquée,
séparation faits/hypothèses, cache inchangé et inconnus conservés. Ce marqueur
ne certifie aucun texte réel ni la légalité des listes du PC.

Résultats finaux de tests et de publication consignés dans RESULT/STATE.
La CI de livraison doit être contrôlée **au HEAD exact publié**, deux jobs
Windows/Ubuntu completed/success. La CI de départ ne remplace pas ce contrôle.
Les preuves finales durables sont dans Actions après push; pas d'auto-VERIFIED.

## Arrêt

`AWAITING_AUDIT`, execute_now=false, consumed=true; STOP ChatGPT indépendant.
DKI-03/04/05/06 non exécutés; aucun nouveau lot préparé ou lancé. Autres portes
A–J conservées. **V1 NOT_RELEASE_READY.**
