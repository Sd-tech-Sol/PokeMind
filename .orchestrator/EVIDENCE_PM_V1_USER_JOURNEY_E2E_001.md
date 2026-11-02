# Preuves — PM-V1-USER-JOURNEY-E2E-001

2026-10-20 Québec. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
Livraison à auditer indépendamment par ChatGPT. **V1 NOT_RELEASE_READY**.

## STOP après la CI de livraison — échec Windows

Le contrôle post-push du code livré **5b8a543242bd08f04327ac6f418f815120b5646c**
constate [run39467579068](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39467579068)
`completed/failure` : Windows **1 failed/542 passed/2 skipped**, Ubuntu
**542 passed/3 skipped**, ce dernier `ci_evidence` confirme le SHA exact.
Le test en échec est
`test_complete_player_journey_blocks_network_in_every_cli_child`, à son dernier
appel `v1 readiness`, qui retourne `DEMO_CLI_STEP_FAILED:v1`. La façade de démo
n'expose pas la sortie détaillée de cet enfant : **cause exacte UNKNOWN**.
Ne pas conclure à un accès réseau, à une corruption de DB ou à un défaut produit
particulier sans preuve; l'échec pourrait concerner le test ou l'appel CLI.

**STOP selon la condition propriétaire « STOP si elle échoue ».** Aucune correction,
réexécution de test local, relance de workflow ou opération privée après ce constat.
Seul ce complément documentaire assaini est publié conformément à la continuité.
Les 14 étapes et 542/3 ci-dessous sont des **observations locales**, pas une
validation de livraison Windows. Statut **PARTIAL / AWAITING_AUDIT**, autorisation
consommée et execute_now=false. ChatGPT doit auditer puis établir un nouveau
mandat explicite si une reproduction/correction est voulue.
La CI du commit documentaire de ce complément est PENDING_CI à publication;
contrôler son HEAD exact dans Actions, sans assimiler une autre exécution à une
explication de la panne initiale. V1 NOT_RELEASE_READY.

## Prévol et périmètre

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
  Synchronisation `fetch` puis `pull --ff-only`, sans écrasement, du checkpoint
  `0dcad51891f879178d6f1b159663e579a477a694` au HEAD préparé
  `a13ac1ae84796d1a4ca82ccdf0becd7f01ec526d`.
- AGENTS, continuité/adoption V2, STATE et premier NEXT_ACTION concordants,
  HANDOFF/RESULT/DECISIONS, skill exécuteur, mandat A–F intégral, autonomie,
  matrice J et guides Windows/CLI consultés. Seul mandat E2E exécuté;
  BULK et PUBLIC-COVERAGE terminés, sans rejeu.
- **CI de départ directement consultée sur GitHub** :
  [run39352842189](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39352842189),
  `completed/success` sur **a13ac1ae84796d1a4ca82ccdf0becd7f01ec526d**.
  Windows job118400807192 : **531 passed/2 skipped**;
  Ubuntu hérité job118400806791 : **530 passed/3 skipped**.
  Logs `ci_evidence` au même SHA lus avant les tests locaux.
- Prévol local : `RUNTIME_READY`, Python3.13.15, SQLite3.50.4, FTS5 mémoire;
  zéro écriture de prévol. Aucun paquet installé.
- Inventaire par `--help` de la CLI, deck, match, knowledge,
  candidate-export, rules load-official et restore apply; implémentations/tests
  existants réutilisés. Aucun flag inventé ni nouvel outil OS.

## Parcours reproductible et résultats

**14 étapes synthétiques passées localement; livraison Windows non validée** :
13 checkpoints joueur dans **79 processus CLI**, plus une étape récupération
dans **9 processus CLI**. Les cinq sondes négatives des gardes sont des refus
attendus, pas des étapes joueur échouées. Les trois diagnostics DB-free et les
deux tests d'export sont des régressions supplémentaires.

Le [guide opérateur](../docs/PARCOURS_UTILISATEUR_E2E.md) contient chaque étape,
les commandes et leurs substituts de fixture, résultats, inconnues et limites.
Les 79 appels utilisent tous un `--db` temporaire explicitement fourni; aucun
fichier réel du propriétaire n'est sélectionné ou inventorié.

| Étapes | Preuve observée | Inconnues conservées |
|---|---|---|
| 1–3 premier usage/bibliothèque | FTS mémoire, quatre volumes importés deux fois, dix recherches avec citation `.md`, date2026-10-09 et lignes contrôlées | règles Pokémon changeantes non actualisées |
| 4 bilingue | une impression fictive affichée et trouvée dans chaque langue EN/FR, provenance `example.invalid` | catalogue global, équivalence et disponibilité Live non prouvés |
| 5 deck | deux versions exactes60, comparaison, export via la CLI et réimport distinct | légalité et structure du deck principal `unknown` |
| 6 profil | cinq journaux fictifs ×deux imports = cinq combats, trois W/une L/une issue inconnue; revue et leçons, n=5, dénominateur décidé=4 | pas de causalité ni tendance démontrée, cartes observées ≠ collection |
| 7 conseil | `recommend deck` = `INSUFFICIENT_EVIDENCE`, date locale distincte de l'import UTC | collection/crédits inconnus, aucun tarif/achat |
| 8 liens | cinq candidats initialement sans lien; preview immuable, une attestation répétée sans duplication, révocation et zéro attribution active ensuite | aucune version jouée déduite automatiquement; déclaration fictive explicite seulement |
| 9 candidat | preview sans mutation; candidat60 distinct, export drafts dans la fixture puis réimport sous un autre ID; version jouée2 conservée | candidat `UNKNOWN_LEGALITY`, aucune légalité positive déduite de l'export |
| 10 légalité | un autre deck fictif résolu et un registre entièrement fabriqué produisent successivement `legal/not_legal/unknown`; expiration également `unknown` | aucune norme réelle, date de rotation réelle ou légalité mondiale affirmée |
| 11 coach | trois tours PNG/annotations fictifs; advice sans coup certifié, avertissements/inconnues, processus frais, quatre observations dont une révision, trois actives, contexte contradictoire refusé, fermeture | zéro pixel persisté dans la DB; aucune lecture OCR réelle ou qualification terrain |
| 12 mise à jour | daily/deep dry-run et octets DB inchangés; cadence Toronto/DST, install/status/uninstall dry-run | réseau et scheduler non contactés, fuseau OS non observé |
| 13 readiness | `NOT_RELEASE_READY` et portes restantes présentes | aucun gate terrain levé par fixture |
| 14 récupération | fixture historique7 existante, backup plan/create/verify; clone neuf7 et clone distinct migré13 via CLI publiques; cibles existantes refusées | SHA/FK/FTS/histoires/source immuables sur fixtures; aucune ACL/confidentialité/durabilité ou migration personnelle attestée |

Le mode `demo` retire son espace synthétique à la fin. La récupération est un
test séparé sous une fixture neuve, jamais un backup lancé par la démo.
Le JSON du parcours ne contient aucun chemin absolu. Les bruts DB/images/logs
et les artefacts de tests ne sont pas versionnés.

## Deux défauts concrets corrigés

1. **Isolation des exports CLI.** L'ancien routage isolait `test-runs` seulement.
   Une DB de démo sous `demo-runs` envoyait `deck export` et `candidate-export`
   vers le dossier général des decks. Deux échecs reproduits sur une **fausse
   racine** et son faux dossier personnel, jamais sur les vrais decks. Le routage
   reconnaît maintenant les deux espaces jetables; les tests prouvent sortie
   sous la fixture et sentinelle fictive intacte. La démo utilise enfin la CLI
   d'export plutôt qu'un appel direct contournant ce routage.
2. **Diagnostics visuels sans sélection SQLite.** Avant le branchement match,
   `main` appelait `_db_for`, même pour capabilities/preflight/benchmark-ocr,
   pouvant inspecter les métadonnées du chemin DB par défaut. Trois échecs
   reproduits avec un sélecteur interdit et une fausse racine. Ces diagnostics
   évitent maintenant ce sélecteur; trois régressions réussies sans fichier créé,
   moteur OCR exécuté ni accès au chemin personnel. Les commandes de données
   gardent leurs contrôles de chemin/reparse existants.

Aucun changement de schéma ni d'algorithme de légalité/conseil. Le parcours
réutilise les modules et fixtures existants et rend leurs raccords vérifiables.
Les seules lignes de matrice modifiées sont J1/J6 et I démo; aucune porte
PARTIAL/BLOCKED publique, vision, OS ou personnelle n'est promue DONE.

## Vérifications et diagnostics des tests

- `python -m pokemind preflight --json` : runtime prêt, FTS5, aucune DB personnelle.
- `python -m pokemind match preflight --json` après correctif :
  `OCR_ENGINE_NOT_INSTALLED`, `binary_executed=false`, réseau/installation=false;
  aucune base sélectionnée même pour ses métadonnées.
- `python -m pokemind demo --json` : répétition complète exécutée, **79 CLI**,
  `SYNTHETIC_REHEARSAL_PASSED`, `NOT_RELEASE_READY`.
- `python -m pytest -q tests/test_user_journey_e2e.py` : **9 passed** avant ajout
  des trois diagnostics DB-free; puis `-k database_free` : **3 passed**.
  **12 nouveaux cas** au total : 1 parcours, 5 sondes négatives, 1 récupération,
  2 exports isolés et 3 diagnostics sans DB.
- Quatre régressions dates Toronto hiver/été avant/après minuit, suite I
  et toutes les suites héritées conservées. Les imports UTC restent visibles;
  les requêtes collection/crédits respectent leur calendrier local.
- Suite complète finale `python -m pytest -q` : **542 passed/3 skipped**, zéro échec, 359,60s. Les trois skips locaux sont deux essais OCR réel absent/non attesté et un lien symbolique non permis sur ce Windows; aucune installation/élévation tentée.
- Première suite complète, avant collecte des trois diagnostics supplémentaires :
  **539 passed/3 skipped**, zéro échec; passe complète finale relancée pour inclure
  les douze nouveaux cas et le dernier correctif dans une même exécution.
- Compilation `python -m compileall -q src tests scripts`, hygiène
  `python scripts/check_repo_hygiene.py`, `git diff --check` : réussis localement;
  contrôle de staging incluant les nouveaux fichiers avant commit, aucun artefact privé préparé.
- Diagnostic de développement : le garde réseau initial bloquait aussi
  `gethostname`, utilisé pour les verrous/plateforme; le test fournit maintenant
  un hôte fictif, sans appel réseau. Un premier teardown Windows retenait une
  connexion SQLite de test : fermeture explicite ajoutée, scénario récupération
  et deux exports repassés (**3 passed**). Résidu synthétique de ce premier
  teardown laissé ignoré, sans inventaire/effacement global ni donnée privée.

Dans le parcours E2E, sockets/DNS sont refusés dans le parent et chaque CLI
enfant; SQLite et open/listdir/scandir sous `data/local` sont limités à la fixture,
et Popen/system/startfile refusés dans les enfants. Cinq sondes prouvent ces
refus sur des destinations inexistantes fictives. Ces gardes de tests ne sont
pas des hooks installés dans l'environnement utilisateur. Pas de moteur OCR,
de commande scheduler, de client Live ou de processus tiers exécuté par le parcours.

## Portes V1 et prochain geste

Budget privé exécuté : **zéro**. Aucun accès aux DB, backups, decks, logs, images
ou ACL réels, aucun clone/migration personnel, installation ou changement OS.
Seuls les échanges GitHub explicitement demandés (sync/CI/push) utilisent le réseau;
zéro GET fournisseur, aucun nouveau BULK/PUBLIC-COVERAGE.

Après audit ChatGPT : les cinq checkpoints terrain et leurs replis sont décrits
dans le guide opérateur. Ils requièrent des ordres distincts : sûreté du backup
moderne existant **sans nouvelle création**, résolution du blocage clone7 et
choix de clones neufs, import de vrais deck/logs et attestations, installation
puis essai OCR autorisés séparément, ouverture auditée du verrou scheduler puis
installation/essai/statut/désinstallation avec heures et base publique choisies.
Les lacunes de connaissances publiques, réimpressions/errata/Live, méta,
Trainer Hill et sécurité restent aussi à compléter, sans retrait de périmètre.

`STATE/RESULT/HANDOFF/NEXT_ACTION = AWAITING_AUDIT`, `execute_now=false`,
autorisation E2E consommée. **Aucun prochain lot exécutable. STOP ChatGPT.**
CI de livraison **PENDING_CI au moment de rédaction/publication** : contrôler après
push les deux jobs et leurs tests au **SHA contenant ce rapport**, pas seulement
la CI de départ. Les résultats finaux Actions attachés à ce SHA sont la preuve
durable; la CI ne certifie ni ce PC ni une opération personnelle.
