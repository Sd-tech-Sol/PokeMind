# VERIFICATION_PM-0006C — audit indépendant ChatGPT (2026-10-12, Québec)

## Verdict
**PM-0006C ACCEPTÉE EN REVUE STATIQUE INDÉPENDANTE POUR SA PORTÉE** : création d'un outil d'attestation propriétaire individuelle, datée et révocable entre un combat et une version de deck, sans appliquer de lien à la véritable base utilisateur durant la livraison. Cela ne signifie **ni tests locaux indépendants par ChatGPT**, ni vérification matérielle de la base privée, ni certification que les déclarations du propriétaire sont exactes. Aucun défaut bloquant neuf identifié dans la portée de PM-0006C.

## Sources effectivement contrôlées
- Repo GitHub privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0006c-manual-link-attestations`.
- Parent préparation `c6c2e9eab4ae70c3df3999bda6aa67921493a726` ; commit Codex **`8876d6c73b7df0cb075ddc39a80c6ad0d36592b4`**. Compare : **1 commit d'avance, 0 de retard, 21 fichiers changés** (code, documentation et adaptations de tests).
- Code `src/pokemind/attestations.py` (542 lignes), `database.py` schéma 8, `version_evidence.py`, `analysis.py`, CLI et `tests/test_attestations.py` (~525 lignes) lus directement, ainsi que `RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md` et `docs/PM-0006C_MANUAL_ATTESTATIONS.md`.
- Arbre Git complet **136 entrées, truncated=false**, aucun fichier SQLite privé, deck réel, journal personnel, sauvegarde, capture, token ni données `data/local` privé dans les chemins suivis. Absence de contenu sensible **dans les chemins** ne garantit pas un examen de chaque octet de toute l'histoire Git.
- GitHub `get_commit_combined_status` retourne `statuses:[]` ; `fetch_commit_workflow_runs` retourne `workflow_runs:[]`. **203 tests réussis au prévol / 216 à la fin** (compileall, diff check, intégrité SQLite/FTS5, rollback, données locales inchangées) sont **déclarés par Codex**, pas exécutés indépendamment par ChatGPT.

## Schéma et migrations : conforme à la portée
- Schéma SQLite **7 → 8 additif**, nouvelle `battle_version_attestations` conservant `battle_id`, `deck_version_id`, provenance **`owner_asserted`**, `confirmed_at` UTC et `revoked_at`, motif normalisé et date de partie éventuellement déclarée. Aucun glissement des champs existants `battle_deck_versions.effective_from/approved_at`.
- Index unique partiel `battle_version_attestations_one_active` sur `battle_id WHERE status='active'`; FK et contraintes de statut de révocation.
- `initialize_schema` sauvegarde une base versionnée avec `sqlite3.backup()` avant migration, puis `_migrate_attestation_schema` crée la table/index dans une transaction. Les tests synthétiques contrôlent backup/restauration v7, FTS5, quatre documents, cinq combats, catalogue/règles/méta et rollback de migration simulé. Attention : toute migration réelle reste dépendante du test local rapporté par Codex, non d'un test matériel externe.

## Confirmation, révocation et confidentialité : conformes
- `link-battle` fait **prévisualisation en SQLite `mode=ro` par défaut** (aucune migration ni write), `--apply` sans `--confirm-owner` est refusé, aucun mode `--all`. Chaque paire est revérifiée sous `BEGIN IMMEDIATE`; combat existant/valide même deck, version exacte/total 60 et somme 60, refus des liens legacy/conflicts. La confirmation insère `battle_deck_versions` plus la nouvelle attestation dans la **même transaction**, avec horodatage UTC **au moment de la confirmation**.
- Confirmation identique idempotente; tenter de changer de version sans révoquer refuse. `unlink-battle` ne révoque que l'attestation active de ce mécanisme, met `revoked_at`, **garde le journal**, supprime seulement le lien associé et refuse un lien legacy non attesté. Race/rollback testés en base synthétique.
- `link-candidates` renvoie IDs locaux, date d'import, issue et statut, **pas de hash, pseudo, carte ni journal**. Exceptions SQLite des nouvelles commandes neutralisées au niveau CLI; pas d'accès à un compte, HTTP, surveillance du jeu, scheduler ou export vers Git.
- `version_evidence` et `analyze deck` différencient `owner_asserted`, lien legacy, révocation et attestation pas encore disponible à `as_of`, sans attribuer une partie à une version avant le jour de `confirmed_at`. Les tests incluent une attestation après le combat, puis diagnostic avant/après confirmation et après révocation.

## Limites non bloquantes à préserver dans la suite
- Une attestation `owner_asserted` est une **déclaration humaine**, pas une preuve indépendante de la version réellement jouée; avec une date d'import du journal plutôt que date réelle du match, les analyses doivent afficher la provenance et leurs incertitudes.
- La granularité des diagnostics historiques est `YYYY-MM-DD` : confirmation/révocation le même jour peuvent paraître globalisées dans une même date, limitation indiquée dans la documentation. Une analyse à l'heure près nécessiterait une API temporelle différente, pas autorisée ici.
- Au prochain lot de fiabilisation, vérifier que `PRAGMA user_version=8` et les migrations partielles anciennes restent récupérables; ne pas transformer par défaut une prévisualisation en migration. Les liens legacy ne doivent jamais être « confirmés propriétaire » par migration.
- Le CLI global des autres commandes possède encore certains retours `str(exc)` : future revue sécurité générale nécessaire; les nouvelles commandes traitent les exceptions SQLite dans leur branche.
- Codex déclare que **les cinq vrais combats demeurent non liés et non modifiés**; le repo ne permet pas de l'attester directement. Aucune commande `--apply` réelle n'a été demandée à l'utilisateur par ChatGPT.

## Étape suivante et changement de méthode expressément demandé
La demande récente de l'utilisateur est de **garder TOUT le périmètre PokeMind V1, agrandir les tâches et donner davantage d'autonomie à Codex**, sans microaudits entre sous-tâches. Politique déjà préparée séparément sur `orchestration/pm-v1-autonomy-batches` :
- `.orchestrator/AUTONOMY_POLICY.md`;
- `.orchestrator/V1_BATCH_PLAN.md`.

**Ne pas merger cette branche** ni réécrire PM-0006C déjà livrée. Préparer sur une **nouvelle branche issue de cet audit** la politique et le **LOT A complet** (TCGdex/versions/texte/variantes FR-EN, règles officielles datées/structure/réimpressions, Limitless, mesures de couverture) avec plusieurs sous-tâches, commits et corrections gérées par Codex **jusqu'à l'audit de fin de lot**. Maintenir ensuite lots B (collection/recommandations/apprentissage), C (coach visuel), D (mises à jour publiques quotidien + mardi/vendredi sur opt-in installation), E (sauvegardes/smoke tests/stabilisation). Aucune fonction V1 n'est abandonnée.
