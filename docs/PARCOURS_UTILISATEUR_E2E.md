# Parcours joueur V1 reproductible — fixtures hors ligne

2026-10-20. Mandat `PM-V1-USER-JOURNEY-E2E-001`, livraison Codex à auditer.
**V1 NOT_RELEASE_READY.** Aucune connaissance Pokémon réelle actualisée dans ce lot.
Historique2026-10-20 : la CI Windows du code5b8a543 échouait sur le dernier appel
instrumenté `v1 readiness`; le STOP et les runs rouges restent documentés.
Le mandat ciblé2026-10-21 a reproduit la cause sous Python3.11 : le helper système
Python tentait d'appeler `ver`, refusé par le garde. Readiness évite maintenant
ce processus; le garde reste actif. Les validations locales et la CI au SHA de
livraison sont distinguées dans les [preuves du correctif](../.orchestrator/EVIDENCE_PM_V1_E2E_WINDOWS_READINESS_FIX_001.md).
Seul l'audit indépendant peut accepter le lot E2E complet.

Depuis la racine du dépôt Windows, avec Python et pytest déjà disponibles :

```powershell
python -m pokemind preflight --json
python -m pokemind demo --json
python -m pytest -q tests/test_user_journey_e2e.py
```

Le prévol utilise FTS en mémoire. La démo n'accepte pas de base en argument :
elle crée un espace neuf sous `data/local/demo-runs`, transmet sa base explicitement
à chaque CLI et retire seulement cet espace. Les exports restent dans ce même
espace. Aucun presse-papiers, compte, client Live, paquet, OCR ou tâche OS utilisé.
Le rapport indique 13 checkpoints passés et 79 processus CLI neufs.
Les diagnostics `match capabilities`, `match preflight` et `match benchmark-ocr` évitent aussi le
sélecteur de base : trois régressions vérifient l'absence de toute inspection du
chemin SQLite par défaut, sans exécuter de moteur OCR.

Le test E2E bloque les sockets/DNS dans le parent et dans **chaque enfant**;
dans les enfants il refuse aussi toute ouverture SQLite/fichier local hors de
la fixture et tout processus externe. Le nom d'hôte est simulé. Cinq tests de
contrôle prouvent le refus DNS/socket/DB/fichier/processus. Ces gardes sont
temporaires au test, sans installation ni surveillance. Le mode démo utilise
uniquement un client catalogue fictif, des fichiers versionnés et des commandes
hors ligne. Une sortie `network_used=false` n'est pas, à elle seule, la preuve réseau.

## Séquence observée

Les fragments ci-dessous décrivent les commandes réellement lancées par la démo;
le lanceur ajoute toujours `--db F --json`. `F`, `DECK`, `LOG`, `CHANGES`, `REGISTRY`,
`PNG`, `ANNOTATION` et les identifiants désignent exclusivement les artefacts
générés automatiquement dans la fixture. Ne pas remplacer F par une base réelle
pour reproduire cet essai. Les assertions détaillées sont dans `demo.py` et
`tests/test_user_journey_e2e.py`.

| Checkpoint | Commandes réelles principales | Résultat et limites |
|---|---|---|
| 1 démarrage | prévol puis SQLite FTS5 en mémoire | runtime prêt, aucune base personnelle |
| 2 bibliothèque | `import-seed` ×2 | quatre volumes, réimport idempotent |
| 3 recherche | `search récompenses --limit 1`, puis neuf autres questions | dix citations `.md`, date source et lignes; connaissances versionnées |
| 4 cartes | client `DemoCatalogClient` + `cards search "Nom jumeau" --lang fr`, `cards show syn1-1 --lang fr` et EN | un résultat par langue, identité/provenance affichées; aucune exhaustivité/équivalence Live inférée |
| 5 deck | `deck import DECK --deck synthetic` ×2, `deck compare synthetic --from-version 1 --to-version 2`, `deck export synthetic`, réimport `--deck roundtrip` | deux versions exactes de 60, légalité/structure initiales `unknown`; fichiers jetables |
| 6 parties | `log import LOG --deck synthetic` ×10, `profile summary/review --deck synthetic`, `battle lessons --deck synthetic --as-of DATE` | cinq journaux distincts chacun importé deux fois; n=5, trois victoires/une défaite/une issue inconnue, dénominateur descriptif=4; aucune causalité démontrée |
| 7 conseils | `recommend deck synthetic --as-of DATE_LOCALE` | `INSUFFICIENT_EVIDENCE`, collection/crédits inconnus; aucun coût inventé |
| 8 versions jouées | `deck link-candidates --deck synthetic`, `deck link-battle --deck synthetic --battle-id B --version 2` preview/apply/répétition, `deck version-evidence`, `deck unlink-battle` preview/apply | cinq parties initialement sans lien; une attestation active après répétition, zéro après révocation; previews sans écriture |
| 9 candidat | `deck candidate-create --changes CHANGES` preview/apply, `deck candidate-show --candidate C`, `deck candidate-export --candidate C` preview/apply, réimport `--deck candidate-roundtrip` | candidat60 de légalité inconnue, version jouée2 conservée, collection inconnue, zéro crédit dépensé; export dans drafts jetable |
| 10 légalité | `rules load-official --registry REGISTRY`, `rules check-deck tri-state --format standard --platform live --as-of 2026-01-02` ×3, puis date2026-01-04 | règles **fabriquées** pour trois impressions fictives : `legal`, restriction `not_legal`, source non vérifiée `unknown`, source expirée `unknown`; aucun verdict réel |
| 11 coach | `match start`, `match observe --image PNG --annotation ANNOTATION --session S --turn N` et `match advise` ×3, `match show/correct/show`, conseil en contexte contradictoire, `match close` | trois tours, correction versionnée, mémoire entre processus, zéro pixel conservé en DB, zéro coup certifié; avertissements/informations cachées explicites, OCR non exécuté |
| 12 actualisations | `knowledge update --mode daily/deep --dry-run`, `knowledge status`, `knowledge cadence --start-utc 2026-10-31T00:00:00Z --daily-time 01:30 --deep-time 05:00 --days 5`, scheduler install/status/uninstall `--dry-run` | base inchangée par les plans, zéro réseau; Toronto/DST simulé, fuseau Windows déclaré, aucun OS observé/activé |
| 13 readiness | `v1 readiness` | `NOT_RELEASE_READY`, portes réelles maintenues |

Les dates du conseil utilisent le calendrier local pour collection/crédits;
les preuves importées restent datées UTC. Quatre régressions hiver/été avant/après
minuit Toronto conservent le parcours et le refus des dates locales futures.
Les drapeaux `--apply --confirm-owner` dans cet essai ne concernent que les fixtures.

## Récupération fictive complémentaire

Le test `test_schema7_backup_clone_migration_public_cli_offline` réutilise la
fixture historique7 existante, sous un répertoire neuf `data/local/test-runs`.
Il effectue neuf CLI avec réseau/processus externes bloqués : `backup plan`,
`backup create`, `backup verify`, puis pour chacun des deux noms neufs de clone
`restore plan`, `restore apply` et refus du même apply sur cible déjà existante.
Le clone7 conserve7; le second utilise `--migrate-clone` et passe à13.
SQLite/FK/FTS et les anciennes histoires concordent, source/backup restent
identiques octet pour octet. Il n'y a aucun accès aux sauvegardes personnelles,
ni ACL, activation ou migration réelle. La démo joueur n'effectue pas de backup.

## Acceptation terrain après audit indépendant

Cet ordre prépare les futurs mandats; il ne les autorise pas. Les campagnes
BULK/PUBLIC-COVERAGE restent terminées, sans rejeu. Les lacunes de catalogue FR/EN,
normes/reprints/errata/Live, méta et Trainer Hill restent des exigences V1, même
si tous les essais fictifs réussissent.

1. **GitHub et sûreté** : ChatGPT audite le SHA livré, le diff et les deux CI.
   Pour le backup moderne déjà tenté/vérifié selon le rapport local, conserver
   le STOP courant : aucune nouvelle création et aucun rejeu d'une permission.
   Le dossier privé clone7 demeure BLOCKED; un futur mandat doit résoudre les
   prérequis et choisir les fichiers précis, sans déduire un accès des archives.
2. **Clones et activation** : après nouvel ordre ciblé seulement, choisir deux
   noms neufs pour clone7 et clone13, vérifier les plans, migrer le second puis
   comparer intégrité, histoires, versions et FTS avant toute sélection explicite.
   Checkpoint avant chaque écriture. Repli : cesser le clone et choisir la base
   précédente; conserver tous les artefacts, sans remplacement/purge.
3. **Deck et combats** : après ordre sur les fichiers/base choisis, importer un
   export réel de60 puis au moins cinq journaux valides, répéter un import et
   vérifier n/inconnues. Confirmer chaque version réellement jouée; révoquer les
   associations erronées. Candidat distinct, export seulement après choix; aucun
   changement du client ni achat. Repli : révoquer les liens et conserver l'historique.
4. **OCR et entraînement** : sélectionner version/distributeur/licence/hashes/packs,
   autoriser séparément installation puis exécution, et calibrer avant trois
   décisions avec images volontairement attachées en entraînement permis.
   Checkpoints : prévol, benchmark, revue des lectures et incertitudes. Repli :
   cesser le moteur, corriger/révoquer les annotations; aucune certitude par fixture.
5. **Actualisations OS** : choisir heures et base publique, audit ciblé du verrou
   scheduler actuellement fermé, puis accord propre pour installation/essai.
   Observer fuseau OS, quotidienne et mardi/vendredi, retry, statut et désinstallation.
   Repli après futur mandat : désinstaller les deux tâches choisies sans effacer
   les données. Le dry-run ne prouve pas le comportement d'un PC éteint ou le DST réel.

Le [protocole propriétaire Windows](VALIDATION_PROPRIETAIRE_V1_WINDOWS.md)
décrit les commandes et risques. La CI prouve les tests sur runners; le rapport
local Codex ne vaut pas audit indépendant du PC. Aucun `RELEASE_READY` ni merge.
