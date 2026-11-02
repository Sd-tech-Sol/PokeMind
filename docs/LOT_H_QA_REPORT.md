# QA LOT H — développement H0–H5, 2026-10-14 Québec

Rapport Codex; ce n'est pas l'audit indépendant ChatGPT. V1 NOT_RELEASE_READY.
Le précédent rapport de récupération est historique dans LOT_H_RECOVERY_REPORT.

## Prévol et périmètre

Worktree propre sur branche H; fetch origin puis pull --ff-only de cde321c vers
c0c543c. Mandat complet NEXT_PROMPT et références d'orchestration/architecture/
sources/audit G lus. Code A–G conservé. Aucun H perdu recherché une seconde fois.
Status/search locaux en lecture seule; aucun acte propriétaire appliqué. Le schéma
logiciel reste 13. Aucune migration personnelle ni nouvelle dépendance.

Baseline : **388 passed, 2 skipped, 94,93 s** Windows local. Skips hérités :
Tesseract absent et privilège de création de symlink indisponible.

## Tests et corrections significatifs

- H0 : processus Python séparés tenant une connexion SQLite idle, un writer DELETE
  ou WAL; cible existante refusée et octets préservés. Processus créant une cible
  à la publication : aucune substitution du fichier. Hardlink source/manifest
  refusé, collision de manifeste préservée, fsync/disque refusé sans faux succès,
  verrou remplacé préservé. Résidus consultables sans droit d'écriture.
- Keep_last sain, manifestes hostiles, >1000 manifestes et source/manifeste changés
  gardent leurs contrôles. L'ancienne rétention était une suppression multifichier
  vulnérable aux races extérieures; H la refuse publiquement sans bypass. Trois
  tests hérités de suppression/staging sont adaptés au refus sans mutation; leur
  injection n'est plus décrite comme un staging effectivement exécuté.
- Première régression complète : 8 échecs dus au fsync d'un descripteur readonly
  sous Windows. Correction r+b, puis 26 tests ciblés récup/E2E/readiness réussis.
  L'attestation stable a aussi requis de distinguer ctime handle/path sous Windows;
  les autres champs d'identité et le contenu restent contrôlés.
- H1 : corpus de vrais textes rasterisés FR/EN (22 cas, 88 champs), absence moteur
  explicite, aucun TSV simulé dans le benchmark; identité inconnue/mauvais code,
  numéro et HP, occlusion/crop/bruit/zoom/cisaillement. Store lié au digest de
  l'observation, prévisualisation, dédoublonnage, correction invalidante, révocation,
  relecture dans mémoire/conseil et restauration; aucune visual_certain promue.
- H2 : fin de scan et membres distincts de l'union FR/EN, reprise sans page1,
  doublon/gap/stale/futur et détails indisponibles; tests cartes/règles existants.
  Revue intégrale liée au SHA entier, modification→stale et aucune assertion
  promue. Métagame exclut événement futur et observation future; n=0 reste inconnu.
- H3 : structure historique7 sans tables futures, corpus/FTS/catalogue/deck60/
  combat synthétiques; backup vérifié→clone13→historiques identiques; trois tours
  PNG de marqueurs réellement décodés (pas OCR), review/advise/révocation,
  second backup/clone→mémoire persistée; source original byte-identique.
- H4 : Toronto quotidien et mardi/vendredi, DeepTime, DST heure inexistante/répétée,
  reprise du plus récent deep, idempotence et refus d'horloge naïve; install,
  status et uninstall simulés ne contactent pas l'OS. Tests hérités lock/retry/
  quotas/alertes/rollback/offline conservés.
- H5 : toutes gates G conservées; nouvelles portes calibration réelle OCR et
  rétention sûre. Les revues owner_asserted et simulations ne satisfont pas
  vision réelle, scheduler, remplacement, purge ou audit indépendant.

Auto-revue H5 supplémentaire : l'ancien adaptateur de marqueurs pouvait produire
visual_certain et conseiller une attaque malgré la porte release fermée. Correction
au commit a1647fb : marqueurs ocr_uncertain, calibration réelle=false et les anciennes
observations visuelles non calibrées ne sont plus des faits pour le conseil. Test
de régression ajouté; annotations propriétaires manuelles conservées. Les 34 tests
ciblés visuel/E2E réussissent, un skip OCR absent. Nouvelle suite complète ci-dessous.

## Résultat local final

**415 passed, 3 skipped en 106,60 s**; JUnit privé
`data/local/lot-h-final-junit.xml` (non versionné). Troisième skip ajouté : test
Tesseract réel du corpus, moteur absent. La rasterisation et les garde-fous ont
été exécutés sans moteur. Compilation src/tests/scripts, hygiène Git et
`git diff --check` réussis. Aucun test réseau dans pytest/CI.

Le benchmark local versionné contient OCR_ENGINE_NOT_INSTALLED, zéro tentative,
aucun pixel persistant et aucune métrique de précision inventée. Les mesures
Python wall/mémoire ne sont pas des mesures de Tesseract. La campagne publique
séparée consomme 29/32 GET, base jetable, rapport LOT_H_PUBLIC_EVIDENCE.

## CI observée et preuve finale

Code **b056218f6142ac388a5539e6c407557637637a44**, run
[38677662258](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38677662258) :
API completed/success. Jobs Ubuntu116234837178 et Windows116234838065 success;
logs consultés : **415 passed, 2 skipped chacun**, respectivement 40,14 s / 63,93 s.
Différence locale : le symlink fonctionne sur les runners. Deux skips OCR absent.
Les jobs publient TECHNICAL_TESTS_GREEN avec ce SHA précis; compilation/hygiène/diff
réussis. C'est une preuve CI automatisée, pas un audit indépendant ChatGPT.

Durcissement **a1647fb6b8ae5f672b1a44ff37a92671faf61a2b**, run
[38678122722](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38678122722) :
API completed/success, jobs Ubuntu116236270494 et Windows116236270795 success.
Logs lus : 416 passed/2 skipped sur chaque plateforme. Le test ajouté ferme
l'ancienne confiance accordée aux marqueurs/visual_certain sans calibration.

Ces runs de code ne sont PAS substitués à la CI du commit de clôture documentaire.
Le workflow existant publie pour chaque dernier HEAD son SHA exact, OS et nombres
dans les résumés de jobs. La livraison finale n'est annoncée qu'après lecture des
résultats Actions des DEUX jobs et de leurs logs pour le dernier SHA distant.
Le lien définitif est donné dans le compte rendu de livraison; la preuve liée au
SHA final reste dans Actions, sans tentative de SHA auto-référent dans ce fichier.

## Bornes

Pas d'installation locale OCR/modèle/paquet, vraie capture, client/compte Pokémon,
planificateur OS, achat/crédits, vraie opération backup/restore/retention/migration/
import/attestation, merge/reset/force-push. Aucune comparaison personnelle SHA
avant/après n'a été effectuée; ne pas la confondre avec celle des fixtures.
La V1 garde les blocages de la matrice H et le plan I+. STOP audit ChatGPT.
