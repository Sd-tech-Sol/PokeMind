# AUDIT CHATGPT — PM-V1-MEMORY-RECEIPT-CONSISTENCY-001

**2026-10-27 Québec — AUDITED_GITHUB_STATIC_HOST_RECEIPT_CORRECTED_RESEARCH_ANSWER_UX_REGRESSION_CI_PENDING.**
**V1 NOT_RELEASE_READY / CI AWAITING_EVIDENCE.**

## Portée et preuve du code

- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`. Base `696824fffb0cd9e416f01d9d6184f769ec5dd34d`, code livré `5a72a0d897e6707e9df66f8ccdbaff6b489eeea8`, HEAD documentaire audité `713237df2e9ba7b0f873e52bf84fd2b38a1173c4`. Comparaison GitHub : **2 commits / 16 fichiers**.
- Audit statique du diff et des fichiers `assistant/receipts.py`, `desktop/services.py`, `desktop/window.py`, `assistant/tools.py`, `qa_unified_desktop.py`, tests Qt/unité, RESULT, EVIDENCE, matrice V1. Aucun script, EXE, fournisseur, test Windows ni donnée personnelle exécuté/lu indépendamment par ChatGPT.
- `Services.prepare_question` conserve le reçu de recherche; le moteur expose `ERROR/persisted=None` si état non confirmé, et `tool_call(research)` réutilise le reçu pour éviter un second GET.
- `public_memory_record` et `public_memory_message` créent la réponse déterministe dans **le fil existant**, avec comptes du moteur, distinction nouvelle écriture/cache, non-vérification des sources, disponibilité offline et absence d'attestation de l'usage par le modèle.
- `MainWindow.chat_delta` ignore la prose du fournisseur dès qu'un reçu est présent; `chat_done` met le reçu et son rendu canonique dans le message conservé, puis réinitialise l'état. Le texte trompeur « rien n'a été mémorisé » n'est plus affiché à côté de « 2 faits ajoutés » dans ce flux.
- Tests ajoutés : contradiction artificielle `added=2` pour Codex/Claude, états SAVED/PARTIAL/cache/échec/interruption, texte rendu, sauvegardé et rouvert, vérification du viewport Qt; QA `memory_consistency_gate` rejette l'ancien déni suivi d'un compteur. Les tests positifs locaux sont **rapportés** : **1409 passés / 3 ignorés** hors Qt + **54 Qt Windows passés** = **1463 passés distincts / 3 ignorés**, 25 nouveaux. Portable fictif frozen=true/exit0, fenêtre peinte et reprise offline sans GET **CODEX_LOCAL_REPORTED seulement**.

## Nouvelle réserve fonctionnelle : réponse de recherche perdue

**RESEARCH_ANSWER_UX_REGRESSION — démontrable par le code.** La route `research_request` traite des demandes « cherche », « recherche », « internet », « web » ou « méta récente » comme des recherches. Lors de chacune, `prepare_question` enregistre `last_research_receipt` et `chat_delta` ignore alors **l'intégralité de l'analyse IA**, même si elle contient des faits, conseils ou réponses pertinents. `chat_done` la remplace par un résumé de stockage.

Ainsi, « Cherche les derniers changements des règles et explique leurs implications pour mon deck » peut n'obtenir que « 2 faits ajoutés, sources…, non vérifiés », sans explication des changements demandés. Le comportement a été **volontairement documenté** par Codex pour ne pas publier son récit de collecte faux/incomplet. Il règle le faux déni de mémoire mais laisse **incomplète** la finalité métier d'un chatbot qui cherche, mémorise puis **répond**.

Les tests actuels vérifient les reçus et l'absence de contradiction; aucun test n'impose la pertinence de la réponse sur les **faits demandés**. Le correctif ne doit pas revenir à un simple suffixe (le bug précédent) ni à un prompt seul. Il faut une réponse utile à partir des observations PUBLIC sourcées et de leurs limites, tout en gardant un reçu d'écriture strictement autoritaire. Pas de second cerveau.

## CI indépendante

- Code run [40505943526](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40505943526) au SHA `5a72a0d8` : `completed/failure`. Jobs Ubuntu **122195157900** et Windows **122195158297**, tous deux **steps=[]**, vérifiés.
- HEAD run [40506064562](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40506064562) au SHA `713237df2e9ba7b0f873e52bf84fd2b38a1173c4` : `completed/failure`. Jobs Ubuntu **122195562421** et Windows **122195562212**, tous deux **steps=[]**, vérifiés.
- **Aucun test CI exécuté.** Budget Actions = cause consignée par l'exécuteur, cohérente avec les jobs vides mais annotations budget **non relues indépendamment** dans ce tour.
- Tout nouveau commit documentaire d'audit porte un nouveau HEAD et un run distinct non validé à l'avance.

## Portes conservées et verdict

SQLite7 personnelle→13, réception terrain, OCR, restauration/backup, légalité Standard/Live et qualité des sources, planificateur, CI actuelle, et Ollama absent selon exécuteur restent ouverts. Option B : shell de développement non isolé avec consentement explicite, non une exclusion OS vérifiée.

**Verdict : AUDITED_GITHUB_STATIC_HOST_RECEIPT_CORRECTED_RESEARCH_ANSWER_UX_REGRESSION_CI_PENDING.** La tâche de cohérence des reçus est auditée **pour son code**; perte d'utilité de la réponse de recherche reste à corriger. Prochaine tâche unique `PM-V1-RESEARCH-ANSWER-USEFULNESS-001` **préparée, non autorisée** (`execute_now=false`). Aucune exécution privée ni agent lancé.
