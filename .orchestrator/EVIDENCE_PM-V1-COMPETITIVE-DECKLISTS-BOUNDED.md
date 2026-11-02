# PM-V1-COMPETITIVE-DECKLISTS-BOUNDED — preuves assainies

Exécution manuelle propriétaire, 2026-10-22 Québec. **CODEX_LOCAL_REPORTED**
pour toute collecte et opération sur le cache réel; aucune auto-certification
indépendante. V1 NOT_RELEASE_READY. Les pages, listes, corps HTTP et preuves
locales détaillées restent hors Git. Aucun nom de joueur, donnée personnelle,
chemin absolu, DB, manifeste privé ou empreinte privée dans ce rapport.

## Prévol et autorisation

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, arbre initial
  propre; fetch + pull ff-only de9bc2bcb vers
  `22e5e00c4e430880c8896a8414119f0c4282b919`, sans perte de travail local.
- Mandat/STATE/NEXT_ACTION synchronisés READY,execute_now=true,consumed=false;
  démarrage manuel confirmé dans la session. Aucun nouveau go demandé.
- CI préalable [Actions39872809188](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39872809188),
  exact22e5e00 : Windows120151387945,730passed/2skipped;
  Ubuntu120151387480,729passed/3skipped. Deux jobs completed/success, marqueurs
  `ci_evidence`/`rules_registry_evidence` lus. Collecte commencée après succès.
- `preflight` : Python3.13.15,SQLite3.50.4,FTS5,aucune DB propriétaire ouverte.
  `demo` : SYNTHETIC_REHEARSAL_PASSED,79CLI/13checkpoints,aucun réseau/OCR/OS.

## Matrice des exigences de ce mandat

| Exigence | État de portée | Preuve et limite |
|---|---|---|
| Qualifier sources/robots/conditions | DONE (CODEX_LOCAL_REPORTED) | Robots,about,legal,privacy lus avant les événements; pas de licence ouverte de redistribution établie, corpus local seulement et attribution |
| 1–3 tournois Standard récents | DONE (CODEX_LOCAL_REPORTED) | Nice582,17octobre2026,2336participants; Louisville581,10octobre2026,2927participants; index Standard contrôlé sur URL/date/nom/taille |
| 15–45 listes complètes variées | DONE (CODEX_LOCAL_REPORTED) |32placements des deux top16 publiés,28URL/compositions uniques,15étiquettes d'archétypes; totaux des trois sections et60cartes contrôlés; aucun nom de joueur persisté dans les tables |
| Cache PUBLIC local exclusivement | DONE (CODEX_LOCAL_REPORTED) | Espace neuf marqué, contrôle namespace/reparse/hardlink et absence de tables propriétaire peuplées;2nouvelles tables `meta_competitive_*`,versionlogicielle13 conservée;aucune base existante migrée |
| Provenance/date/résultat/dénominateur | PARTIAL_WITH_EVIDENCE | URL/date/format/placement,empreintes de pages PUBLIC et instant de collecte restent dans cache; statistiques phase2 dénominateurs547 et429,distincts des participants;BO1/BO3unknown |
| Hors ligne/idempotence/export | DONE (CODEX_LOCAL_REPORTED) | Réimport32lignes stable,intégritéok/FK0;32textes exportés et reparsés60cartes,aucune mutation DB sur consultation/export;4exports CLI comparatifs réussis |
| Comparer Dragapult et alternatives | PARTIAL_WITH_EVIDENCE |[Comparaison](../docs/COMPETITIVE_DECKLISTS_20261022.md) : Dragapult,Basic Box,Hydrapple,Dhelmise;10textes de cartes clés consultés;déductions conditionnelles,pas de winrates ni légalité/collection inventés |
| Tests et CI | DONE_LOCAL_QA / PENDING_DELIVERY_CI_AT_COMMIT |67tests ciblés réussis;suite complète772passed/3skipped en330,70s;CI finale au HEAD exact à contrôler après push |
| Publication assainie et STOP audit | AWAITING_AUDIT | RESULT/HANDOFF/NEXT_ACTION/STATE/NEXT_PROMPT fermés ensemble,permissions consommées;commit/push autorisés des seules pièces assainies puis contrôle CI,aucune nouvelle tâche lancée |

## Enveloppe réseau de ce lot, close

**47GET directs/100,2 846 587octets/67 108 864**,maximum lu par réponse497265
sur2097152. Sept recherches Web de découverte sur40, aucune réponse de recherche
importée comme liste. Le collecteur journalise les réservations avant l'I/O,
compte les corps sans décompression (`identity`),espace les appels d'au moins1s,
refuse redirections/URL hors portée/doublons/challenges/encodages inattendus,
arrête le fournisseur sur erreur/refus/cap et ne retente aucune URL. Verrou de
processus et relecture du compteur évitent deux réservations concurrentes.
Les corps complets sont relus hors ligne avec leur empreinte PUBLIC.

Détail47 :4pages de qualification,1index Standard ciblé,2pages de résultats,
2statistiques de phase2,28pages de listes uniques,10pages de cartes clés.
Aucun HTTP401/403/429/challenge rencontré,aucun plafond dépassé,aucun ancien
GET API arrêté à8MiB repris. Statut final de l'enveloppe
`COMPLETED_BATCH_NO_RESTART`;les53GET inutilisés ne sont pas une permission.
Les métriques de découverte Web sont distinctes des GET directs mesurables.

L'encodage d'affichage du terminal a nécessité une correction locale après
téléchargement de la page about :relecture du corps déjà en cache,**zéro GET
répété**. Un test de conflit a révélé une réinitialisation inutile du schéma
PUBLIC :l'import initialise maintenant seulement une DB neuve et refuse toute
migration existante;le test de non-mutation au conflit réussit. Aucun de ces
incidents techniques ordinaires n'a ouvert de donnée privée ou réactivé une source.

## Code et preuve reproductible dans GitHub

- `src/pokemind/competitive.py` :petites pages bornées,parseurs HTML statiques
  sans exécution de code amont,qualification Standard par index,validation des
  sections/impressions/60cartes,SQLitePUBLIC,idempotence et conflits explicites.
- `scripts/import_competitive_pages.py` :plan sans I/O par défaut;application
  **hors ligne seulement**,1–3événements/45listes max,aucun fallback DB privée.
- CLI `meta competitive-summary` et `competitive-export` :`--db` PUBLIC requis
  avant `_db_for`,sans réseau,presse-papiers ou mutation du deck joué.
- `tests/test_competitive.py` :pages/index/listes entièrement synthétiques;
  limites,refus,reprise impossible après interruption/clôture,cache,provenance,
  date future,format,sections60,SQLitevide,idempotence/conflits,CLI,lecture seule.
- Le publieurCI exige une propriété JUnit synthétique
  `public_competitive_reproduction`,filtre son contenu et publie
  `competitive_pages_evidence` au SHA réellement testé. Preuve manquante,
  dupliquée,59cartes ou promotion de la base réelle refusée. Le précédent
  `rules_registry_evidence` garde sa portée synthétique et ses registres inchangés.

La CI prouve uniquement le parseur/chargement/export sur **fixtures inventées**.
Elle ne télécharge pas les pages réelles et ne certifie pas le cache PUBLIC du
PC. Le corpus réel n'a pas été copié dans les fixtures ni dans un artefact CI.

## Limites conservées et audit attendu

Sélection de bons placements,deux événements présentiels,phase2 partielle;
pas de dénominateur tous joueurs pour la représentation des decks,pas de matchs
importés,pas de conversion de points en victoire. BO1/BO3,matchups,conseil
personnalisé,cartes possédées,crédits et légalité TCG Live inconnus. Les versions
régulières affichées par le fournisseur ne certifient pas les impressions
physiques enregistrées au tournoi. Aucun test jeu/presse-papiers répété.

Aucun accès decks/collection/journaux/DB privée,capture,OCR,client du jeu,
planificateur,service,compte,backup,migration,restauration,purge,merge,reset ou
force-push. Tests sur fixtures synthétiques uniquement. Les autres objectifs
V1 restent entiers;V1 NOT_RELEASE_READY.

ChatGPT doit examiner le diff depuis22e5e00,les nouvelles gardes/tests,les sources
publiques liées,le HEAD distant et **les deux jobs au SHA exact de livraison**.
Le statut CI au moment du commit doit être lu dans GitHub Actions;ne jamais
substituer la CI préalable à la CI finale. La collecte réelle reste rapportée
localement,même si la CI finale est verte. Après publication :STOP.

## Validation locale finale

Suite complète **772passed/3skipped en330,70s**,Python3.13.15. Les skips sont
les deux scénarios OCR réel non autorisés/attestés et un symlink non permis sur
ce Windows;ils ne sont pas présentés comme réussis. **67tests ciblés** passent.
Compilation de src/tests/scripts,hygiène Git et `git diff --check` réussis.
Le JUnit complet local contient une seule preuve publique synthétique de
listes compétitives et une seule preuve des registres officiels.

La CI finale n'existe qu'après push :**PENDING_AT_COMMIT**,résultat durable
consultable dans GitHub Actions au SHA exact contenant ces documents. Le
contrôle post-push doit lire les deux jobs/logs et leur HEAD;pas de substitution
par le prévol. Aucun statut VERIFIED attribué par Codex.
