# Audit indépendant — PM-V1-OWNER-SELECTED-MATCH-REVIEW-UX-001

**23 octobre 2026. Verdict : `VERIFIED_GITHUB_CODE_CI_SYNTHETIC_SCOPE_ONLY`. V1 `NOT_RELEASE_READY`.**

## Contrôles GitHub
- Branche `work/pm-v1-lotj-final-readiness-windows`. Comparaison base [57bf4f9](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/57bf4f9d16c1bdcf97fe3a22596e5d8e0d9619db) à livraison [81c82d4](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/81c82d4ec42954e10a2603f6a2c317ca7d984de1) : **1 commit / 17 fichiers**, code, CLI, tests, docs, preuves et orchestration.
- Arbre Git complet **423 entrées**, `truncated=false`. Sous `data/local/`, uniquement `.gitkeep`; aucun journal, SQLite ni média privé suivi. Cela ne certifie pas les accès locaux de Codex sur Windows.
- [CI livraison 40000981581](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40000981581) : `completed/success` au **même SHA**. Windows job `120576660685` : **1051 passed / 2 skipped** (OCR non attesté); Ubuntu job `120576661070` : **1050 passed / 3 skipped** (mêmes 2 OCR + test Windows-junction).
- **Neuf marqueurs** présents dans chacun des deux logs : `selected_match_review_evidence`, `counter_learning_evidence`, `deck_library_matchup_evidence`, `deck_knowledge_evidence`, `public_deck_preflight_evidence`, `competitive_advisor_evidence`, `competitive_pages_evidence`, `rules_registry_evidence`, `ci_evidence`; SHA et run corrects.
- Empreintes SHA-256 canoniques JSON **identiques sur Windows et Ubuntu** pour les deux registres : `6039ba349a5dcb3a0af605fb2b2834108a0c5c58b1fb5e1b610ea22cf996b7ba`, `330790df14d7d5474503d04b31c29c36eddd1ba8b003736271ab82704f55e3d7`. Les empreintes d'octets bruts LF/CRLF demeurent différentes; cause historique reproduite **selon Codex**, sans mutation des registres ni nouvelle validation normative.

## Revue code/tests
- `selected_match_review.py` exige DB/deck/date, exactement un log ou battle ID, autorisation lecture et choix explicite dry-run ou apply **avant accès fichier**. Import et attestation demandent des consentements séparés, impossibles en une même commande. Aucun deck version attesté par simple import.
- Validation bornée du fichier choisi (local `data/local`, types/2Mo, liens/redirections/sidecars, contrôle de poignée et métadonnées), DB schéma existant, aucune découverte ni migration. **Non certifié face à tout processus hostile concurrent et toutes courses locales**.
- Réutilisation des moteurs battle_logs, Observer/Analytics, attestations, Deck Knowledge, Counter-Deck et Learning Loop. Cartes visibles vs proxy PUBLIC; W/L/unknown, version inconnue, petits n, date de partie distincte; 60 cartes à copier manuellement; pas de jeu/presse-papiers.
- Tests `test_owner_selected_match_review.py` examinés et exécutés par CI : simulation 5→6 matchs inventés, panne après commit, import idempotent, version v2 puis retrait motivé/correction v1, Learning Loop JSON explicite sans overwrite, rejets avant I/O, fichiers malformés, chemins, liens, doublons, conflits et inconnues. Propriété CI `SYNTHETIC_OWNER_SELECTED_MATCH_REVIEW_ONLY` avec 3 consentements, 4 exports60 et `real_personal_records_opened=false` : simulation, **non preuve d'absence d'accès privé sur PC**.

## Limites et verdict
**Accepté pour code/CI/fixtures uniquement, sans bloqueur manifeste dans cette portée.** Codex rapporte localement 1049 passed/3 skipped, 112 ciblés, 0 GET, aucun vrai cache privé ouvert : `CODEX_LOCAL_REPORTED`, non audité indépendamment depuis GitHub. Aucune vraie partie, légalité Live ou données propriétaire validées. Sous D-196, prochain mandat PUBLIC borné, 0GET et départ manuel permis; consentements privés toujours interdits. V1 `NOT_RELEASE_READY`.
