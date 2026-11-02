# Matrice d’acceptation — LOT E et fonctions V1 A–E

Date de preuve Codex : 2026-10-13. Cette matrice décrit l’exécution locale; elle
n’est pas un audit indépendant et n’emploie pas `VERIFIED`. Statut global :
`NOT_RELEASE_READY`.

| Fonction V1 | État | Preuve/test et chemin | Dernière preuve | Travail restant / action suivante | Priorité post-E |
|---|---|---|---|---|---|
| Bibliothèque 4 volumes + FTS5 + citations | `DONE` | `knowledge_status`, `test_import_search.py`, E2E SQLite FTS5 | 2026-10-13 | Revalider les règles changeantes à leur source | P2 continu |
| Catalogue TCGdex FR/EN, index/détails/reprise/quotas | `PARTIAL_WITH_EVIDENCE` | `cards.py`, `test_cards.py`, `knowledge audit`; base personnelle observée partielle sans migration | 2026-10-13 | Continuer les scans bornés jusqu’aux fins de scopes; total fournisseur demeure inconnu | P1 LOT F |
| Identités, variantes, réimpressions, promos/errata | `PARTIAL_WITH_EVIDENCE` | résolution déterministe et tri-state testés; zéro registre exhaustif démontré | 2026-10-13 | Charger seulement des équivalences officielles datées, mesurer exceptions | P1 LOT F |
| Règles officielles et légalité Standard/Expanded/Live | `PARTIAL_WITH_EVIDENCE` | `rules.py`, `test_rules.py`; verdict conservateur et structure testés | 2026-10-13 | Compléter restrictions/promos/errata/réimpressions et compatibilité Live prouvée | P1 LOT F |
| Limitless descriptif/contextualisé | `PARTIAL_WITH_EVIDENCE` | `meta.py`, `test_meta.py`; budgets/404/rate-limit/offline testés | 2026-10-13 | Accumuler des snapshots fiables; mapping archétypes/matchups incomplet | P2 LOT F |
| Trainer Hill | `BLOCKED_WITH_REASON` | `knowledge audit`: aucune API publique/condition d’automatisation autorisée vérifiée | 2026-10-13 | Obtenir documentation/permission primaire; aucun scraping de remplacement | P2 externe |
| Import/export deck exact 60 et versions immuables | `DONE` pour le mécanisme | `test_decks.py`, `test_deck_exports.py`, validation terrain historique documentée | 2026-10-13 | Toute nouvelle version réelle reste une action propriétaire | P3 propriétaire |
| Collection/crédits volontaires, datés, révocables | `DONE` pour le mécanisme; `BLOCKED_WITH_REASON` pour données réelles | `collection.py`, `test_collection.py`; aucune vraie donnée appliquée | 2026-10-13 | Import local volontaire; tarif officiel de fabrication toujours inconnu | P3 propriétaire/source |
| Conseils, comparaisons, candidats et export | `PARTIAL_WITH_EVIDENCE` | `test_recommendations.py`, `test_candidates.py`, `test_lot_b_e2e.py` | 2026-10-13 | Étendre preuves de textes/règles/méta/collection avant conseils précis | P2 LOT F |
| Journaux, profil, leçons et attestations révocables | `DONE` pour le mécanisme; `PARTIAL_WITH_EVIDENCE` pour attribution réelle | tests battle/profile/attestations/version; n réel non réécrit | 2026-10-13 | Cinq combats historiques restent sans attestation de version volontaire | P3 propriétaire |
| Image privée éphémère, limites, symlinks, mémoire textuelle | `DONE` | `visual_coach.py`, `test_visual_coach.py`; aucun pixel/chemin stocké | 2026-10-13 | Maintenir tests multiplateformes; symlink Windows dépend du privilège système | P2 continu |
| Reconnaissance locale réelle de capture | `PARTIAL_WITH_EVIDENCE` | `match capabilities`; aucun Pillow/OpenCV/OCR/ONNX disponible, aucun adaptateur calibré | 2026-10-13 | Consentir installation facultative, calibrer synthétique, puis essai réel autorisé | **P0 LOT F** |
| Conseil tour par tour conditionnel et mémoire multi-tours | `PARTIAL_WITH_EVIDENCE` | annotation manuelle + énergie typée + contexte; `test_visual_coach.py` | 2026-10-13 | Reconnaissance réelle et couverture des effets/règles avant `verified_possible` | **P0 LOT F** |
| Updater daily/deep/auto public, offline/reprise/alertes | `DONE` pour le mécanisme; données `PARTIAL_WITH_EVIDENCE` | E0 `test_updates.py`: compte GET effectif, date Toronto/dédup/rattrapage | 2026-10-13 | Exécuter futures fenêtres publiques avec budget choisi; données restent partielles | P1 LOT F |
| Scheduler Windows dry-run | `DONE` pour préparation | timezone `Eastern Standard Time` exigée; `-DeepTime` transmis; manifests testés | 2026-10-13 | Audit + consentement spécifique avant toute activation; verrou dur maintenu | P3 propriétaire |
| Scheduler Windows réellement actif | `BLOCKED_WITH_REASON` | `SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D`; aucune installation LOT E | 2026-10-13 | Opt-in séparé, revue du code d’activation, install/status/uninstall réels | P3 propriétaire |
| Backup SQLite cohérent et vérifié | `DONE` pour le mécanisme | `recovery.py`, `test_recovery.py`: sqlite3.backup, checksum, intégrité/FK/FTS5 | 2026-10-13 | Choix réel d’un dossier/support privé et première exécution propriétaire | P1 propriétaire |
| Restore plan/verify/apply atomique | `DONE` pour le mécanisme | clone ancien schéma 7→12, quarantaine, rollback publication, backup source préservé | 2026-10-13 | Toute restauration/migration réelle exige une action distincte | P1 propriétaire |
| Rétention/disque/concurrence/crash | `DONE` pour le mécanisme | preview hashée, espace/taille/durée, PID vivant, états failed/in_progress/verified/unknown | 2026-10-13 | Définir politique réelle; aucune purge réelle LOT E | P2 propriétaire |
| Caviardage erreurs et hygiène privée Git | `DONE` | `security.py`, `test_security.py`, `check_repo_hygiene.py` | 2026-10-13 | Audit indépendant et surveillance CI | P1 audit |
| E2E offline Windows | `DONE` selon Codex | 313 tests verts; parse PowerShell sans exécution; Unicode/SQLite/FTS5 | 2026-10-13 | Rejeu indépendant requis | P1 audit |
| CI Windows/Linux | `PASS_OBSERVED` | workflow no 38504190576 vert sur `windows-latest` et `ubuntu-latest` au SHA `3c252f6`; permissions `contents: read`, aucun test réseau | 2026-10-13 | Audit indépendant toujours requis; une CI verte ne prouve pas la complétude fonctionnelle | P1 audit |
| Smoke réel données personnelles / vraie capture | `BLOCKED_WITH_REASON` | explicitement interdit pendant LOT E | 2026-10-13 | Consentements séparés, backup préalable et protocole terrain LOT F | P0/P3 propriétaire |

## Preuves d’exécution

- Baseline : 288 tests. Suite LOT E locale : **313 réussis, 1 skip** en environ
  62 s; le skip est la création de symlink non permise par Windows.
- `python -m compileall -q src tests scripts`, `git diff --check` et
  `python scripts/check_repo_hygiene.py` réussis.
- E0 ciblé : 14 tests. E1–E2 + E0 : 24 réussis, 1 skip. E2E LOT E : 3 réussis.
- La vraie SQLite est demeurée schéma 7 en consultation seulement. Aucune migration,
  sauvegarde, restauration, rétention ou import personnel n’a été appliqué.
- Aucun scheduler, service, modèle, paquet vision, capture réelle, cloud, compte
  Pokémon, achat/crédit, merge ou changement de branche par défaut.

## Verdict

La qualité technique locale et le mécanisme de récupération ont progressé, mais la
reconnaissance visuelle automatique — fonction V1 fondamentale — ne fonctionne pas,
et plusieurs connaissances publiques ne sont pas complètes. LOT E est livré pour
audit, tandis que la V1 reste `NOT_RELEASE_READY`. Les lignes partielles/bloquées
passent au LOT F; aucune n’est supprimée.
