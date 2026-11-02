# AUDIT INDÉPENDANT ChatGPT — PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001

**2026-10-27 Québec. Verdict : AUDITED_STATIC_SYNTHETIC_QA_IMPLEMENTED_OWNER_MANUAL_TRIAL_READY_CI_PENDING.**
**Produit : V1 NOT_RELEASE_READY. CI : AWAITING_EVIDENCE. Réception du propriétaire : NOT_PERFORMED.**

## GitHub / SHA audités

Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`. Baseline `c6c81eaa104ac7c7c1be6e2cbc49fa1bada8316d`, code commit `0be909d11968bd1e4a4587c689b741d42e71e951`, HEAD complet `35280016c25a6d45afae6177c510a63d3a0b890d`. Comparaison vérifiée sur GitHub : **2 commits, 25 fichiers ajoutés ou modifiés, ahead=2, behind=0**; inclut code, tests, script PowerShell, guide, preuves et état. Pas de modification de workflow GitHub Actions dans la liste de diff. Aucun merge `main` ni force-push effectué par ChatGPT.

Sources réellement inspectées via le connecteur GitHub :
- `src/pokemind/synthetic_qa.py` (nouveau), `scripts/run_synthetic_qa.py`, `scripts/Start-PokeMind-Synthetic-Offline-QA.ps1`, `scripts/qa_offline_gui.py`, `scripts/qa_offline_runtime.py`, `scripts/qa_offline_reception.py`, `scripts/qa_unified_desktop.py`.
- `tests/conftest.py`, `tests/qa_recovery_canary.py`, `tests/qa_recovery_targeted.py`, `tests/qa_offline_gate.py`, `tests/qa_synthetic_cli.py`, `tests/test_public_evidence_explain_cli.py`, `tests/test_synthetic_release_preflight.py`.
- `docs/RECEPTION_UTILISATEUR_V1_SYNTHETIQUE_WINDOWS.md`, `.orchestrator/EVIDENCE_PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001.md`, le JSON assaini de même nom, `STATE.json`, RESULT et mandat courant.

## Implémentation confirmée par lecture du code

1. **Lanceur distinct :** `scripts/Start-PokeMind-Synthetic-Offline-QA.ps1` exige le venv Qt existant et appelle `scripts/qa_offline_gui.py` au premier plan. Il ne télécharge rien, n'installe pas de paquet et ne pointe pas vers l'EXE propriétaire. Sans `-Workspace`, nouveau workspace; avec un `-Workspace` relatif `build/qr-XXXXXXXX` explicitement contrôlé, réouverture de la copie. La validation de marqueur et de purpose `gui` se trouve dans le module Python.
2. **QA de chemin/fixtures :** `synthetic_qa.bootstrap` impose un répertoire neuf marqué sous `build/qr-…`, configuration `TEMP`/`TMP`/`TMPDIR` et `tempfile` avant chargement de pytest, puis audit Python; `tests/conftest.py` réutilise l'allocation uniquement sous opt-in de la session. Le comportement historique du test hors opt-in demeure. Des vérifications lexicales, de chemin canonique et de liens matériels/reparse existent; ce n'est pas une sandbox OS.
3. **CLI test réellement évaluée :** `tests/qa_synthetic_cli.py` appelle le vrai parseur/les formateurs dans le processus, restreint le choix d'opération et les bases à la paire PUBLIC fictive, interdit les enfants arbitraires et les écritures; les deux anciens tests bloqués utilisent cette voie sous opt-in.
4. **Fenêtre existante :** `qa_offline_runtime.Runtime` enveloppe `MainWindow`, `Store`, `Services` existants; applique avant création de la fenêtre des remplacements locaux Codex/Claude/Ollama, les points d'entrée HTTP connus, l'ouverture navigateur, images et pièces jointes. Un bandeau visible **« QA HORS LIGNE — DONNÉES FICTIVES »** identifie l'environnement. Les interactions de développement sont bloquées. Les pages existantes et le chat unique sont conservés.
5. **Persistance et réception codifiées :** `qa_offline_reception.py` vérifie ouverture réelle Qt native, six pages, questions/deck60/log fictifs, déduplication, refus des données incomplètes, reçu PUBLIC issu du moteur hôte, consentement refusé, aucune recherche méta inventée, fermeture et réouverture de la même conversation. Les sources Pokémon/Limitless y sont des URL de fixtures et réponses inventées, pas une qualification de leurs vrais sites.

## Qualification des preuves locales — ne pas surpromouvoir

Le JSON assaini de Codex donne :
- **248 tests** dans la suite `all` et **54** dans la suite `cli`, classes/identités JUnit sans recouvrement selon l'exécuteur, soit **302 réussites distinctes** et 0 échec/erreur/ignoré *rapportés*. La somme de répartition des classes du JSON est cohérente avec 302. Les 19 tests du lanceur sont déjà inclus dans 248 : ne pas les additionner.
- **32 contrôles GUI premier processus** et **21 contrôles GUI deuxième processus** (même workspace), exit0 et boucle `QApplication.exec` native Windows rapportés. `qa_offline_reception.py` contient les portes correspondantes.
- Une série d'erreurs initiales de logger/capture/guard, de signal Envoyer et d'attente GUI a été corrigée au sein du mandat conformément au GO d'itération. Les passes finales restent distinctes de ces tentatives initiales.
- Les captures d'écran, JUnit et ledgers bruts sont **locaux hors GitHub**. ChatGPT n'a pas exécuté ces tests, démarré Windows/PySide6, observé la fenêtre, lu les fichiers locaux ni accédé à l'EXE propriétaire. **`CODEX_LOCAL_REPORTED`, pas `INDEPENDENT_RUNTIME_VERIFIED`.**

### Limites de sécurité et de produit

- `Context.summary()` expose `real_source_gets:0` et `real_provider_calls:0` comme **valeurs déclarées du contexte**, et non comme compteurs OS indépendants des sockets natifs. Le code dispose d'audit hooks et de doublures vérifiés statiquement, mais **ne prouve pas l'absence absolue de trafic réseau, d'accès natif ou de lecture hors espace**. Les affirmations « aucun accès personnel » / « EXE inchangé » restent des déclarations de Codex sur l'exécution.
- La politique Python refuse les espaces sensibles connus (`data/local`, `dist`, `.env*`), mais ce n'est pas une politique OS couvrant exhaustivement tout fichier privé éventuel dans le dépôt. L'utilisateur ne doit coller **que les exemples inventés**.
- Ce mode utilise des **réponses fixes de doublures**, pas une intelligence artificielle ou ses quotas réels. Il teste l'interface, des mécanismes de moteur local sur fixtures et les reçus, **pas** les règles Pokémon réelles, la méta, la légalité Standard/Live, la disponibilité des cartes ou la qualité d'un conseil de jeu.
- L'application normale et l'EXE propriétaire ne sont **pas** validés par cette réception. CI, source réelle, sauvegarde/restauration, migration propriétaire, OCR, scheduler, Ollama et Option B restent des portes distinctes. `ISOLATION_UNRESOLVED_OPTION_B` inchangé.

## GitHub Actions exactes

- [Code 40613114259](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40613114259) au SHA `0be909d11968bd1e4a4587c689b741d42e71e951` : `completed/failure`; Windows job 122569190231 et Ubuntu 122569189883, **steps=[]**.
- [HEAD final 40613283155](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40613283155) au SHA `35280016c25a6d45afae6177c510a63d3a0b890d` : `completed/failure`; Windows 122569759284 et Ubuntu 122569758964, **steps=[]**, vérifiés indépendamment via connecteur.
- Explication « budget Actions » rapportée par Codex. Les annotations de facturation ne sont pas revérifiées indépendamment dans ce cycle. **Aucun test CI n'a démarré**, donc ne pas réutiliser un ancien succès à la place.
- Un commit documentaire d'audit créera un nouveau SHA; contrôler sa propre CI sans prétendre succès.

## Verdict et seule suite

**AUDITED_STATIC_SYNTHETIC_QA_IMPLEMENTED_OWNER_MANUAL_TRIAL_READY_CI_PENDING** : le code et la structure de tests répondent aux objectifs de réception synthétique; la documentation locale est cohérente. Pas de bloquant de code confirmé par cet audit statique pour **un essai volontaire limité aux données fictives**. Cela ne constitue pas une certification de sécurité OS ou une validation de V1.

**Prochaine étape : réception manuelle du propriétaire uniquement**, **proposée et non lancée**. Aucune nouvelle tâche Codex, collecte, sauvegarde, migration ou nouvelle permission réseau nécessaire pour le simple essai fictif. L'utilisateur pourra ouvrir PowerShell à la racine du dépôt synchronisé, exécuter `.\scripts\Start-PokeMind-Synthetic-Offline-QA.ps1`, conserver la commande de reprise imprimée, essayer les scénarios du guide **sans données réelles**, fermer et signaler les écarts de façon assainie. Si la politique Windows refuse le fichier PS1, **ne pas contourner la GPO** : utiliser le point d'entrée Python existant `.\.venv-desktop\Scripts\python.exe -B .\scripts\qa_offline_gui.py`, sans `--exercise`, ou signaler le blocage; vérifier l'environnement avant de procéder. Une réception propriétaire positive est une preuve manuelle distincte, pas une promesse automatique. `execute_now=false`; V1 NOT_RELEASE_READY.
