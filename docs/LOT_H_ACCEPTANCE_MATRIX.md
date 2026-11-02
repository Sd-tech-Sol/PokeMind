# Matrice H0–H5 et V1 intégrale — 2026-10-14 Québec

Livraison de développement Codex pour audit indépendant ChatGPT.
**V1 NOT_RELEASE_READY.** DONE vise uniquement le mécanisme et les preuves cités.
PARTIAL_WITH_EVIDENCE et BLOCKED_WITH_REASON ne ferment aucun objectif.

| Objectif A–H | État | Preuve test/source | Limite et prochaine action |
|---|---|---|---|
| A bibliothèque, 4 volumes, citations FTS | DONE | suites import/search/markdown; E2E historique7→13 conserve contenu et MATCH FTS | règles changeantes ne deviennent pas normatives par les volumes |
| A/H2 historique TCGdex FR/EN | PARTIAL_WITH_EVIDENCE | `catalog_snapshots.py`, `test_lot_h_knowledge.py`; 16 GET publics | membres datés, détails partiels; finir campagnes sans réduire l'historique |
| A/H2 dénominateurs | PARTIAL_WITH_EVIDENCE | membres par page + checkpoint transactionnel; gap/doublon/reprise/stale testés | dénominateur du scan fini seulement; total fournisseur unknown, pagination mutable |
| A éditions, variants/réimpressions | PARTIAL_WITH_EVIDENCE | `cards.py`/suites reprints et identités; pas d'équivalence par nom | registre fonctionnel et variants exhaustifs non prouvés; poursuivre I+ |
| A rotations Standard Live/physique | PARTIAL_WITH_EVIDENCE | registre daté hérité, `normative_coverage`, refus de capture future H | nouvelles pages officielles non revues intégralement; dates/sources complètes à valider |
| A structure 60, bans/exceptions | PARTIAL_WITH_EVIDENCE | suites rules/candidates; aucune légalité globale avec preuves incomplètes | couverture des exceptions et restrictions à finir avec sources officielles |
| A Expanded, promos, errata, Live | PARTIAL_WITH_EVIDENCE | gates séparées, tri-state, revue documentaire liée au SHA entier | pas de registre exhaustif validé; HTTP 200/hash n'est pas preuve normative |
| A/H2 revue officielle | DONE | `official_reviews.py`, `knowledge review-official`; changement rend stale; assertions inchangées | DONE pour workflow, revue complète/validation normative de contenu reste partielle |
| A/H2 Limitless descriptif | PARTIAL_WITH_EVIDENCE | 3 snapshots publics; n=553 pairings, 497 classifiables; BO/périodes/biais, futures observations exclues | base jetable, pas de couverture personnelle/globale; aucun taux de victoire annoncé |
| A Trainer Hill | BLOCKED_WITH_REASON | accès automatisé autorisé non établi, aucun scraping tenté | preuve primaire des conditions/API autorisées avant collecteur |
| B deck/version/export 60 | DONE | suites decks/export/candidates; E2E historique conserve version et 60 cartes | export exact ≠ légal; import réel et choix de deck distincts |
| B collection et crédits facultatifs | DONE | mécanismes import/rollback hors ligne et gates non requises | aucun import personnel H; possession/coût unknown sans déclaration/tarif |
| B conseils conditionnels/candidats | PARTIAL_WITH_EVIDENCE | suites analysis/recommendations/candidates | dépendance aux cartes/règles/méta, n/version et informations fournies; aucun achat |
| B journaux/profil/versions | PARTIAL_WITH_EVIDENCE | parseur/dédoublonnage/attestations réversibles hérités, E2E H préserve historiques | liens propriétaire réels distincts; cartes observées ≠ collection ou deck60 |
| C images éphémères et mémoire | DONE | PNG synthétique→3 tours→review→advise→révocation→backup/clone | aucun pixel en SQLite, images réelles non utilisées |
| C/H1 corpus rasterisé | DONE | 22 cas FR/EN, 88 champs; `ocr_benchmark.py`, tests sans mock et artefact JSON | police 5×7/cisaillement, corpus simple ≠ vraie carte/calibration |
| C/H1 OCR réel et mesures d'erreurs | BLOCKED_WITH_REASON | OCR_ENGINE_NOT_INSTALLED; compteur attempted=0, métriques inconnues; test réel ignoré | choisir/installer moteur/langues après ordre séparé, exécuter/calibrer |
| C/H1 store de revues | DONE | `vision_evidence.py`; digest/contexte/profil, preview, correction, dédoublonnage, révocation et restauration | owner_asserted seulement, aucune promotion visual_certain/porte release |
| C vraie capture et 3 décisions réelles | BLOCKED_WITH_REASON | aucun essai propriétaire; gate reste fermée | calibration puis essai volontaire en entraînement permis sur ordre distinct |
| C conseil tour par tour | PARTIAL_WITH_EVIDENCE | exact état actif, options conditionnelles, repli/inconnues, revue ajoutée au conseil | règles/effets complets et essai réel manquants |
| D collecteurs/quotas/reprise/offline | DONE | suites updates/cards/meta/security et campagne bornée | mécanismes prouvés; exhaustivité/fraîcheur réelle à poursuivre |
| D/H4 cadence logicielle Toronto | DONE | simulation daily+Tue/Fri, DeepTime, DST printemps/automne, reprise/idempotence, horloge naïve refusée | politique simulée DST ≠ preuve OS; CI fixtures, pas de service actif |
| D/H4 installation/statut/désinstallation OS | BLOCKED_WITH_REASON | scheduler_contacted=false, active_service_proven=false, OWNER_ACTION_REQUIRED | aucun contact/activation OS; consentement, heures, preuve réelle séparés |
| E/H0 snapshot backup autonome | DONE | SQLite backup WAL→DELETE, vérification source/manifeste, flush, lien sans écrasement et collision testés | vrai premier backup distinct; pas de transaction multifichier/power-loss garanti |
| E/H0 attestation stable/aliases | DONE | hachage même handle, identité/métadonnées avant/après; alias hardlink refusé | pas d'exclusion universelle face à un processus ayant les mêmes droits |
| E/H0 clone neuf sans écrasement | DONE | processus externe idle/writer/WAL; fichier créé au moment publication conservé; rollback G conservé | activation offline explicite séparée; filesystem sans hardlink refuse |
| E/H0 remplacement opérationnel | BLOCKED_WITH_REASON | RESTORE_EXISTING_TARGET_BLOCKED, même cible idle; helpers anciens seulement fixtures | exclusion extérieure durable et sécurité crash à démontrer |
| E/H0 rétention opérationnelle | BLOCKED_WITH_REASON | apply refuse RETENTION_EXTERNAL_EXCLUSION_UNPROVEN; aucun bypass ni staging nouveau | keep_last face aux autres processus/power-loss non prouvé; protocole I+ |
| E/H0 consultation/résidus | DONE | lecture sans W_OK, compteurs résidus, manifestes hostiles/limite1000/backup corrompu | inspection offline propriétaire, aucune réparation/purge implicite |
| E/H3 prévols et répétition propriétaire | DONE | owner-plan, vraie structure synthétique7→13, octets source/historiques/FK/FTS, trois tours et revues restaurées | prévol d'un backup ≠ preuve de correspondance au source; actes réels séparés |
| E/H3 actes propriétaires réels | BLOCKED_WITH_REASON | aucun backup/restore/purge/migration/import/attestation personnel H | autorisation distincte pour chacun; guide préparé |
| E confidentialité | DONE | fixtures synthétiques, rapport agrégé, hygiène Git, pas de chemins/valeurs privées dans readiness | pas d'audit universel des octets privés prétendu; aucune comparaison SHA personnelle H |
| H5 gates V1 exhaustives | DONE | `test_lot_h_readiness.py` et gates G; OCR/calibration/rétention/OS/audit bloquent explicitement | aucune porte ne peut être levée par un simple flag de simulation |
| H5 Windows/Linux | DONE | CI de code a1647fb : Windows/Ubuntu 416 pass/2 skips, run 38678122722 | CI du HEAD documentaire final à consulter séparément via Actions et preuve SHA des jobs |
| H5 audit/release finale | BLOCKED_WITH_REASON | STOP de livraison, pas d'auto-VERIFIED; LOT_I_COMPLETION_PLAN | audit ChatGPT puis mandats I+; aucun merge ni RELEASE_READY |

Preuves détaillées : LOT_H_QA_REPORT, LOT_H_LOCAL_VISION, LOT_H_PUBLIC_EVIDENCE,
MISE_EN_SERVICE_PROPRIETAIRE, V1_READINESS_REPORT. Les lignes A–G sont conservées;
les tests historiques ne sont pas présentés comme de nouvelles fonctions H.
