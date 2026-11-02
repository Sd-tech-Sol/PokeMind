# Matrice V1 A–I — livraison pour audit ChatGPT

2026-10-15 Québec. **NOT_RELEASE_READY**. DONE porte sur le mécanisme et les
preuves nommés, jamais sur une capacité réelle absente. Aucun objectif A–H retiré.

| Lot I | État | Preuve / limite |
|---|---|---|
| I0 audit/régressions H | DONE | baseline 415/3; `test_lot_i_safety.py`, suites G/H; dénominateurs, OCR et récupération renforcés |
| I1 premier parcours Windows/Codex | DONE | `demo`, `test_lot_i_e2e.py`, guide Windows; processus frais, fixtures, aucune base personnelle |
| I2 connaissances FR/EN/normes/méta | PARTIAL_WITH_EVIDENCE | dérive de tête et scans/erreurs testés, campagne 31/34 GET; normes complètes et historique exhaustif non établis |
| I3 OCR préparé | PARTIAL_WITH_EVIDENCE | preflight local + identité 4 champs/langue/stale; moteur absent, installation/calibration/essai réel bloqués |
| I4 decks/journaux/coach synthétiques | DONE | versions 60/export/réimport,3 combats dédupliqués, n=3,3 tours/correction/conflit/reprise; application personnelle distincte |
| I5 intégrité et récupération Windows | PARTIAL_WITH_EVIDENCE | panne entre backup/manifeste, reparse points/résidus; remplacement/purge et garanties ACL/flush/power-loss bloqués |
| I6 cadence Windows préparée | DONE | daily+Tue/Fri/DST/idempotence H conservés; install/status/uninstall dry-run en démo; OS jamais contacté |
| I7 QA/matrice/passation | DONE | suite locale, compilation/hygiène/diff; workflow existant vérifié au SHA final avant annonce; audit ChatGPT distinct |

| Objectif V1 A–H conservé avec apports I | État | Preuve / limite et prochain ordre |
|---|---|---|
| A bibliothèque 4 volumes et citations FTS | DONE | import/search/markdown;10 recherches de la démo, source 2026-10-09, extension.md et lignes; règles changeantes distinctes |
| A historique TCGdex EN/FR | PARTIAL_WITH_EVIDENCE | quatre scopes, détails/stale/404; campagne locale cumulative; poursuivre progressivement index puis détails |
| A dénominateurs fiables | PARTIAL_WITH_EVIDENCE | duplication interne/interpage,0/unknown/stale/erreur/durée et dérive testés; scan observé ≠ total fournisseur |
| A éditions/variantes/identités | PARTIAL_WITH_EVIDENCE | `cards.py` et tests hérités; champs manquants explicites, pas d'exhaustivité attestée |
| A réimpressions/texte effectif/errata | PARTIAL_WITH_EVIDENCE | registre daté/tri-state/reprints; aucune équivalence par nom; preuves officielles à compléter |
| A rotations Standard Live/présentiel | PARTIAL_WITH_EVIDENCE | gates séparées, dates de revue future refusées; sources entières datées manquantes |
| A structure 60/quotas/exceptions/bans | PARTIAL_WITH_EVIDENCE | `rules.py`/tests; total exact ≠ conformité normative complète; compléter exceptions et identités |
| A Expanded | PARTIAL_WITH_EVIDENCE | contexte et gate spécifiques; catalogue historique ≠ éligibilité ≠ support client |
| A promos | PARTIAL_WITH_EVIDENCE | gate propre; date/impression/source admissibilité à valider |
| A compatibilité Live | PARTIAL_WITH_EVIDENCE | inconnue sans preuve client/officielle; pas de déduction depuis TCGdex |
| A revue entière des sources | PARTIAL_WITH_EVIDENCE | store hash/revue/registre distincts; pages web inexploitable/iframe,0 assertion nouvelle; pas de legal par 200/hash |
| A Limitless descriptif | PARTIAL_WITH_EVIDENCE | campagne 1 snapshot,9 pairings dont 3 admissibles, SWISS/BO1/PTCGL/online/date; n et biais, événement non finalisé |
| A Trainer Hill | BLOCKED_WITH_REASON | accès automatisé primaire autorisé non prouvé; aucun scraping |
| B decks/version/export 60 | DONE | deux versions synthétiques, comparaison, export/réimport PTCGL; aucune modification du client/deck joué |
| B collection/crédits facultatifs | DONE | import/version/rollback et gates hérités; aucun apport personnel I; possession/coûts unknown |
| B diagnostic/conseils/candidats | PARTIAL_WITH_EVIDENCE | suites analysis/recommendations/candidates; conseils prudents, données normatives/méta encore partielles |
| B journaux/profil/leçons | PARTIAL_WITH_EVIDENCE | trois logs indépendants+réimports idempotents; n=3 insuffisant pour tendance,0 lien inféré; cartes vues ≠ deck 60/collection |
| B confirmations de version réversibles | DONE | suites attestations/version_evidence conservées; confirmation personnelle unitaire distincte |
| C images éphémères et mémoire | DONE |3 tours annotés+PNG raster,4 révisions dont 3 actives, processus frais; pixels non stockés |
| C corpus raster FR/EN | DONE |22 cas/88 champs H, police artificielle; distinct d'imitation de capture et vraie image |
| C OCR réel et métriques | BLOCKED_WITH_REASON | OCR_ENGINE_NOT_INSTALLED; précision/faux positifs/CPU/RSS inconnus; installation/packs et benchmark distincts |
| C revues/digests/révocations | DONE | suites H conservées; owner_asserted et anciennes certitudes ne font pas preuve indépendante |
| C vraie capture et 3 décisions | BLOCKED_WITH_REASON | aucun essai ni calibration propriétaire; opt-in entraînement autorisé requis |
| C conseil de tour/repli/inconnues | PARTIAL_WITH_EVIDENCE | corrections/contexte refusé et options conditionnelles; règles/effets complets et essai terrain manquants |
| D collecteurs/quotas/reprise/offline | DONE | suites cards/meta/updates/security et campagne PUBLIC bornée; fraîcheur/exhaustivité produit partielle |
| D cadence Toronto daily+Tue/Fri | DONE | H DST/reprise/idempotence et démo I; Eastern Standard Time, DeepTime conservés |
| D installation/statut/désinstallation OS | BLOCKED_WITH_REASON | simulation seulement, scheduler_contacted=false; opt-in/heures/fuseau et preuves réelles nécessaires |
| E backup autonome et attestation | DONE | sqlite 3.backup/WAL→DELETE/FK/FTS/manifest/checksums; publication individuelle, pas transaction/power-loss garanti |
| E aliases/chemins Windows | DONE | hardlinks/symlinks/reparse points refusés, attestations stables; exclusion universelle non prouvée |
| E clone neuf sans écrasement | DONE | suites G/H idle/writer/WAL/collisions/rollback; activation offline personnelle distincte |
| E remplacement existant | BLOCKED_WITH_REASON | RESTORE_EXISTING_TARGET_BLOCKED; pas de contournement |
| E rétention/purge | BLOCKED_WITH_REASON | RETENTION_EXTERNAL_EXCLUSION_UNPROVEN; keep_last multifichier non prouvé |
| E inventaire/résidus | DONE | panne inter-fichiers conserve base non attestée; sidecars/manifeste orphelin/lock visibles; aucune purge |
| E ACL/chiffrement/durabilité Windows | PARTIAL_WITH_EVIDENCE | ACL non attestée, chiffrement non implémenté, flush namespace/power-loss non prouvé; protocole isolé à auditer |
| E prévol/migration fixtures 7→13 | DONE | `test_lot_h_commissioning.py`; source/historiques/FTS/FK conservés, clone seulement |
| E mise en service propriétaire | BLOCKED_WITH_REASON | aucun acte réel I; backup/clone/migration/import/attestation/activation autorisations distinctes |
| E confidentialité | DONE | fixtures et rapports agrégés, hygiène Git, données/API/CI séparées; pas d'audit universel du disque prétendu |
| F/G/H gates exhaustives | DONE | readiness ne lance pas la démo, ne promeut pas ses preuves synthétiques; toutes gates héritées maintenues |
| F/G/H/I QA Windows/CI héritée | DONE | QA locale et deux logs Actions au SHA exact; aucune nouvelle fonction Linux |
| H audit indépendant technique | DONE | audit ChatGPT VERIFICATION_LOT_H, SHA5d 27832,416/2 dans chaque job; réserves conservées |
| I audit/release final | BLOCKED_WITH_REASON | STOP après livraison et CI finale; audit ChatGPT requis; aucun merge ni RELEASE_READY |

Preuves : `LOT_I_QA_REPORT`, `LOT_I_PUBLIC_EVIDENCE`, `LOT_I_LOCAL_VISION`,
`LOT_I_RECOVERY_PROTOCOL`, `PREMIER_USAGE_WINDOWS`, rapports historiques A–H.
Écarts conservés dans `LOT_J_COMPLETION_PLAN` : proposition, aucune autorisation J.
