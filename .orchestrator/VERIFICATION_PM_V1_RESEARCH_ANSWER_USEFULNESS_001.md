# AUDIT INDÉPENDANT CHATGPT — PM-V1-RESEARCH-ANSWER-USEFULNESS-001

**2026-10-27 Québec — AUDITED_GITHUB_STATIC_SYNTHETIC_PASS_SOURCE_DEPTH_PENDING_CI_PENDING.**
**V1 NOT_RELEASE_READY / CI AWAITING_EVIDENCE.** Aucune certification du poste Windows ni du corpus privé.

## Révisions et provenance

- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`; départ `70d3033741d2ea5957082fafbcef5dd262946d2d`. Code livré `6a478c45cea8ffc584ed73773a1a1124e3597f10`; HEAD audité `cb593d3b3d1ee70c7577b7de969ecff63450f40c`.
- Comparaison GitHub : **2 commits, 14 fichiers modifiés/ajoutés, ahead=2, behind=0**.
- Audit direct du correctif dans `src/pokemind/assistant/receipts.py`, `desktop/window.py`, `batch_public_research.py`, `public_campaign.py`, tests `test_research_answers.py`, `test_desktop_workflow_qt.py`, `test_synthetic_release_preflight.py`, harness `qa_unified_desktop.py`, preuve et matrice V1.
- Aucun accès du présent auditeur à la base personnelle, aux journaux, captures privées, EXE utilisateur, poste Windows ou fournisseurs réels. Aucun test exécuté par ChatGPT; résultats de Windows/CLI/pytest uniquement **CODEX_LOCAL_REPORTED**.

## Validation de la livraison

1. `public_research_answer(receipt, question)` construit une explication **déterministe** de champs publics typés reconnus (`official_document`, répertoires/archétypes, `deck60`, carte), après filtres URL, horodatage et forme du hash/version. Les observations affichent URL, date de consultation, version et validation `unverified` ou `schema_validated_observation`. Les champs libres inconnus sont exclus.
2. `public_research_message` conserve une explication relative au sujet **avant** le reçu canonique de stockage; même contenu rendu et sauvegardé dans le fil existant via `MainWindow.chat_done`. Le modèle ne décide ni des faits ni du résultat d'écriture. L'ancien déni par modèle reste écarté du message visible.
3. Un cache ou l'offline ne se transforme pas en nouvel enregistrement : logique `public_memory_message` antérieure préservée. Les outils `Services` existants réutilisent le reçu du tour, sans deuxième collecte automatique.
4. Les tests nouveaux vérifient un cas contradictoire et quatre scénarios règles/méta pour Codex/Claude, absence d'affirmations de légalité ou winrate inventés, provenance/date/version, affichage/sauvegarde, réouverture, cache et offline. Le harness possède deux portes distinctes : `memory_response_consistency` et `research_answer_usefulness`; il rejette une réponse composée uniquement du reçu.
5. Codex rapporte `1426 passed / 3 skipped` (cerveau), `58 passed / 0 skipped` (Qt Windows), **1484 réussis distincts / 3 ignorés**, 21 tests nouveaux, et un portable QA dédié `frozen=true, native_windows=true, exit0`. Captures et binaires restent locaux, non inspectés par ChatGPT. Aucune comparaison réelle de sources externes faite durant ce lot.

## Réserve de portée : qualité du contenu réellement disponible

Le lot élimine la régression « reçu seul », **mais ne prouve pas qu'il peut répondre aux changements des règles ou aux tendances récentes avec le contenu métier attendu**. `batch_public_research.refresh_public` stocke actuellement pour les documents officiels une observation `official_document` fondée sur métadonnées, **pas le texte normatif des règles**. Un répertoire d'archétypes prouve seulement la présence de noms, **pas des taux, une série temporelle, ni une causalité**. La nouvelle synthèse le dit correctement : elle n'invente ni règle, ni rotation certifiée, ni tendance quantitative, ni légalité Standard/Live.

Donc **PASS_STATIC_DESIGN / PASS_LOCAL_SYNTHETIC_REPORTED** pour l'association synthèse+reçu dans une conversation, mais **SOURCE_DEPTH_UNRESOLVED** et **REAL_WORLD_EVIDENCE_PENDING**. Ne pas promouvoir un test de fixture « réponse utile » à une attestation que les informations officielles actuelles ou les recommandations de deck sont exactes. Un retour utile minimal peut être une limite honnête; cela ne suffit pas à toutes les questions de l'utilisateur.

Le parseur est volontairement borné par des URLs officielles et politiques `robots.txt`, anti-contournement, limites de volume et droits de rétention. Toute augmentation de profondeur exige de préserver ces contraintes, de vérifier licences et provenance, et de séparer un essai synthétique de nouveaux appels Internet réels.

## CI aux deux SHAs exacts

- [CI du code 40510511061](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40510511061), SHA `6a478c45cea8ffc584ed73773a1a1124e3597f10` : `completed/failure`, jobs Windows `122210855344` et Ubuntu `122210855814`, chacun **steps=[]**, vérifié.
- [CI du HEAD livré 40510642088](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40510642088), SHA `cb593d3b3d1ee70c7577b7de969ecff63450f40c` : `completed/failure`, jobs Windows `122211324117` et Ubuntu `122211324861`, chacun **steps=[]**, vérifié.
- **Aucun test CI exécuté**. Cause « budget GitHub Actions » consignée dans les preuves Codex; annotations non relues indépendamment par ChatGPT durant ce cycle. Aucun rerun/facturation et aucune CI verte héritée.
- Un nouveau commit documentaire d'audit a son propre SHA/run éventuel, non présumé vert.

## Verdict / prochaine étape

**AUDITED_GITHUB_STATIC_SYNTHETIC_PASS_SOURCE_DEPTH_PENDING_CI_PENDING** : code de réponse source+reçu livré et vérifié statiquement, prévol local Windows/pytest **rapporté**, aucune erreur bloquante supplémentaire confirmée dans le périmètre livré. Réserve **SOURCE_DEPTH_UNRESOLVED**. V1 **NOT_RELEASE_READY**; portes ouvertes : CI actuelle, vérification des sources réelles et légalité, données personnelles legacy7→13 (sans migration), OCR, sauvegarde/restauration, scheduler, Ollama local et réception propriétaire. Option B = shells non isolés avec consentement, pas une frontière OS.

Un nouveau mandat unique `PM-V1-PUBLIC-SOURCE-DEPTH-001` est **préparé mais non lancé**. Objectif : enrichissement vérifiable des faits PUBLIC existants depuis des documents de règles et des preuves temporelles autorisées, tests synthétiques d'abord, aucune lecture privée et aucun GET réel supplémentaire par ce simple audit. Les autorisations futures restent explicites.
