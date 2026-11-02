# Audit ChatGPT indépendant — PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001

Date : 2026-10-27 (Québec). Portée : **inspection indépendante du GitHub privé**, code et tests publiés, métadonnées Actions au SHA exact. Aucun accès au poste Windows, à la base personnelle ni aux secrets; aucun test exécuté par ChatGPT.

## Résultat

**VERIFIED_GITHUB_CODE_STRUCTURE_WITH_RESERVATIONS / CI_AWAITING_EVIDENCE / V1_NOT_RELEASE_READY.**

- Branche `work/pm-v1-lotj-final-readiness-windows`, HEAD livré `c5410add611e4f2c0fbb9e996f1de87677b4348d`, commit de code `f2b54582eccd1bcc244e1f302f074384347a8ec2`. Comparaison depuis `693750ce63cc81330c171537c0e75b8866b5c31e` : 3 commits avant le commit final documentaire; pas de divergence de cette base. Le dernier commit modifie seulement les cinq rapports d'orchestration.
- CI code [40451791236](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40451791236) et CI HEAD documentaire [40451884809](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40451884809) : **completed/failure**, deux jobs Windows/Ubuntu chacun **sans étapes**. Aucune exécution des tests CI à ces SHAs. L'explication « budget Actions » est documentée par Codex; la connexion d'audit confirme zéro étape, mais n'a pas pu relire les annotations de budget (API non exposée, logs des jobs introuvables). Ne pas confondre avec un échec de pytest.
- Code inspecté : `desktop/window.py` a une saisie commune et route localement import/slash/développement; `desktop/ingestion.py` sépare le journal d'une question et valide par le parseur; `assistant/sessions.py` conserve une conversation avec sous-sessions fournisseur/canal; `assistant/codex_app_server.py` expose des appels RPC et le pont de commandes; `assistant/provider.py` fournit Claude/Ollama; `desktop/services.py` borne les projections du rapport, candidats60 et annotations; `opponent_observer.py` étiquette la reconstruction hypothétique; `batch_public_research.py` conserve les observations PUBLIC, révisions et reçus dans l'index existant. Aucune preuve de second cerveau.
- Tests de régression dédiés réellement présents dans `tests/test_unified_assistant.py` et `tests/test_desktop_workflow_qt.py` (journal+question, reprise des sous-sessions, RPC, refus de chemins, mémoire hors ligne, hypothèses, annotations). **1393 réussis/3 ignorés, puis 102 ciblés et 31 Qt** : résultats *déclarés par l'exécuteur*, non rerun indépendamment. Idem pour vraies sessions Codex/Claude, fenêtre Windows, interruption, EXE rebuilt et collecte réseau publique.
- Aucun nouveau code final n'a été testé par Actions. Ancienne CI verte `40408811095` au SHA `2e28b33...` ne certifie pas cette version.

## Risque prioritaire à vérifier/corriger — frontière de confidentialité des outils de développement

Constat de code : `Store.DEFAULTS.project_relative='.'`. En demande de développement, `MainWindow.send_chat` autorise cette racine; `CodexAppServer` active `workspaceWrite` sur le répertoire projet, réseau autorisé et `approvalPolicy='never'`; Claude active des outils natifs de shell/fichiers. Les filtres `project_tool(read/write)` et les instructions du modèle ne contraignent **pas** un shell général, lequel peut potentiellement lire `data/local` et d'autres secrets accessibles au processus. La documentation le reconnaît. **Aucune exfiltration prouvée**, mais l'absence de lecture/transmission privée par le canal de développement n'est pas garantie techniquement. Le badge d'accès complet reste opt-in; cela ne suffit pas à isoler les lectures en mode standard. Évaluer une isolation effective ou une frontière explicitement vérifiable, sans retirer les actions de développement voulues.

## Portes restant ouvertes

1. Frontière effective confidentialité/shell en développement standard, tests négatifs y compris chemins absolus et commandes réellement exécutées.
2. CI complète Windows et Ubuntu aux nouveaux SHAs quand le service GitHub Actions peut lancer les jobs, marqueurs et empreintes vérifiés; ne pas contourner la limite ni attribuer les anciens succès.
3. Réception utilisateur sur vraies données/EXE sans publication privée; attention au schéma SQLite7 vs13, toujours non migré.
4. Autres portes V1 historiques (OCR terrain, récupération opérationnelle, installation planifiée) : non résolues par ce lot. Ollama non testé localement.

## Décision d'orchestration

Mandat A–G **audité statiquement avec réserves**, pas relancé. Prochaine tâche unique recommandée : `PM-V1-DEV-PRIVACY-BOUNDARY-001` (tests de frontière puis correctif minimal seulement si démontré), préparée dans `.orchestrator/NEXT_PROMPT.md`, **non autorisée / non lancée**. Statut V1 `NOT_RELEASE_READY`; aucune migration, sauvegarde, collecte personnelle, changement de facturation, fusion ni force-push. Ce rapport ne certifie ni la machine de l'utilisateur ni une preuve de sécurité absolue.
