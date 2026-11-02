# AUDIT INDÉPENDANT CHATGPT — PM-V1-SYNTHETIC-RELEASE-PREFLIGHT-001

**2026-10-27 Québec — AUDITED_GITHUB_STATIC_SYNTHETIC_PREFLIGHT_DELIVERED_RESPONSE_RESERVATION_CI_PENDING.**
**Release : NOT_RELEASE_READY.** Prévol de logiciel fictif vérifié par code; exécution réelle Windows/EXE/CLI = **CODEX_LOCAL_REPORTED**, non rejouée indépendamment. Ce rapport ne déclare aucun fournisseur ou contenu réel vérifié.

## Portée GitHub et commits

- Dépôt `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`; code livré `2c9966d14868b9ef294d0cac1ec2d3328d5f9e7f`, HEAD documentaire audité `69072aaadf8651006a808f57b5df1ae50b19a843`, base `911a50b4192816c9ec4e9694b7800a1dd209d6ef`.
- GitHub compare : **2 commits, 15 chemins modifiés/ajoutés**. Diff inspecté, ainsi que `scripts/qa_unified_desktop.py`, `scripts/Build-PokeMindDesktop.ps1`, `scripts/desktop_licenses.py`, `src/pokemind/desktop/app.py`, `tests/test_synthetic_release_preflight.py`, `src/pokemind/desktop/window.py`, `src/pokemind/desktop/services.py`, `src/pokemind/batch_public_research.py`, `.orchestrator/RESULT.md`, preuves et `docs/SYNTHETIC_RELEASE_PREFLIGHT.md`.
- Aucune donnée privée ouverte par cet audit; aucun build ni test personnel, migration SQLite, CI rerun, édition du code ou facturation réalisés par ChatGPT.

## Validations statiques positives et leurs limites

1. Le script PowerShell offre un paramètre `-SyntheticQaRoot`, vérifie que le dossier est sous `build/synthetic-release-[32hex]`, refuse divers points de redirection et une sortie `dist` déjà présente, et déplace les sorties PyInstaller et licences dans le dossier de QA. **Le comportement du portable propriétaire non remplacé est rapporté par Codex**, non attesté par GitHub seul.
2. `desktop/app.py` n'active le mode `synthetic-release` que sur variable d'environnement explicite, vérifie la forme du chemin et le marqueur exact avant d'instancier `MainWindow`, et importe le harness embarqué seulement dans ce mode. Les protections sont des contrôles applicatifs pour la QA, pas une séparation de privilèges ni une sandbox.
3. Le harness `qa_unified_desktop.py` prépare une fixture totalement inventée, appelle les constructeurs métier existants, intercepte la recherche publique dans le scénario pour employer un transport inventé et rend la collecte de pairings indisponible. Il prévoit une vraie fenêtre native, un fil visible, Codex/Claude, `/status`, journal+question, hypothèse60, essai éditeur/test, consentement B, mémoire/reprise hors ligne et SQLite7 fictive non modifiée. Son résultat d'exécution et les captures locales ne sont pas vérifiables indépendamment via GitHub.
4. Nouveaux tests `test_synthetic_release_preflight.py` portent sur la validation du marqueur et d'alias, refus de racine ordinaire, puis persistance/lecture offline sur réponses inventées. Aucun test ajouté ne vérifie la **cohérence du texte généré et du reçu canonique**.
5. Tests **rapportés**, non relancés : `1404 passed / 3 skipped` hors Qt + `34 Qt Windows passed` = **1438 tests distincts passés / 3 ignorés**. Aucun ajout en double des ciblés. Ollama absent selon rapport exécuteur.
6. Sources publiques du harness et règles légales sont **inventées et non vérifiées** : les marqueurs `validation=unverified`, `legality=unknown` restent correctement conservés. Aucune affirmation sur la méta Pokémon actuelle par ces tests.

## Défaut bloquant : texte de réponse faux malgré la mémorisation

**RESPONSE_CONSISTENCY_UNRESOLVED.** L'exécuteur rapporte qu'au tour « Recherche les règles ... et mémorise les sources comme non vérifiées », le modèle a dit qu'aucune mémorisation n'avait eu lieu alors que les reçus indiquaient **deux observations non vérifiées ajoutées**, visibles dans la chronologie et relues hors ligne. Les sorties originales ne sont pas partagées, la cause exacte du choix de mots du modèle reste indéterminée.

Le code permet effectivement la contradiction :
- `Services.prepare_question` (`services.py`) exécute la recherche et enregistre `last_research_receipt`, puis passe `public_research` au contexte envoyé au modèle.
- `MainWindow.chat_done` (`window.py`) **ajoute en suffixe** une phrase canonique « Mémoire publique : X faits ajoutés… » au texte déjà généré, sans détecter ni traiter un déni de mémorisation.
- Le test Qt existant `test_successful_persistence_receipt_is_visible_as_soon_as_the_answer_finishes` certifie seulement que le compteur est visible, pas que le texte n'est pas contradictoire.
- Le harness frozen valide `public_receipt_persisted_not_normative` si des faits existent et si « faits ajoutés » apparaît dans la transcription; **la réponse peut démentir ce reçu et le scénario rester vert**.

Ainsi, le stockage local et la relecture offline sont compatibles avec les preuves rapportées; **la qualité conversationnelle n'est pas reçue**. Ne pas confondre faits **non vérifiés sur le plan normatif** et **non enregistrés**. Ni prompting supplémentaire ni reclassification des faits ne constituent par eux-mêmes un correctif déterministe fiable.

## CI et autres portes

- Run de code [40499211164](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40499211164) au SHA `2c9966d1` : `completed/failure`; jobs Ubuntu et Windows observés sans étapes dans la liste.
- Run final [40499348109](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40499348109) au SHA `69072aaadf8651006a808f57b5df1ae50b19a843` : `completed/failure` et **`steps=[]` vérifié par l'auditeur** sur jobs Ubuntu **122172810178** et Windows **122172810348**. Zéro test CI.
- Budget GitHub Actions comme cause : annoncé dans les preuves exécuteur et cohérent avec jobs vides, mais **annotations non lues indépendamment par ChatGPT** dans ce cycle.
- Restent ouverts : SQLite7 personnelle→13, OCR terrain, restauration/rétention, preuves de légalité/Live, réception sur données choisies par l'utilisateur, planificateur Windows, Ollama local absent, CI complète. Le choix B maintient explicitement la confidentialité shell `ISOLATION_UNRESOLVED_OPTION_B` comme risque reconnu, non une protection démontrée.

## Verdict et suite

**AUDITED_GITHUB_STATIC_SYNTHETIC_PREFLIGHT_DELIVERED_RESPONSE_RESERVATION_CI_PENDING**. Le code de packaging/QA et sa portée sont vérifiés **statiquement**; le lancement EXE, la suite Windows et la sécurité effective restent seulement rapportés. **Le parcours « recherche et mémorise » est à corriger** avant d'accepter l'expérience utilisateur. **V1 NOT_RELEASE_READY; CI AWAITING_EVIDENCE.**

Le prochain mandat unique proposé `PM-V1-MEMORY-RECEIPT-CONSISTENCY-001` cible la cohérence entre réponse et reçu hôte, avec tests de contre-exemple et un prévol synthétique corrigé. Il est **préparé, non autorisé** (`execute_now=false`). Aucun agent lancé, aucune permission personnelle déduite de ce rapport; aucune action sur main, aucun force-push, aucune facturation ou CI rerun.
