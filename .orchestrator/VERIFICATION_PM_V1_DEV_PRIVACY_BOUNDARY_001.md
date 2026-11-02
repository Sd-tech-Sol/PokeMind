# AUDIT CHATGPT — PM-V1-DEV-PRIVACY-BOUNDARY-001

**2026-10-27 Québec — AUDITED_GITHUB_STATIC_CONSENT_DELIVERED_ISOLATION_UNRESOLVED_CI_PENDING.**

## Portée et ancrage

- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`.
- HEAD documentaire audité : `bae728b2e19e5e42f71724f3121701a70abec660`. Commit de code : `b0c1c70d6b1c8cf6fae884597b0a836ff7a5fb41`; base de comparaison `bb007cbe373007b48efe955f6308b4becbd2bdc0`.
- GitHub compare : **ahead 2 / behind 0, 14 fichiers**. Aucun merge main inspecté ou opéré, aucune donnée utilisateur consultée.
- Lecture indépendante des patches source `src/pokemind/desktop/window.py`, `src/pokemind/assistant/provider.py`, `src/pokemind/assistant/sessions.py`, `src/pokemind/assistant/codex_app_server.py`, tests, harness `scripts/probe_dev_privacy_boundary.py`, STATE, RESULT et preuves publiées.
- Limite : audit **statique GitHub**, pas exécution indépendante sur Windows ni nouveau test du runtime cloud.

## Vérifications positives — code, pas certification de sécurité OS

1. Le libellé « projet protégé » a disparu. Badge `STANDARD · shell : données privées accessibles` et notice détaillée dès l'ouverture.
2. `window.py:send_chat` appelle `acknowledge_development_privacy()` avant `get_adapter()`, `store.switch()` et envoi fournisseur pour les requêtes classées développement. Boîte Oui/Non, **Non par défaut**; refus garde brouillon et historique.
3. Acceptation mémorisée sous une clé `shell-privacy-v1` par fournisseur, chemin de projet **relatif au dépôt** et mode; les anciennes permissions cloud/full ne sont pas réutilisées. Révocation visible et refus si écriture des préférences échoue.
4. `ProviderAdapter.configure(development=True)` exige le paramètre explicite `privacy_acknowledged=True`. Cela protège ce chemin applicatif, **pas** des commandes directement lancées hors application.
5. Le canal développement ne charge plus automatiquement le rapport personnel coach. Tests nouveaux couvrent refus, acceptation, révocation, défaut d'enregistrement et impossibilité pour un import de demander les outils de développement.
6. Le harness manuel emploie un workspace et un canari **inventés**; ses quatre sorties Windows Codex/Claude × standard/full sont **rapportées par l'exécuteur**, non rejouées par ChatGPT. Le code de sonde rend plausible la méthode de mesure, sans prouver de contrôle global de tous chemins/OS.

## Bloqueur de confidentialité

**ISOLATION_UNRESOLVED.** Le mode standard est un mode de développement réel, et non un bac à sable exclusif de `data/local`. `codex_app_server.py` transmet `command/exec` avec `workspaceWrite`, `writableRoots=[cwd]` et `networkAccess=True`, et démarre les threads avec `workspace-write`. Le projet par défaut `project_relative='.'` inclut `data/local`; ce répertoire n'est pas exclu des shells par les filtres des outils de fichiers. Claude Code autorise Bash natif en développement; les règles `Read/Edit/Write(./data/**)` ne sont pas une isolation des commandes Bash. Les chemins absolus et alias sont une autre limite.

Le consentement constitue une **atténuation de transparence et d'autorisation**, pas une preuve que le shell ne lira/modifiera/transmettra jamais les données privées. Aucune exfiltration personnelle constatée, mais absence de test d'exfiltration ne vaut pas protection garantie.

Le prochain choix de produit doit être explicite : **(A)** exiger et qualifier une véritable frontière d'exécution au niveau OS, sans accès au corpus privé, avant d'affirmer « données privées protégées »; ou **(B)** accepter que l'assistant de développement opère avec les droits du compte après avertissement, et maintenir le risque documenté sans présenter le mode standard comme isolé. Ne pas choisir l'un des deux à la place du propriétaire; aucune configuration Windows globale, conteneur, WSL, VM, migration ou nouvelle exécution autorisés par ce rapport.

## Tests et CI

- Tests locaux déclarés dans `EVIDENCE_PM-V1-DEV-PRIVACY-BOUNDARY-001.md` : **1401 réussis, 3 ignorés** hors Qt; **34 Qt Windows réussis**; **33 ciblés réussis**. Statut probatoire : **CODEX_LOCAL_REPORTED**, pas test relancé par l'auditeur.
- GitHub Actions **run 40488964933**, SHA code `b0c1c70d6b1c8cf6fae884597b0a836ff7a5fb41` : `completed/failure`; aucune étape observée dans les deux jobs selon preuve exécuteur.
- GitHub Actions **run 40489091291**, SHA documentaire audité `bae728b2e19e5e42f71724f3121701a70abec660` : `completed/failure`; **steps=[]** confirmé séparément par l'auditeur pour jobs **122138199126** (Ubuntu) et **122138199393** (Windows). Aucun test CI exécuté.
- « Budget Actions » : explication documentée par l'exécuteur, cohérente avec l'absence de steps. Les annotations budget n'ont **pas** été relues indépendamment par ChatGPT à cet audit; ne pas prétendre le contraire.
- Aucun EXE portable reconstruit dans ce lot; aucune qualification indépendante de la machine réelle, de la base personnelle, de l'OCR, des récupérations, ni des portes V1 restantes.
- Un éventuel commit documentaire de cet audit aura son **propre SHA/CI non encore certifiés**; ne pas lui attribuer les tests précédents.

## Verdict et suite

**AUDITED_GITHUB_STATIC_CONSENT_DELIVERED_ISOLATION_UNRESOLVED_CI_PENDING. V1 NOT_RELEASE_READY.**

La tâche est **auditée** pour présence des changements et des preuves disponibles, **non acceptée comme correction de l'isolation**; CI reste `AWAITING_EVIDENCE`. Prochain jalon : **HOLD_OWNER_DECISION** sur l'architecture d'isolation et restauration de la capacité CI, sans nouvelle tâche d'exécution préparée ou déclenchée, sans relance automatique, et sans avancer une release. Conserver `.orchestrator/NEXT_PROMPT.md` en STOP.
