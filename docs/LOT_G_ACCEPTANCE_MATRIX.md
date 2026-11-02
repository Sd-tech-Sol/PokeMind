# Matrice d’acceptation — LOT G et fonctions V1 A–G

2026-10-14. Livraison Codex pour audit indépendant, **NOT_RELEASE_READY**.
`DONE` concerne le mécanisme et les fixtures indiqués, jamais une qualification
personnelle réelle ou un statut `VERIFIED`. Tous les objectifs antérieurs restent.

| Objectif | État | Preuve et portée | Limite / prochaine action |
|---|---|---|---|
| A — bibliothèque/citations FTS | DONE | suites historiques; G3 vérifie aussi contenu FTS, pas seulement comptes | règles changeantes à revérifier; corpus inchangé |
| A — historique TCGdex FR/EN | PARTIAL_WITH_EVIDENCE | G2 stale non complet, GET restant exact, reprise initiale profonde; campagne publique 4 GET/2 détails | membres d’index et total global inconnus; fenêtres H |
| A — identités/réimpressions | PARTIAL_WITH_EVIDENCE | matching strict; OCR exige nom+code+numéro, source et HP concordants; aucune équivalence de même nom | registre officiel exhaustif absent |
| A — règles/structure/rotations | PARTIAL_WITH_EVIDENCE | `normative_coverage` daté; source non verified/future refuse; gate par plateforme | restrictions/exceptions/Expanded incomplets |
| A — promos/errata/Live | PARTIAL_WITH_EVIDENCE | dimensions séparées et fail-closed | normalisation normative complète et support exact Live à produire |
| A — Limitless | PARTIAL_WITH_EVIDENCE | collecteur public conservé; 2 GET, 3 briefs, aucun winrate; n contextualisé | au moins plusieurs snapshots classifiables; total mondial inconnu |
| A — Trainer Hill | BLOCKED_WITH_REASON | absence d’accès automatisé autorisé établi | preuve primaire d’accès/conditions, aucune API privée supposée |
| B — deck/version/export 60 | DONE | tests historiques et E2E G3 de version synthétique 60 | import réel séparé; export exact ne prouve pas légalité |
| B — collection/crédits volontaires | DONE | mécanismes historiques, absence facultative séparée de release | données réelles inconnues; ordres facultatifs séparés |
| B — conseils/candidats | PARTIAL_WITH_EVIDENCE | aucun achat, présence et coût inconnus sans source; historique conservé | cartes/règles/méta/collection pour conseils contextualisés complets |
| B — observations/versions de combat | PARTIAL_WITH_EVIDENCE | attestations explicites; readiness compte seulement liens cohérents vers 60 | vrais liens et n confirmés par propriétaire, jamais déduits |
| C — images éphémères/mémoire | DONE | observation OCR simulée→3 tours→backup→clone; aucun pixel en SQLite | capture originale jamais supprimée; vraie session distincte |
| C/G1 — OCR local optionnel | PARTIAL_WITH_EVIDENCE | profil ROI/TSV, Unicode/CRLF/zoom, faux noms/HP, seuils et abstention; 32 tests ciblés | OCR absent localement; mocks ne prouvent pas reconnaissance, benchmark H |
| C — reconnaissance vraie capture | BLOCKED_WITH_REASON | aucun essai utilisateur, aucune calibration réelle, pas de cloud | moteur et essai autorisés séparément; store de preuve à construire |
| C — conseils de tour | PARTIAL_WITH_EVIDENCE | provenance `ocr_uncertain` ne promeut aucune action; manuel conservé | règles/effets complets, plateau et terrain autorisé |
| D — collecteurs/cadence logicielle | DONE | quotidien/deep existants, profondeur initiale corrigée, budgets/reprise/DST testés | sources courantes partielles, observation officielle reste non normative |
| D — validation des variations officielles | PARTIAL_WITH_EVIDENCE | file explicite changed/truncated/missing; aucune promotion par hash | revue de contenu et workflow de clôture normatif H |
| D — scheduler actif | BLOCKED_WITH_REASON | activation logiciel toujours désactivée; dry-run seul | opt-in, heures propriétaire, Toronto, installation/contrôle/désinstallation distincts |
| E — sauvegarde vérifiée | DONE | fixtures SHA, SQLite, FK/FTS avec contenu; WAL non haché refusé, snapshot DELETE autonome, réattestation après contrôles | premier backup réel sous ordre distinct |
| E/G0-1 — rollback postpublication | DONE | OperationalError/DatabaseError/PermissionError/OSError/RecoveryError/RuntimeError; anciennes cibles synthétiques octet-identiques; quarantaine préservée si échec | helper d’ancienne cible interne aux fixtures, non accessible en CLI |
| E/G0-2 — protection existante / clone neuf | DONE | refus de toute cible existante, WAL/SHM/journal/header; writer entre gate/publication, collision sans écrasement | protection livrée; remplacement opérationnel reste bloqué |
| E — restauration opérationnelle existante | BLOCKED_WITH_REASON | `RESTORE_EXISTING_TARGET_BLOCKED`; exclusion externe durable non démontrée | H0 Windows/Linux ou solution offline auditée; pas de bypass |
| E/G0-3 — rétention | PARTIAL_WITH_EVIDENCE | contenu/manifeste revalidés, keep_last revérifié; hostile paths, limite 1000, staging/rollback et comptage exact résidus | suppression multifichier non atomique, aucune purge réelle, races externes restent une limite |
| E — confidentialité/hygiène | DONE | rapports sans chemin/montant/carte privée, exceptions neutres, fixtures seules en Git | revue continue, aucune garantie d’audit indépendant implicite |
| F/G3 — QA/E2E portable | DONE | schéma réel synthétique 7 sans tables futures→13, historiques et MATCH FTS conservés; suites Windows et CI | les preuves de données personnelles ne sont pas substituées par la QA |
| G4 — portes de release | DONE | chaque dimension requise explicite; flags superficiellement verts refusés; n=1 insuffisant; propriétaire facultatif non bloquant | vrais producteurs d’attestations/calibration/activation/audit requis en H |
| G5 — clôture et mise en service | DONE | guides séparés, présent tableau, RESULT/HANDOFF/NEXT_ACTION/ROADMAP/DECISIONS et LOT H | STOP pour audit ChatGPT, aucune phase H exécutée |

## Preuves automatisées

Rapport : `docs/LOT_G_QA_REPORT.md`. Chaque job CI publie au HEAD qu’il teste une
preuve agrégée `TECHNICAL_TESTS_GREEN`, SHA exact, plateforme, passed/skipped et lien
du run. Cette preuve reste distincte de `OWNER_ACTION_REQUIRED`,
`PRODUCT_CAPABILITY_PARTIAL` et de l’audit indépendant futur. Aucun résultat de
branche F ou d’un checkpoint G ne remplace la CI du commit final de clôture.

## Périmètre réellement exécuté

Développement G0–G5, tests synthétiques, observation publique courte séparée de QA,
commits et push branche G seulement. Aucune opération privée de backup/restore/
migration/import/purge, aucune installation, vrai screenshot, compte Pokémon,
achat/crédit, tâche Windows, merge, reset ou force-push.
