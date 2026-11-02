# PM-V1-REST-FR-EN-COVERAGE-001 — campagne PUBLIC partielle, STOP source

2026-10-21 Québec /2026-10-22 UTC. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
**PARTIAL_WITH_EVIDENCE / SOURCE_ERROR**, collecte arrêtée après63GET.
V1 **NOT_RELEASE_READY**. Aucune reprise ou utilisation du reliquat autorisée.

## A — Prévol et droits

Branche autorisée work/pm-v1-lotj-final-readiness-windows, arbre initial propre.
Fetch puis pull --ff-only sans perte depuis249a30158ca02b619dd3dcaa514f025c1e89519e
vers **a8a9ed992952e181768ef43fef06de8ebfd60fbe**; HEAD distant identique.
AGENTS, continuité/adoption V2, STATE, premier NEXT_ACTION, NEXT_PROMPT, mandat
complet, instructions actives HANDOFF/RESULT/DECISIONS, skill exécuteur,
AUTONOMY_POLICY, PROJECT_SPEC, matrice J, sources et preuves PUBLIC/BULK/
alternatives relus. Anciens mandats/budgets consommés, jamais rejoués.

[CI39706243935](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39706243935)
initialement in_progress : WAIT_CI_NO_FUNCTIONAL_WORK, deux attentes45s, aucune
phase fonctionnelle ni écriture/collecte pendant l'attente. Puis completed/success
au SHA exact **a8a9ed992952e181768ef43fef06de8ebfd60fbe**, Windows119586836561 et
Ubuntu119586836775 completed/success. Branche/HEAD local/distant, arbre propre,
ID READY et execute_now=true/consumed=false revalidés avant démarrage.
Aucun watcher ou workflow relancé.

Prévol local : RUNTIME_READY, Python3.13.15, SQLite3.50.4/FTS5,
owner_database_opened=false, network_used=false, writes_to_disk=0.

Droits du seul REST TCGdex relus dans les éléments versionnés autorisés :
[registre](../docs/SOURCES_CONNAISSANCES.md), [PUBLIC](EVIDENCE_PM_V1_PUBLIC_COVERAGE_001.md)
et [BULK](EVIDENCE_PM_V1_TCGDEX_BULK_SOURCE_001.md). Ils documentent APIv2 publique
sans clé, cache recommandé, absence de plafond dur publié, MIT TCGdex
copyright2021 et notice au commit cbddf7e54033b1b58e44af1049c88832e55b94d0.
Aucune autorisation d'aspiration illimitée ni de réutilisation des images/marques.
Attribution et texte MIT standard reproduits localement avec cette provenance;
aucun corpus redistribué. Pas de nouvelle consultation externe pour les droits,
conformément au mandat; cette revue n'est pas une certification juridique actuelle.

public_campaign/cards/catalog_snapshots/public_card_selection et l'entrée CLI
existante relus : budget débité avant transmission, redirects/retries inclus,
HTTPS/hôte/endpoints bornés, intervalle0,5s, timeout10s, JSON8MiB max,
stop_on_access_denial pour401/403/429/non-JSON/challenge reconnu. Aucun nouveau
programme/service/SDK/helper de collecte, code produit ou schéma ajouté.

Dry-run du script existant, campagne au nom neuf dérivé du mandat, phase index,
budgets24/0/0, --create sans --execute-public-campaign : mode=dry_run,
network_used=false, owner_database_opened=false. Emplacement exact inexistant
après dry-run, ignoré par Git; aucune liste d'anciens espaces consultée.

## B — Campagne nouvelle et compteur par invocation

Un seul espace PUBLIC neuf créé exclusivement par le mécanisme versionné avec
--create au premier appel. Garde owner/unknown, marqueur, ancêtres/reparse,
alias et verrou existants conservés. Aucune DB préexistante ouverte/copiée.
Le préfixe lot-i du mécanisme ne change pas l'identité de cette nouvelle campagne.

Commande via `python -B scripts/lot_i_public_campaign.py` :

```text
--campaign pm-v1-rest-fr-en-coverage-001-4c7a2d8f
--phase index --tcgdex-budget 24 --meta-budget 0 --official-budget 0
--execute-public-campaign
```

--create seulement au premier appel; aucune entrée --db/--card-ids ou fichier
privé. Rapports par invocation, notice et couverture finale uniquement dans
le nouvel espace ignoré. Plan maximal4index puis4details; arrêt au troisième
index, **3invocations/8,63GET/192,129GET inutilisés et non réutilisables**.

| Invocation | GET tentés | Pages valides ajoutées | Membres cartes EN/FR | Union impressions | Détails EN/FR | Arrêt |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Avant | 0 | 0 | 0/0 | 0 | 0/0 | espace inexistant |
| 1,index/create | 24 | 24 | 800/800 | 890 | 0/0 | budget normal |
| 2,index | 24 | 24 | 2000/2000 | 2213 | 0/0 | budget normal |
| 3,index | 15 | 12 | 2600/2600 | 2871 | 0/0 | source_error,STOP |
| **Total** | **63** | **60** | **2600/2600** | **2871** | **0/0** | **aucun autre appel** |

Métadonnées catalogue :63GET =24+24+15 =setsEN4+setsFR4+cardsEN29+cardsFR26.
Chaque invocation respecte24GET. **60opérations de pages valides,3tentatives
sans nouvelle page validée,0refus strict signalé.** Les rapports ne conservent
pas les statuts HTTP de ces3tentatives ni la répartition retry/redirection/
échec final. Ne pas transformer63GET en63HTTP200, ni ces3GET en3refus d'accès.
Aucune absence404 carte/set enregistrée; détails non commencés. Le statut HTTP
de l'échec d'index demeure inconnu. Aucun GET officiel/Limitless/TrainerHill/image.

## C — STOP et couverture

Invocation3 : error=TCGDEX_INVALID_INPUT_OR_STATE, stopped_reason=source_error,
blocked_reason=null,15GET. Le contrôle immédiatement après retour CLI constate
l'erreur et arrête l'orchestration. Aucun GET après ce constat, aucun appel4,
aucune phase détails ou relance. Erreur stockée : cards:en,curseur27,
2026-10-22T01:40:34Z; snapshot INDEX_OBSERVATION_FAILED.
**Cause précise UNKNOWN** : code neutre insuffisant pour attribuer réseau/HTTP/
JSON/forme/validation. Aucune charge défaillante conservée par le rapport,
aucun diagnostic par nouvelle requête ou correctif spéculatif. Garde strict
conservé; aucun401/403/429/challenge reconnu signalé. Reliquat non autorisant.

| Scope | Membres | Pages/état | Dénominateur établi | Détails frais/absents |
| --- | ---: | --- | --- | ---: |
| sets EN | 220 | 4,fin confirmée par page vide | 220 pour ce scan seulement | 0/0 |
| sets FR | 202 | 4,fin confirmée par page vide | 202 pour ce scan seulement | 0/0 |
| cartes EN | 2600 | 26,partial,erreur avant page27 validée | unknown,fin non atteinte | 0/0 |
| cartes FR | 2600 | 26,partial,curseur27 | unknown,fin non atteinte | 0/0 |

Union locale **223sets/2871impressions**. Par langue :2600noms de briefs,
0détail présent/0absence attestée/2871détails cartes non récupérés,223détails
sets non récupérés. Différence entre union et noms ≠ absence de traduction.
0détail stale (aucun détail),0doublon de membres et0trou dans les quatre scans;
aucun conflit d'identité fonctionnelle prétendument résolu. Scans commencés
2026-10-22T01:38:46–48Z; sets terminés01:38:54Z, dernières pages EN01:40:30Z et
FR01:40:31Z. Aucun flag stale/date future ou durée anormale signalé.

Contrôle agrégé en lecture seule de la nouvelle DB PUBLIC explicite : les2871
briefs ont URL TCGdex et date non vide. Hashes publics/membership conservés
localement; aucun hash privé consulté.0assertion normative, aucune équivalence,
réimpression, règle, Standard/Live, propriété ou coût déduit des noms/IDs.

Gain dans cette seule campagne :0→2871impressions de briefs et0→2600membres
cartes par langue, **0→0détail riche**.45,57impressions distinctes/GET tenté,
dépendant de cette pagination; aucun rendement mondial/futur extrapolé.
Anciennes campagnes3200/langue/12détails et sélection2impressions restent
historiques séparées, jamais additionnées, leurs bases non consultées.

Travail connu sur l'union découverte :**6188GET de détails** encore nécessaires
(5742paires cartes+446paires sets), hors croissance et index restant unknown.
current_indexes_complete=false,complete=false,details_complete_on_discovered=false.
Les dénominateurs des sets sont ceux de scans non atomiques seulement; aucun
100%,total mondial ou complétude FR/EN attesté.

Pour une éventuelle suite après audit : établir la cause sur preuve appropriée
avant de décider une nouvelle collecte; détails bilingues encore tous manquants.
Ce constat ne prépare aucun mandat et n'autorise ni curseur27 ni reprise du workspace.

## D — Tests synthétiques et contrôles

80tests ciblés réussis avant collecte,15,91s,0skip :

```text
python -B -m pytest tests/test_cards.py tests/test_public_coverage.py tests/test_lot_j_knowledge.py tests/test_public_card_selection.py tests/test_lot_i_e2e.py::test_campaign_no_network_by_default_and_resumes_only_public_workspace -q
```

Budgets/retries/redirects/reprises, snapshots/doublons/gaps, provenance/langues,
dates, gardes PUBLIC, arrêts403/429/challenge couverts par fixtures existantes.
Aucun nouveau test ajouté : cause spécifique de l'erreur réelle non reproduite,
aucun correctif/garde assoupli pour la masquer. Aucun corpus réel en fixture/CI.

Suite complète `python -B -m pytest -q` : **553 passed/3 skipped**,287,81s,
Windows Python3.13.15/pytest9.1.1,aucun échec. Skips hérités :2OCR réel
absent/non attesté et1symlink Windows non permis localement; aucun skip ajouté.

Compilation src/tests/scripts réussie. Hygiène/secret scan des292fichiers
versionnés,nouvelle preuve incluse,git diff --cached --check,cohérence JSON/rapports,
périmètre exact8documents et scan des ajouts sans chemin privé réussis.
Aucune DB/réponse brute/notice locale/artefact ignoré préparé. Aucun support Linux ajouté.

## E — Livraison

Collecte PARTIAL_WITH_EVIDENCE; quatrième index et détails BLOCKED_WITH_REASON
par STOP source. Contrôles et rapport poursuivis hors réseau seulement.
STATE/RESULT/HANDOFF/NEXT_ACTION/DECISIONS synchronisés à AWAITING_AUDIT,
execute_now=false, autorisation consommée puisque63GET effectifs.
CI du rapport PENDING_CI à publication; contrôle HEAD distant et Windows/Ubuntu
au SHA final exact après push. STOP audit indépendant ChatGPT, sans auto-VERIFIED
ou nouveau mandat.

Aucune donnée/métadonnée personnelle de DB/backup/ACL/deck/log/capture ou autre
projet, aucun ancien workspace, autre fournisseur, OCR/installation/scheduler/
achat/Live, vrai backup/clone/restore/migration, merge/reset/force-push.
Les bases/récupérations de la suite restent synthétiques. Ancien clone privé
BLOCKED; **V1 NOT_RELEASE_READY**.
