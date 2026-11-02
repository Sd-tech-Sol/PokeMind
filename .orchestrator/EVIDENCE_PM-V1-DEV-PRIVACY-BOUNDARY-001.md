# PM-V1-DEV-PRIVACY-BOUNDARY-001 — preuves assainies

**Publication contrôlée :** code livré `b0c1c70d6b1c8cf6fae884597b0a836ff7a5fb41`, HEAD distant égal au local et worktree propre après le premier push. [CI40488964933](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40488964933) à ce SHA exact : completed/failure, **0 étape Windows et 0 étape Ubuntu**; annotations des deux jobs relues, budget Actions empêchant le démarrage. Aucun test CI exécuté. Porte **AWAITING_EVIDENCE**; aucune relance. Le complément présent ne modifie que les rapports; son HEAD/CI doivent aussi être contrôlés après push, sans succès présumé.

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / AWAITING_AUDIT / ISOLATION_UNRESOLVED / V1 NOT_RELEASE_READY.**

## Autorisation et portée

Ordre manuel du propriétaire : synchroniser la branche `work/pm-v1-lotj-final-readiness-windows` en fast-forward puis exécuter NEXT_PROMPT et publier les preuves. Synchronisation propre de `c5410add611e4f2c0fbb9e996f1de87677b4348d` vers `bb007cbe373007b48efe955f6308b4becbd2bdc0`. Le prompt préparé a été lancé par cet ordre; le mandat A–G n'a pas été repris. Les états ont été enregistrés IN_PROGRESS avant les essais.

Code et corpus entièrement inventés; aucun fichier personnel ouvert pour ces essais. Aucun accès à la vraie SQLite, aux sauvegardes, journaux, préférences ou conversations du propriétaire. Aucun backup/clone/migration/effacement personnel, changement global, WSL, scheduler, facturation ou interaction avec le jeu. Les essais créent leurs propres workspaces ignorés; le nettoyage normal des fixtures ne concerne que leurs fichiers inventés. Les workspaces du diagnostic manuel sont conservés localement, hors Git.

## Options officielles examinées

- [Codex App Server](https://learn.chatgpt.com/docs/app-server) : `command/exec` exécute réellement sous la politique du serveur, sans inférence ni thread; `workspaceWrite.readOnlyAccess` permet des racines de lecture restreintes. Une racine writable contenant des données privées ne les exclut pas automatiquement.
- [Profils Codex](https://learn.chatgpt.com/docs/permissions) : règles de chemins `read/write/deny` et profils minimaux existent. Cela offre une piste Codex à qualifier, pas une frontière commune déjà prouvée pour les deux fournisseurs.
- [Windows Codex](https://learn.chatgpt.com/docs/windows/windows-sandbox) : MXC/elevated et unelevated diffèrent; unelevated ne prend pas en charge les chemins de lecture interdits, et les globs ont une limite temporelle. Aucun setup privilégié ni changement de configuration globale effectué.
- [Sandbox Claude Code](https://code.claude.com/docs/en/sandboxing) : les commandes sur Windows natif ne sont pas sandboxées; les règles des outils de fichiers et la sandbox shell sont des mécanismes distincts. WSL2/VM ou isolation externe changeraient le périmètre de déploiement.

Conclusion de portée : aucune barrière commune Windows qualifiée dans ce lot. Une simple copie de code sans données ne suffit pas : chemins absolus et alias restent accessibles au shell. Le repli prévu explicitement par NEXT_PROMPT est appliqué : limite visible, consentement éclairé et STOP sur la garantie d'isolation non résolue. Ce n'est pas une preuve d'impossibilité de toute solution future.

## Diagnostic réel Windows, uniquement sur fichiers fictifs

Harness reproductible : `scripts/probe_dev_privacy_boundary.py`, lancement manuel seulement. Python projet 3.13.15; Codex CLI 0.163.0; Claude Code 2.1.311. Aucun watcher ni lancement par pytest/CI.

Le harness crée `data/local/private.txt` **dans son propre workspace inventé**, un hardlink `alias.txt`, un script enfant et un fichier de code public. Il exerce les politiques natives déjà utilisées par l'application. Le texte système Claude du diagnostic autorise expressément le canari inventé : l'obéissance du modèle à une interdiction textuelle n'est pas testée comme une barrière OS.

| Fournisseur / mode | Lecture relative | Absolue | Hardlink | Sous-processus | Modification privée fictive | Alias PowerShell `gc` | Édition, test Python, Git diff |
|---|---|---|---|---|---|---|---|
| Codex standard | oui | oui | oui | oui | oui | oui | oui |
| Codex full | oui | oui | oui | oui | oui | oui | oui |
| Claude standard | oui | oui | oui | oui | oui | oui | oui |
| Claude full | oui | oui | oui | oui | oui | oui | oui |

Quatre sorties de processus `0`; les deux tours Claude terminent sans erreur et exposent effectivement le JSON du sous-processus dans un `tool_result`. Les règles natives Claude `Read/Edit/Write(./data/**)` demeurent présentes : elles ne suffisent pas pour Bash. Codex utilise le vrai `command/exec`; son résultat est retourné au pont frontend sans appel de modèle pendant cette sonde. Aucun envoi de données personnelles testé ou autorisé. Les marqueurs inventés et booléens sont les seuls contenus nécessaires au diagnostic cloud Claude. Aucun brut de session, identifiant fournisseur ni chemin absolu publié.

Ces résultats **réfutent l'exclusion effective des données privées par le mode standard actuel**. Ils ne démontrent aucune exfiltration passée de données du propriétaire. Aucune variante de sandbox prétendument sûre n'a été substituée sans qualification.

## Changements livrés et contrôles de refus

- Libellés standard et badge permanent corrigés dès l'ouverture; portée de lecture/modification et sortie cloud expliquées dans Réglages et avant développement.
- Confirmation avec Non par défaut, enregistrée par version de notice/fournisseur/projet canonique/mode. Cloud ordinaire ou ancien full n'acceptent pas cette nouvelle portée. Révocation disponible; changement de portée exige un choix distinct.
- Avant acceptation, refus réel du routage UI : brouillon, chronologie et sous-session conservés; aucun appel au fournisseur. Si l'enregistrement échoue, développement arrêté. `ProviderAdapter.configure` refuse un appel de développement sans acceptation explicite. C'est un contrôle applicatif de consentement, **pas une sandbox**.
- Les demandes de développement ne chargent plus le rapport personnel du coach. Questions Pokémon, imports avec question, slash et canaux distincts conservent leurs moteurs; une instruction importée ne peut pas demander le consentement ni activer les outils. Aucune deuxième conversation.
- Les shells, outils d'édition/tests/Git et modes natifs sont conservés après consentement; aucune garantie d'absence de lecture/transmission privée après cette acceptation. Les historiques cloud antérieurs ne sont ni inspectés ni effacés.

## Tests et limites des preuves

| Contrôle local | Résultat |
|---|---|
| `preflight --json` | RUNTIME_READY; owner_database_opened=false, writes_to_disk=0 |
| `demo --json` | SYNTHETIC_REHEARSAL_PASSED; 79 processus CLI, aucun réseau/donnée propriétaire |
| Ciblés `test_unified_assistant.py` + `test_assistant_providers.py` | 33 passed |
| Suite complète hors deux modules Qt | **1401 passed / 3 skipped**, 585,89 s |
| Deux modules Qt avec plateforme **windows native**, services inventés | **34 passed**, dernière suite après modifications finales |
| Compilation, tabnanny, hygiène et diff | contrôlés avant publication; aucune donnée privée préparée |

Ignorés Windows : deux attestations OCR absentes et création de symlink non permise; le hardlink du diagnostic a fonctionné. La suite conserve ces limites et ne certifie ni OCR ni récupération réelle. Les tests UI acceptation/refus/erreur d'enregistrement/reprise/révocation sont fictifs; ils ne constituent pas une acceptation du risque par le propriétaire pour ses propres données. Aucun consentement personnel existant modifié. Aucun portable EXE reconstruit par ce mandat ciblé; preuves UI limitées au code source sous Python/Qt Windows. Toutes les observations PC sont rapportées par l'exécuteur, pas indépendamment vérifiées par ChatGPT.

## CI et arrêt

Au point de départ `bb007cbe373007b48efe955f6308b4becbd2bdc0`, [run 40452976427](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40452976427) : completed/failure, **zéro étape dans les deux jobs Windows/Ubuntu**. Annotation API relue : budget Actions empêchant le démarrage. Aucun test CI exécuté et aucun ancien vert substitué. CI de publication à contrôler au SHA exact après push; porte **AWAITING_EVIDENCE**, sans rerun ni modification de facturation.

STOP exécuteur après publication et contrôle du HEAD distant/CI exacts. Audit indépendant ChatGPT du diff, du consentement et des limites seulement; **aucun lancement privé, aucune isolation certifiée, V1 NOT_RELEASE_READY**.
