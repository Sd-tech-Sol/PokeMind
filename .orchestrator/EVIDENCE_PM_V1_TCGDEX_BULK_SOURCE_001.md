# PM-V1-TCGDEX-BULK-SOURCE-001 — preuves de livraison publique

2026-10-19 Québec. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
Résultat : **BULK_BLOCKED_WITH_TESTED_REST_SELECTION_FALLBACK**.
Aucun verdict d'audit indépendant; **V1 NOT_RELEASE_READY**.

## A — Départ et réutilisation

Branche `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
Fetch puis pull ff-only de `0a41ce3` vers
`51d7451669220bb3f029d51d3d6a19fb8447da4f`, sans écrasement local.
HEAD distant confirmé par ls-remote. Avant code/réseau fournisseur :
[CI39346833315](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39346833315)
completed/success au même SHA exact; logs ci_evidence lus, Windows **499/2**,
Ubuntu héritée **498/3**. Prévol local `RUNTIME_READY`, Python3.13/SQLiteFTS5,
aucune base personnelle ouverte. Mandat stable et skill exécuteur lus;
ancien PUBLIC-COVERAGE-001 clos, **jamais rejoué**.

| Solution examinée | Constat | Choix |
|---|---|---|
| Catalogue REST existant `cards.py` | validateurs, tables13, FTS, langues, provenance, curseurs/membership et détails déjà présents | réutilisés, aucun nouveau schéma |
| Campagne existante `public_campaign.py` | workspace dérivé, marqueur, garde owner/unknown, lock, budgets, dry-run et client strict | réutilisée; aucun `--db` ajouté |
| Dépôt officiel TCGdex | données multilingues TypeScript, références de sets/séries et types; textes par langue optionnelle | lecture bornée seulement; import direct bloqué |
| SDK/compilation amont | README propose SDK/API et construction du serveur; aucun snapshot JSON local complet attesté | aucune dépendance installée, aucun code amont exécuté |
| Cloner/télécharger une archive complète | volume comprimé/décomprimé du snapshot et complétude FR non attestés | NOT_MEASURED, aucun essai de clone/archive |
| Sélection REST de détails publics | répond aux identifiants utiles sans coût préalable des scans/sets | repli fonctionnel livré, mesuré sur fixtures et petit échantillon public |

## B — Amont, licence et budget réellement consommé

Commit amont épinglé **`cbddf7e54033b1b58e44af1049c88832e55b94d0`**, date
de commit `2026-10-19T09:03:26Z`, branche master. Métadonnées GitHub indiquant MIT;
[README entier](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/README.md)
et [LICENSE entière](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/LICENSE)
réellement lus. Le fournisseur annonce la base sous MIT, copyright2021TCGdex,
avec obligation de conserver copyright/permissions pour les copies substantielles.
Cela ne certifie pas les droits d'illustrations ou de marques. Aucun corpus,
texte de carte complet, image ou code amont copié dans Git; aucun import bulk.

Structure observée : `data/` par séries/sets, `data-asia/`, `interfaces.d.ts`.
L'arbre Base inspecté, non tronqué, contient 507 entrées / 501 blobs et
891308 octets de tailles déclarées; **seules les métadonnées de cet arbre**
ont été téléchargées, pas les 501 fichiers. Ce n'est pas un dénominateur global.
La taille GitHub déclarée du dépôt n'est pas une mesure d'archive/source décompressée.

Exemples réellement lus au même commit :
[carte bilingue](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Base/Base%20Set/1.ts),
[son set](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Base/Base%20Set.ts),
[carte EN sans FR](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Base/Base%20Set%202/1.ts),
[son set](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Base/Base%20Set%202.ts),
[interfaces](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/interfaces.d.ts).
Imports, références `set: Set`, dictionnaires de traductions et variants ne sont
pas le JSON REST normalisé déjà accepté. Aucun parseur TypeScript partiel ni
réimplémentation du compilateur n'est présenté comme une ingestion complète.
Motif : **UNSUPPORTED_TYPESCRIPT_DEPENDENCIES_AND_UNMEASURED_SNAPSHOT**.
Une voie future demanderait un snapshot de données non exécutables, sa provenance,
ses notices, volumes, schéma et couverture réellement attestés.

| Requêtes de ce lot uniquement | Tentées | Corps lus |
|---|---:|---:|
| GitHub public : repo/commit, README/LICENSE, 3 arbres, interfaces, 2 cartes et 2 sets | 12 | 383951 octets |
| REST TCGdex, 2 IDs × EN/FR | 4 | 8967 octets |
| Reprise de la même sélection | 0 | 0 |
| **Total** | **16 / 30 max** | **392918 octets** |

15 réponses200 et une404 FR; aucun401/403/429/challenge réellement observé.
`Accept-Encoding: identity` : corps lus comprimés/non comprimés identiques,
<40MiB et <120MiB, plus grand corps216776 octets <16MiB. Aucune archive ni
extraction; aucun lien/exécutable amont téléchargé en tant qu'artefact à exécuter.
Compteurs = corps applicatifs effectivement lus, hors en-têtes/TLS et corps404
non lu. Helper local à compteur persistant, flux borné, timeout10s, délai>=0,5s,
HTTPS/hôtes publics fixés, aucun jeton; refus des redirections et arrêt sur
401/403/429/challenge. Pas de lecteur web à GET physiques non comptabilisés.
Les consultations Git/CI du dépôt de travail sont distinctes de ce budget fournisseur.

Caches/registre brut de découverte et mesures demeurent uniquement dans le nouveau
workspace PUBLIC ignoré par Git. Aucun ancien workspace ni dossier personnel
inventorié ou repris. Un incident d'affichage Unicode de la première lecture
documentaire a été corrigé en lisant les octets déjà acquis : **aucun replay GET**.

## C — Fonction livrée et résultat observé

`public_card_selection.py` réutilise les validateurs/upserts de `cards.py`,
les tables catalogue et FTS13; `public_campaign.py` ajoute une sélection optionnelle.
Le comportement de campagne antérieur reste le défaut sans `--card-ids`.

- Entrée : 1–100 IDs exacts et bornés, EN/FR explicites; rejet des doublons,
  encodages alias, séparateurs/traversal et entrées de métadonnées non prévues.
  Sélection exige phase details et budgets officiel/Limitless zéro.
- Dry-run par défaut, sans ouverture/création de DB ni réseau. Exécution seulement
  sous le workspace PUBLIC dérivé; aucun argument DB/snapshot/archive arbitraire.
  Gardes owner/unknown et chemins/aliases conservées; marqueur hardlink désormais refusé.
  Une DB existante de version incompatible est refusée avant écriture, jamais migrée.
- Une transaction par paire carte/langue; rollback du brief et du détail/FTS en cas
  d'échec. Les paires terminées survivent au budget/arrêt, aucun nom FR créé depuis EN.
- Détail présent réutilisé si provenance canonique, hash présent, pas de flag stale
  et date non future <=30jours. Ce cache n'est pas une sonde de changement fournisseur.
  Une absence404 reste distincte de not_fetched/erreur et exige `--recheck-absent`
  pour être redemandée. Refus/challenge strict conservé et blocage persistant pour
  les invocations ultérieures **du parcours de sélection** dans ce workspace.
- Métrologie : détails présents/absents, cache_hits, paires restantes, sélection
  résolue et avertissements. Aucun membership de scan ajouté; catalogue complet=false.
  Une sélection résolue ne prouve ni couverture totale, ni légalité, Live ou possession.

Commande de **prévisualisation** disponible (aucune autorisation de nouveau run
déduite de cet exemple après le STOP) :

```powershell
python -B scripts/lot_i_public_campaign.py --campaign exemple-public --phase details --card-ids base1-1,base4-1 --lang en,fr --tcgdex-budget 4 --meta-budget 0 --official-budget 0
```

`--create --execute-public-campaign` ne s'ajoutent que pour créer/exécuter une
campagne PUBLIC autorisée. Aucun flag de base privée. Après création, reprendre
la même campagne sans `--create`; aucune commande n'est lancée par le rapport.

| Mesure, nouveau workspace distinct | Avant | Après 4 GET | Reprise |
|---|---:|---:|---:|
| Impressions sélectionnées présentes dans le cache | 0 | 2 | 2 |
| Détails EN présents | 0 | 2 | 2 |
| Détails FR présents | 0 | 1 | 1 |
| Absence FR sourcée404 | 0 | 1 | 1 |
| Paires à traiter dans cette sélection | 4 | 0 | 0 |
| GET de l'invocation | — | 4 | **0**, 4 cache_hits |

`base1-1` EN/FR et `base4-1` EN présents; `base4-1` FR absent. Concordance des
langues/ID avec les deux fiches source, pas comparaison exhaustive champ par champ
du corpus. Quatre processus **CLI `cards show --lang en/fr --db <workspacePUBLIC>`**
ont réussi hors ligne; provenance de langue, identité fonctionnelle unknown et
statuts distincts contrôlés. Dates de sortie de set/régulation manquantes restent
unknown; aucun remplissage depuis les fichiers TypeScript.

Gain prouvé sur **fixture**, pas extrapolé à toutes les cartes : pour4GET de
détails, parcours antérieur2 détails cartes présents+2 détails sets; sélection
4 paires cartes résolues (3 présentes+1 absence), aucun coût de scan préalable.
Budget réseau identique. Aucune somme avec les3200/langue de l'ancien lot.

## D — Tests, matrice de clôture et limites

Suite ciblée : **70 passed / 0 skipped**, 13,30s, avec32 nouveaux cas de sélection
et suites cards/public_coverage existantes. Sockets interdits dans la nouvelle
suite, aucune source fournisseur téléchargée en CI. Tests de dry-run, budget
interrompu/reprise/idempotence, FR manquant, stale/datefuture/dateinvalide,
identité incorrecte, texte trop grand, versionDB/marqueur incompatible,
hardlinkDB, owner/unknown déguisé, rollback SQL détail et absence, injection
textuelle inerte, variants, CLI bilingue et gain au même budget.

Les entrées `--snapshot`/`--db` sont refusées avec fixtures JSON sans licence,
TypeScript et fauxZIP. Ce sont des **tests de refus d'une surface inexistante**,
pas la preuve d'un validateur de licence, de traversal d'archive ou d'import bulk.
Aucun extracteur ni parseur tiers n'est ajouté. Les exigences de tests de licence/
archive d'un futur importateur restent bloquées avec cette voie bulk.

Premier run de nouveaux tests corrigé : hypothèses de mesure/nom de champ et
fermeture explicite des connexions SQLite des fixtures sous Windows; échecs
ordinaires de tests, aucun fichier propriétaire. Des résidus synthétiques de
ce premier teardown restent ignorés localement; aucun nettoyage global effectué.

**Suite complète Windows : 530 passed / 3 skipped**, 197,34s. Trois exclusions
héritées : deux OCR absent/non attesté, une création de symlink non permise sur
le Windows local. Compilation compileall et hygiène des fichiers préparés
réussies, diffcheck réussi. CI de livraison PENDING_CI à la publication, à contrôler dans Actions au
HEAD final exact. La CI de départ ne remplace pas ce contrôle.

| Exigence | État de livraison Codex | Preuve/limite |
|---|---|---|
| A synchronisation/CI/lecture/inventaire | DONE | SHA de départ et CI exacts, matrice des solutions |
| B licence et structure amont | DONE pour l'échantillon | sources épinglées et16GET réels; pas preuve mondiale |
| B bornes et isolement public | DONE pour ce lot | 392918octets,16GET, aucun média/archive/secret |
| C import bulk réel | BLOCKED_WITH_REASON | TypeScript avec dépendances; snapshot global/FR non attesté |
| C alternative REST autorisée | DONE mécanisme | sélection/reprise/rollback et gain synthétique, échantillon public |
| C couverture catalogue intégrale | PARTIAL_WITH_EVIDENCE |2 impressions,3 détails; index non scanné et total inconnu |
| D tests adverses du parcours livré | DONE |32 nouveaux cas; tests d'import bulk non revendiqués |
| D suite locale/CI finale | DONE local / PENDING_CI à publication |530/3 Windows,70 ciblés, compilation/hygiène/diffcheck; Actions au HEAD livré à contrôler après push |
| D normes, Live, collection/terrain | PARTIAL/BLOCKED inchangés | aucune assertion normative ou donnée personnelle ajoutée |

STOP final AWAITING_AUDIT; execute_now=false et lancement consommé à la livraison.
ChatGPT doit auditer code/diff/tests, provenance et limites, cohérence STATE/
RESULT/HANDOFF/NEXT_ACTION et CI du HEAD livré. Aucune prochaine campagne autorisée
après ce STOP. Ancien clone privé toujours BLOCKED/0plan, aucun accès à source,
sauvegardes ou ACL privées; aucun clone/migration réelle, installation, OCR,
scheduler, client Live, merge ou force-push. **NOT_RELEASE_READY**.
