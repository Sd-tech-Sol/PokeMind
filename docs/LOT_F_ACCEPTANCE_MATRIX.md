# Matrice d’acceptation — LOT F et fonctions V1 A–F

Date de preuve Codex : 2026-10-14. Statut global : `NOT_RELEASE_READY`.
`DONE` signifie mécanisme/test dans le périmètre indiqué, jamais audit indépendant.

| Fonction V1 | État | Preuve LOT F | Travail restant |
|---|---|---|---|
| A — bibliothèque Markdown/FTS/citations | `DONE` | suite historique + intégrité/FTS | validation continue des sources changeantes |
| A — TCGdex FR/EN | `PARTIAL_WITH_EVIDENCE` | campagne publique jetable 221 sets; GET 100 cartes EN après fix `?`; `test_cards.py` | finir scopes/détails EN/FR; total global inconnu |
| A — identités/réimpressions/promos/errata | `PARTIAL_WITH_EVIDENCE` | résolution stricte et règles datées existantes | registre officiel exhaustif absent |
| A — règles Standard/Expanded/Live | `PARTIAL_WITH_EVIDENCE` | verdict tri-state et sources versionnées | compléter rotations/exceptions/compatibilité Live |
| A — Limitless | `PARTIAL_WITH_EVIDENCE` | filtres contexte et zéro-échantillon testés | augmenter snapshots classifiables |
| A — Trainer Hill | `BLOCKED_WITH_REASON` | aucune API/permission publique vérifiée | source primaire autorisée requise; pas de scraping |
| B — deck exact/version/export 60 | `DONE` mécanisme | tests deck/export + readiness compte les versions réellement 60 | chaque import réel reste volontaire |
| B — collection/crédits | `DONE` mécanisme / `BLOCKED_WITH_REASON` données | statut sans valeur privée | déclaration propriétaire facultative |
| B — conseils/candidats | `PARTIAL_WITH_EVIDENCE` | tests recommandations/candidats | couverture règles/cartes/méta/collection |
| C — images éphémères et mémoire | `DONE` | path/symlink/limites, aucun pixel SQLite, révisions | maintenir portabilité |
| C/F1 — lecture locale de pixels | `PARTIAL_WITH_EVIDENCE` | PNG RGB/RGBA décodé; ROI/seuils/occlusion; E2E | backend général + calibration/essai réel |
| C/F1 — conseil tour par tour | `PARTIAL_WITH_EVIDENCE` | provenance `visual_certain` interne → mémoire → conseil sourcé | effets complets et terrain autorisé |
| D — updater public | `DONE` mécanisme / `PARTIAL` données | quotas/reprise/alertes + rapport readiness | poursuivre fenêtres publiques |
| D — scheduler dry-run | `DONE_PLAN_ONLY` | manifeste/timezone/DeepTime testés | opt-in et audit avant activation |
| D — scheduler actif | `BLOCKED_WITH_REASON` | aucune tâche installée | consentement spécifique futur |
| E/F0 — backup | `DONE_SYNTHETIC` | checksum/manifeste/intégrité/FK/FTS | premier backup réel séparément commandé |
| E/F0 — restore | `DONE_SYNTHETIC` | attestation source prépublication, WAL/lock refusés, rollback | audit indépendant puis clone réel volontaire |
| E/F0 — rétention | `DONE_SYNTHETIC` | inventaire SHA réel, plan revalidé sous verrou, rollback paire | aucune purge réelle; politique owner |
| E — confidentialité/hygiène | `DONE` | erreurs neutres, hygiene Git, rapport sans détail privé | surveillance continue |
| F3 — E2E | `DONE_LOCAL` | LOT F vision→mémoire→backup→restore→readiness | audit indépendant |
| F3 — CI Windows/Linux | `PASS_OBSERVED` | run `38509657380`, Windows+Ubuntu verts au SHA `ec190e1` | une CI verte ne prouve pas le terrain propriétaire |
| F4 — mise en service propriétaire | `DONE_PLAN_ONLY` | guide à six portes séparées | exécution seulement sur ordres distincts |
| F5 — readiness A–F | `DONE_DOCUMENTATION` | présent document + rapport CLI | audit indépendant |

## Interdictions respectées

Aucune donnée personnelle, vraie image, migration/restauration/purge, installation de
paquet/modèle, tâche Windows, interaction compte Pokémon, achat, merge, reset ou
force-push. La micro-campagne n’a utilisé que TCGdex public dans des bases jetables
ensuite supprimées.
