# PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001 — preuves assainies

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / AWAITING_AUDIT**, aucune auto-attestation indépendante.
Résultat fonctionnel : **READY_FOR_OWNER_MANUAL_SYNTHETIC_TRIAL_ONLY**. Réception propriétaire non effectuée. **V1 NOT_RELEASE_READY; CI AWAITING_EVIDENCE; ISOLATION_UNRESOLVED_OPTION_B.**

## Autorisation, source et synchronisation

GO explicite du propriétaire pour le mandat complet, incluant corrections et relances techniques ordinaires sans audit intermédiaire. Les anciennes permissions réseau et les anciens STOP techniques n’ont pas été repris. Lecture du contrat complet, continuité V2/STATE/NEXT_ACTION, résultat/passation/décisions, audit EARLY-TEMP, trois preuves PARTIAL et documents de QA. Skill d’exécution : [github-executor](skills/github-executor/SKILL.md), avec la dérogation explicite du propriétaire pour les erreurs techniques de ce seul mandat.

Dépôt `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`. Arbre initial propre. Fetch puis pull **--ff-only**, de `55ff9e67c46fcb1882f5ed2ab62f0179af247798` à `c6c81eaa104ac7c7c1be6e2cbc49fa1bada8316d`. Aucun reset, rebase, merge main ou force. Les anciennes propositions sous build sont restées non qualifiées et conservées; elles n’ont pas été appliquées en bloc. Aucun ancien dossier supprimé.

## Code livré et frontières

- `src/pokemind/synthetic_qa.py` : allocation courte exclusive `build/qr-…`, marqueur de tâche/purpose/token, vérification canonique de la chaîne sans reparse/symlink/hardlink, refus des racines occupées. TEMP/TMP/TMPDIR et tempfile sont configurés **avant import pytest**. Aucun changement permanent Windows.
- `scripts/run_synthetic_qa.py` : suites nommées, capture FD réelle, log explicite, JUnit/cache/basetemp dans la seule allocation; compteurs setup/call/teardown indépendants de JUnit. Identité JUnit fictive via platform.node, sans lecture du nom du PC. Deux captures précèdent conftest. `local_tmp` utilise cette allocation; aucun repli implicite vers le répertoire privé. Sans opt-in, les mécanismes historiques restent inchangés.
- `tests/qa_synthetic_cli.py` : véritable parseur et formateurs humain/JSON/HTML en processus, sur la paire SQLite fictive readonly/immutable exactement admise. Commande et options limitées; découverte, DB implicite, écritures, réseau et processus interdits. Les deux variantes de parcours autrefois bloquées réussissent. L’ancien chemin subprocess/cp1252 est conservé sans opt-in mais **n’a pas été exécuté dans ce mandat**; les nouvelles passes utilisent UTF-8 en processus.
- Gardes Python : réseau/socket/HTTP et sous-processus refusés; DB/écritures uniquement dans la racine propre; vrai `data/local`, `dist`, secrets `.env*`, autres projets et lectures externes non admises refusés. Un alias de source sous le dépôt est aussi refusé. L’unlink d’un nom temporaire **dans sa propre allocation** peut retirer son entrée hardlink lors de la publication atomique, sans modifier le contenu lié; lecture/édition via hardlink et reparse restent refusées. Le test de cette séquence utilise réellement `overwrite=False`.
- `qa_unified_desktop.prepare_release` est réutilisé sous la nouvelle allocation; aucun accès à la base habituelle ou à l’EXE propriétaire. Tests opt-in conservant les seuls nouveaux artefacts; pas de nettoyage des anciens workspaces.
- `scripts/Start-PokeMind-Synthetic-Offline-QA.ps1`, `qa_offline_gui.py` et `qa_offline_runtime.py` : petit point d’entrée manuel distinct, fenêtre MainWindow/Store/Services existants, Fake existant des tests Qt et constructeur fictif existant. Processus au premier plan, pas d’installation/service/hook/scheduler. Chaque nouveau lancement alloue une copie neuve; réouverture explicite seulement d’un purpose GUI avec manifeste OFFLINE et marqueur de fixture valides. Chaîne des fichiers vérifiée avant Store/Services.
- **Avant toute fenêtre**, neutralisation des classes et alias Codex/Claude/Ollama réels, lancement d’outils, HTTP, images et ouverture du navigateur. Trois doublures distinctes préservent les branches de routage de la fenêtre. Développement, statut, compactage et reprise fournisseur refusés avant outil. Pièces jointes et sélecteurs natifs désactivés, collage fictif seulement. Les liens internes restent utiles. Bandeau, titre, libellés et réponses identifient la QA hors ligne.
- Les règles PUBLIC utilisent uniquement l’opener inventé déjà présent, avec robots et licence `synthetic_author_owned` **sur contenu inventé seulement**. Les URL sont des données de test, jamais des pages consultées. La méta sans cache reste vide/hors ligne et les collecteurs de matchups sont neutralisés. Les réponses/reçus proviennent des moteurs hôtes existants; les réponses du faux fournisseur sont fixes et explicitement signalées.

Ces vérifications instrumentent Python et les chemins de ce dispositif. **Elles ne constituent ni sandbox OS, ni trace système de tous les accès natifs possibles.** Les valeurs zéro décrivent les chemins instrumentés/exercés et l’absence d’appel réel observé; aucune isolation Windows générale n’est revendiquée. Les tests négatifs interrogent la politique ou les fonctions de blocage avant IO, sans ouvrir une vraie ressource personnelle ou externe.

## Erreurs et corrections dans le même GO

Les tentatives ci-dessous sont conservées localement, sans logs bruts publiés. Elles ne sont pas additionnées au total final distinct.

| Étape | Observation exacte et traitement |
|---|---|
| Premier canari, `qr-b00c7ae6` | Sortie F puis échec de sérialisation JUnit sur `platform.node → socket.gethostname`. L’ancien compteur affiche 0 faute de JUnit et le drapeau initial `security_incident=true` classe trop largement ce refus. **Ce 0 n’est pas un nombre fiable de tests appelés**; au moins un rapport d’échec apparaît. Aucun nom de machine retourné, aucune connexion. Diagnostic du code pytest : métadonnée locale, refus conservé et identité JUnit remplacée par une constante fictive. Ce faux classement historique n’est pas effacé des artefacts locaux. Les vrais accès personnels/connexions restent des incidents. |
| Canari suivant, `qr-11b99dad` | 1 échec : FileHandler n’est pas un gestionnaire de contexte. Correction try/finally/close. |
| Diagnostic logger | FileHandler(os.devnull, delay=True) expose localement la valeur exacte normalisée, sans ouvrir cette cible. Le chemin absolu n’est pas publié. Le logger pytest utilise désormais un fichier explicitement dans la racine QA; aucune exception générale sur NUL. |
| Ciblés, `qr-ae5e53f5` | 33 réussis, 1 erreur de setup : refus de l’unlink d’un nom temporaire propre pendant publication atomique, nlink=2. Cible précise confirmée synthétique. Correction limitée à l’unlink de cette entrée, test de régression atomique ajouté. Aucun accès personnel ou externe. |
| Canari et ciblés suivants | Canari 1/1 puis ciblés 36/36 et 37/37 réussis; compteurs d’appels sans JUnit ajoutés; deux tests de refus d’alias de code ensuite ajoutés et passés dans la consolidation finale. |
| Premier driver GUI, `qr-4f30a4ec` | IndexError après une interaction de test sans message envoyé, 0 appel fictif/extérieur. Le driver exerce désormais le signal du bouton Envoyer et la touche Enter plutôt qu’un clic de coordonnées non confirmé; les commandes métier restent inchangées. |
| Libellés GUI, `qr-270ca754` | Assertion du libellé fictif : attente plurielle incompatible avec une ancienne affectation de placeholder. Suppression de l’affectation concurrente; libellés QA appliqués au même point après traduction/préférences. |
| Revue des captures de `qr-36becfb5` | Assertions de données vertes, mais capture de reprise trop précoce montrant le tableau encore en chargement. Cause : l’attente pouvait finir avant le callback de démarrage différé. Le driver attend maintenant fin du startup, files de jobs vides, rapport chargé **et métrique visible égale au rapport**. Nouvelle réception complète sur une nouvelle allocation, sans masquer la capture antérieure. La finition du driver passe ensuite par QApplication.exec comme le lancement manuel, avec assertion de boucle active dans chaque processus. |

Aucun vrai incident d’accès personnel, connexion externe ou opération hors mandat observé. Les refus attendus de `/status` et des fonctions réelles sont des portes applicatives, pas des appels à un outil réel. Aucun test supprimé, skip/xfail ajouté, garde désactivé ou allowlist générale élargie.

## Tests finaux réellement exécutés

[JSON assaini](EVIDENCE_PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001.json) : compteurs des rapports pytest, compteurs JUnit et assertions natives. Vérification de l’unicité des couples classname/name dans les deux JUnit : **302/302 distincts**.

| Groupe | Exécutés/réussis distincts |
|---|---:|
| Canari bootstrap/capture/log/fixture | 1 |
| Nouveaux contrôles ciblés de sécurité/CLI/compteurs | 37 |
| Intégration historique : release, parcours, profondeur, recherche | 68 |
| Qt Windows historique : desktop + workflow | 62 |
| Services, ingestion, identité/règles publiques | 61 |
| Nouvelles portes négatives du lanceur, avant fenêtre | 19 |
| Module complet de vues CLI modifié | 54 |
| **Total : 245 existants + 57 nouveaux** | **302** |

Passes de référence :

```powershell
.venv-desktop/Scripts/python.exe -B scripts/run_synthetic_qa.py --suite all
.venv-desktop/Scripts/python.exe -B scripts/run_synthetic_qa.py --suite cli
```

- `all`, `build/qr-04b1821e` : **248 passed, 82.35 s**, exit0, 248 appels, 0 échec/erreur/ignoré. 199 allocations de fixture; 2 captures avant conftest, 3 temporaires enregistrés au total.
- `cli`, `build/qr-8673ee39` : **54 passed, 5.24 s**, exit0, 54 appels, 0 échec/erreur/ignoré. 39 allocations, 2 captures avant conftest.
- Après finition des libellés/exemples GUI, portes du lanceur rejouées : `build/qr-a232bda2`, **19 passed, 0.87 s**, exit0, déjà comptées dans 248.
- Les passes isolées précédentes core 68/40.12 s, Qt 62/38.36 s, wider 61/5.81 s et gates 19/0.84 s ont également réussi; **ne pas les additionner**.
- Toutes les passes finales : 0 refus d’audit, security_incident=false, JUnit concordant. Les deux variantes CLI historiques sont dans les 68 et ne sont pas recomptées.

La suite entière historique du cerveau n’a pas été exécutée ici. Aucun test Linux local, EXE, vrai fournisseur, protocole subprocess cp1252, données personnelles, sauvegarde, migration, OCR, tâche Windows ou collecte réelle. Actions doit rester une preuve distincte au SHA exact.

## Réception native du lanceur final

Allocation finale `build/qr-8d5efef8`, entièrement créée dans ce mandat. Commandes réellement utilisées :

```powershell
.\scripts\Start-PokeMind-Synthetic-Offline-QA.ps1 -Exercise first
.\scripts\Start-PokeMind-Synthetic-Offline-QA.ps1 -Workspace 'build/qr-8d5efef8' -Exercise resume
```

Ces options sont un driver de **réception technique**, pas la décision du propriétaire. [Guide manuel](../docs/RECEPTION_UTILISATEUR_V1_SYNTHETIQUE_WINDOWS.md) : lancement normal sans Exercise, chemin généré dynamiquement puis commande de réouverture imprimée.

Premier processus : **32 assertions vraies, exit0**, Qt platform=windows, boucle native QApplication.exec réellement active (loopLevel > 0), six pages/une saisie; bandeau et libellés; bouton Envoyer et Enter; réponse fixe fictive; deck60 collé/sauvegardé dans la discussion et validateur réel de 60 cartes; journal+question traités par les moteurs, n=2; doublon sans hausse; journal incomplet refusé; variantes60 sourcées restant hypothèses; consentement réel Non par défaut, brouillon/historique conservés; `/status` bloqué avant outil/inférence; liens externes et pièces jointes refusés avant lecture; synthèse/reçu hôte concordants rendus/sauvegardés; deux observations inventées non vérifiées avec application courante/Live/réimpression unknown; méta manquante sans collecte; base legacy fictive inchangée; fermeture complète. **6 réponses fixes locales, 3 réponses de source inventée** (robots + deux pages), **1 commande réelle neutralisée**, 0 source GET réel/0 fournisseur réel.

Deuxième processus, même script, même boucle native et même allocation explicite : **21 assertions vraies, exit0**, même ID de discussion et tous messages identiques, sentinelle visible, n=2 visible après chargement, deux faits récupérés, aucun ajout/mise à jour du cache, **0 appel de doublure, 0 réponse de source inventée et 0 GET réel**. Base fictive inchangée, fermeture complète. Deux captures de **la seule fenêtre fictive** inspectées visuellement après cette correction d’attente; elles demeurent ignorées localement, hors GitHub.

Les marqueurs, tokens, bases, dialogues complets, logs bruts, captures, manifestes locaux et empreintes de données ne sont pas publiés. Le JSON contient uniquement compteurs/assertions et chemins relatifs des nouvelles allocations fictives. Aucun accès à l’EXE propriétaire, même pour le hacher. Rien ne certifie une réception effectuée par le propriétaire.

## Publication et CI

Publication code/guide/preuves : [`0be909d1`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/0be909d11968bd1e4a4587c689b741d42e71e951), HEAD distant concordant et arbre propre après push. CI exacte [run 40613114259](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40613114259) : completed/failure, **0 étape Windows, 0 étape Ubuntu**, SHA de chaque job concordant et annotation budget confirmée pour les deux. Aucun rerun, paiement ou workflow modifié; CI **AWAITING_EVIDENCE**. Hygiène Git OK (521 fichiers suivis), syntaxe/JSON et diff préparé vérifiés, 25 fichiers qualifiés seulement. Ce complément est documentaire; son HEAD et sa CI seront contrôlés en lecture seule après push, sans boucle de commits cherchant à contenir leur propre SHA. L’auditeur doit relire Actions au HEAD final exact.

Code/tests/lanceur/guide qualifiés et orchestration cohérente, sans changement de workflow Actions. Aucune relance Actions ni manipulation de budget/paiement. La CI peut rester bloquée sans invalider l’existence des tests locaux, mais ne doit jamais être annoncée verte par équivalence.

**STOP de livraison unique pour audit indépendant ChatGPT.** L’autorisation est consommée, execute_now=false; aucun nouveau mandat ni essai propriétaire automatique. Les autres portes V1 et le risque Option B restent ouverts.
