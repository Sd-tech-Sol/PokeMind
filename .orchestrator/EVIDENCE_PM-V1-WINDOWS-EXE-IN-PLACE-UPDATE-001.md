# PM-V1-WINDOWS-EXE-IN-PLACE-UPDATE-001 — mise à jour locale du véritable EXE

2026-10-27 Québec. **REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT / execute_now=false / consumed=true.**
Constats Windows **CODEX_LOCAL_REPORTED**, aucune certification indépendante du PC.
**V1 NOT_RELEASE_READY; CI AWAITING_EVIDENCE; réception propriétaire non effectuée.**

## Autorisation, source et cible

- GO manuel explicite pour compiler et remplacer l'installation réelle, avec anciens binaires conservés et données intactes. Le propriétaire a ensuite confirmé explicitement que son EXE utilisé est **`dist/PokeMind/PokeMind.exe`**. Aucun autre emplacement recherché sur le PC, aucun raccourci externe inspecté ou modifié.
- Dépôt `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre. Fetch puis pull **fast-forward** de `537d1f7a8da26effaec28bb2527af6faed7b9d79` à **`b7c1d36607a51c4eb47980e4992f8eb0d03fd89b`**, sans reset, merge ou force-push.
- **SHA source compilé : `a232f17fc56e43722a50a12c5b527a3099db00db`**, correctif minimal du script de build et documentation, au-dessus du HEAD synchronisé. Aucun changement du moteur ou des données. Le commit de livraison documentaire qui contient cette preuve ne change pas les sources compilées.
- Racine du projet retrouvée par `Path(sys.executable).parents[2]` à cet emplacement et marqueur `.orchestrator/PROJECT_SPEC.md`. `Store`, `Services` et les chemins fixes conservent la même racine et le même `data/local`.

## Conservation des données

| Contrôle agrégé autorisé | Avant | Après |
|---|---:|---:|
| Matchs valides du rapport conservé utilisé par l'interface | 66 | 66 |
| Entrées de combats dans la DB historique identifiée | 5 | 5 |
| Version du schéma de cette DB | 7 | 7 |

Les 66 matchs sont dans le **rapport canonique conservé**, et ne sont pas présentés comme 66 lignes de la DB historique. Seuls le contrôle de sélection du rapport et sa projection `coverage.valid` ont été décodés, sans charger l'ensemble du rapport dans les services. La sonde initiale à expression régulière a refusé conservatoirement le bloc `coverage` imbriqué; une lecture bornée avec comptage des accolades a fourni le compteur. Ce contrôle n'est pas une revalidation complète du rapport.

SQLite ouvert seulement sur le chemin déterminé par l'installation, URI **`mode=ro&immutable=1`**, `query_only=ON`, sans WAL/SHM/journal observé. Requêtes limitées à `user_version` et compteurs de `battle_logs`; aucun contenu de partie, deck ou conversation sélectionné. Aucun `status/search` sur DB implicite.

Le relevé local des chemins relatifs, identités de fichiers/dossiers, tailles, dates de modification et modes sous `data/local` est **identique avant et après** les tests, le build et le déploiement. Il reste privé, hors Git; aucun hash du contenu personnel calculé ou publié. Cette comparaison de métadonnées ne constitue pas une preuve cryptographique de tous les octets personnels. Aucune opération de déploiement n'a ciblé ce dossier.

Inspection statique : `Services.load(update=False)` lit les rapports conservés; le prévol de la DB ancienne reste readonly et les chemins d'import bloquent le schéma incompatible plutôt que de migrer. Les préférences de démarrage existantes n'ont pas été consultées ou changées. **La vraie application n'a pas été lancée sur les données personnelles** : les effets ordinaires de l'ouverture et la réception restent à observer par le propriétaire. Aucun nouveau backup, clone, import, reset, migration, remplacement ou suppression de données personnelles.

## Compilation de production et vérifications

- Dépendances **déjà installées**, sans installation : Python **3.13.15**, PySide6 **6.12.0**, PyInstaller **6.22.3**, tzdata **2026.5**, pytest **9.1.1**. Prévol **RUNTIME_READY**, FTS5 disponible, DB personnelle non ouverte par le prévol, zéro écriture annoncée.
- `scripts/Build-PokeMindDesktop.ps1 -StagingRoot` accepte seulement un répertoire **neuf** de forme `build/exe-upgrade-<GUID32>`, refuse les redirections, sorties occupées et l'emploi simultané de `-SyntheticQaRoot`. Le build normal refuse aussi une distribution existante. Aucun déploiement implicite ajouté au script.
- Paramètres de production conservés : **`--onedir --windowed --name PokeMind --paths src`**, vrai `src/pokemind/desktop/app.py`, mêmes exclusions Qt et collecte des notices/licences. Travail, caches PyInstaller, temporaires et traces de ce build confinés aux nouveaux répertoires sous `build`. Le build n'a jamais ciblé l'installation occupée.
- Build **exit 0**, candidat complet de **788 fichiers**, plugin natif Windows, notices et licences présents. **Aucune option de build QA**, aucun `POKEMIND_DESKTOP_SMOKE=synthetic-release`, aucun hidden-import de harness QA.
- Archive frozen inspectée sans l'exécuter : point d'entrée et **56 modules PokeMind embarqués** identiques au code source compilé à ce SHA, après seule normalisation de `co_filename`. Modules `qa_offline_runtime`, `qa_offline_gui`, `qa_unified_desktop` absents de l'archive. Aucune réponse fictive ou doublure de fournisseur injectée dans le candidat déployé.

| Vérification locale dans ce mandat | Résultat |
|---|---|
| Tests Qt existants, fixtures synthétiques séparées | **62 réussis**, 0 échec/erreur/ignoré |
| Services, ingestion et identité publique, fixtures séparées | **61 réussis**, 0 échec/erreur/ignoré |
| Refus build normal sur distribution existante, staging hors destination, options contradictoires, staging déjà occupé | **4 refus attendus** |
| Analyse syntaxique PowerShell | Réussie |
| Contrôle du véritable portable compilé sur fixture indépendante | **exit 0**, Qt Windows natif |

**123 tests distincts** au total; les quatre contrôles PowerShell et le démarrage frozen sont des contrôles supplémentaires, pas des tests pytest ajoutés à ce total. Les suites utilisent le runner de tests synthétiques existant avec ses temporaires précoces et gardes. Son identifiant historique interne ne réactive pas un ancien mandat. Aucune nouvelle réception manuelle fictive demandée au propriétaire.

Le **même EXE de production ensuite déployé** a été lancé avec une racine de travail inventée indépendante, sans marqueur de projet dans son staging binaire; aucune copie de données personnelles utilisée. Seul le smoke de production existant **`POKEMIND_DESKTOP_SMOKE=1`** était actif dans ce processus enfant, pour fermeture et contrôles automatiques; aucun mode `synthetic-release` ni patch `qa_offline_runtime`. Préférences de fixture : cloud refusé, images, surveillance et actualisation automatique désactivées; garde hors ligne d'images activée. Aucun fournisseur ni collecte réelle demandé. Cela ne prétend pas mesurer exhaustivement les sockets Windows.

Contrôles vrais : frozen, fenêtre visible, plateforme `windows`, six pages, rapport chargé, référence de 60 cartes, galerie, import, activité et option démarrage présents. La DB **synthétique** schéma7 est restée identique octet pour octet. Capture de cette seule fixture inspectée localement : interface ordinaire, **aucun bandeau QA HORS LIGNE**; capture et traces hors Git. Aucun essai du chat réel ni nouveau GET de source. Le dernier code de sortie du processus est 0, sans processus tué.

## Déploiement réel et retour arrière

1. Avant déplacement : application fermée, aucun processus `PokeMind` observé; aucune mise à mort de processus. Racine, source, cible et destination de rollback vérifiées dans le dépôt et sans redirection. Inventaires des anciens binaires et du candidat recontrôlés.
2. Ancien dossier binaire : **788 fichiers**, aucun candidat de DB/JSON/log ou dossier personnel dans la distribution. **Dossier entier déplacé vers un nom local neuf sous `dist`**, jamais supprimé ni écrasé.
3. Distribution candidate complète déplacée vers **exactement `dist/PokeMind`**. Pas de remplacement de l'EXE seul. Aucun déplacement de `data/local`, aucune élévation ou modification Windows globale.
4. Après déploiement : tous les fichiers installés correspondent à l'inventaire du candidat, anciens binaires conservés intégralement avec leurs empreintes identiques. Compteurs et métadonnées personnelles inchangés. Racine habituelle préservée. Chemin direct confirmé par le propriétaire inchangé; aucun raccourci recréé ou retargeté.

**Rollback disponible, non exécuté** : fermer normalement l'application, conserver aussi le nouveau dossier sous un autre nom neuf, puis remettre l'ancien dossier à `dist/PokeMind`; aucune suppression ni restauration de DB nécessaire. Le nom exact et la procédure locale sont conservés dans la preuve privée. Aucun ancien dossier n'a été nettoyé. Aucun nouvel acte de rollback n'est lancé par ce rapport.

## GitHub, CI et limites de livraison

Seuls script, guide et rapports assainis sont publiés. `build`, `dist`, ancien binaire et preuve locale ignorés par Git; aucun EXE, DB, sauvegarde, manifeste privé, contenu personnel, empreinte personnelle, chemin absolu ou trace brute préparé pour commit.

Hygiène Git réussie : **523 fichiers suivis** après préparation explicite des huit documents de livraison, `git diff --cached --check` sans erreur et JSON/identifiant/statut/autorisation des documents courants cohérents. Archives conservées; aucune pièce privée préparée.

CI de départ au SHA synchronisé **`b7c1d36607a51c4eb47980e4992f8eb0d03fd89b`**, [run 40620693696](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40620693696) : **completed/failure**, jobs Windows et Ubuntu héritée **0 étape chacun**, HEAD de chaque job concordant. Aucun succès CI repris d'un ancien SHA. Aucun workflow, paiement ou rerun Actions modifié/déclenché manuellement.

Le HEAD distant et la CI **au SHA exact de la publication documentaire** doivent être relus après push, en lecture seule, sans boucle de commits contenant leur propre SHA; les runs GitHub liés au commit sont la trace durable de ce contrôle. **CI AWAITING_EVIDENCE**, aucune réussite présumée. Le statut de publication final est communiqué à la fin de l'exécution; toute CI non terminée demeure pending.

**STOP audit indépendant ChatGPT.** Livraison binaire rapportée localement complète; l'utilisateur ouvrira lui-même son EXE pour sa réception. Pas d'auto-VERIFIED ni de déclaration RELEASE_READY. Les portes distinctes sources réelles, sécurité Option B, OCR, migration contrôlée et réception propriétaire ne sont pas promues par cette mise à jour.
