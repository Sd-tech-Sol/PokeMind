# QA LOT J — rapport Codex, audit indépendant à faire

Addendum post-audit, correctif Stage 1B : préservation des fichiers sur erreur,
21 nouvelles régressions synthétiques, sans accès personnel ni sauvegarde réelle.
Les preuves actuelles sont dans [BACKUP_RESIDUE_FIX_QA.md](BACKUP_RESIDUE_FIX_QA.md).
Les nombres et runs J historiques ci-dessous ne remplacent pas sa CI finale.

2026-10-15 Québec/UTC. Branche exclusive
`work/pm-v1-lotj-final-readiness-windows`, base de préparation
`b323f18e295e3b5955816883274ba329337bc9ab`, descendant de I audité
`aade0fd6b3594e0198c304d472931a0fb6793a0b`. A–I conservés. Schéma logiciel13.

## Prévol et portée

Arbre propre initialement sur I, aucune divergence ni modification à préserver.
`git fetch origin --prune`, création de la branche locale J avec tracking, puis
`git pull --ff-only` : déjà à jour. Aucun reset, merge ni force-push. Mandat J,
audit I/H, politique d'autonomie, plans/matrices/rapports/règles et modules concernés lus.

AGENTS impose status/search en premier : deux consultations locales ont été
faites avant lecture du mandat détaillé J; aucune migration/écriture personnelle.
Référence renvoyée notamment : VOLUME4, source2026-10-09, fichier
`source_material/markdown/04_entrainement.md`, lignes91–98 (`.md`). Ce passage
ne fonde aucun mandat technique. Après lecture de NEXT_PROMPT, aucun nouvel
accès aux données personnelles; pas de SHA/intégrité personnelle prétendus.

Windows11, Python3.13.15, SQLite3.50.4. Baseline **428 passed,3 skipped,122,60s**.
Compilation/hygiène/diffcheck réussis. Aucune dépendance nouvelle ni installation.
Ubuntu conserve seulement le job de non-régression existant, workflow inchangé.

## Vérifications réellement faites

- J0 : PATH hostile sans exécution dans prévol/benchmark/observation; faux PE
  jamais exécuté, politique séparée et version/pack/hash/alias/size/console refusés;
  changement après processus détecté. Le Python de pytest éprouve stdout/stderr
  excessifs, timeout et arguments console littéraux. Corpus22/88 inchangé,
  fausses identités/langues/HP et ancienne certitude testés par suites héritées.
- J1 : `preflight` teste réellement FTS5 en mémoire sans sélectionner la DB;
  `demo` rejoué directement et dans pytest :44 CLI fraîches,4 volumes/10citations,
  versions60/export/réimport,3journaux dédupliqués/n=3,3tours/correction/conflit et
  reprise mémoire entre processus. Aucun `/clear` de l'interface n'est prétendu.
- J2/J3 : metadata ancienne/stale/duréeinversée/gap/reset sur les quatre scopes,
  couverture globale indépendante des vieux curseurs; découvertevia sets distincte
  du dénominateur d'index,404FR. Contradiction de réimpression et publicationfuture
  rendent unknown; suites HTTP429/timeouts/quota/reprise/contexts conservées.
  Campagnes PUBLIC réelles **64/68 GET sur trois commandes réseau**, détaillées
  séparément dans PUBLIC_EVIDENCE; aucune assertion normative ajoutée.
- J4 : cinq prévisualisations sur fixtures, source/backup inchangés, refus de
  cibleexistante et reparseWindows. Suites recoveryF/G/H/I : WAL/SHM/journal,
  identité/hash source+manifeste, hardlinks/concurrence/collisions/pannes/résidus.
  Répétition historique7→13 H conserve FTS/FK/histoires. ACL/chiffrement/namespace
  Windows/exclusion/power-loss toujours non prouvés, aucun purge/replace bypass.
  Revue finale : `_db_for`/`_private_path` résolvaient auparavant les chemins
  avant contrôle et pouvaient masquer une jonction. Correction avant resolve,
  vraie jonction Windows créée pour tester les trois entrées CLI et refus neutre
  sans lecture/création dans la cible. Test Windows seulement; Ubuntu l'exclut.
- J5 : mocks interdisent toute invocation d'utilitaire OS dans install/status/
  uninstall dry-run, refus sans fuseau explicite, fuseauasserté ≠ observé;
  suites DSTdaily/Tue-Fri/DeepTime/retry/idempotence/alertes héritées exécutées.

Erreurs ordinaires corrigées durant J : fermeture manquante d'une connexion
PUBLIC révélée par WinError32 au teardown; faux refus sur lignes internes FTS
vides; première extension des dates confondant évaluation rétrospective des règles
et disponibilité historique du cache. Cette dernière a été corrigée pour garder
la sémantique effective héritée, avec garde spécifique sur publicationfuture.
Les échecs ont été retestés; aucun test existant supprimé pour les masquer.

## Tests locaux et preuves du dernier code

Première suite entière : **453 passed,3 skipped,134,73s**. Quatre régressions
supplémentaires ont ensuite couvert version/langue/encodage du diagnostic et
complétude globale fondée sur un ancien curseur.

Suite locale avant correction finale de jonction : **457 passed,3 skipped en137,90s**, au checkpoint de code
`58eb481318650c33c133086fc952ff6e0c247a38`. Toutes les suites A–I et les29 nouvelles
régressions J exécutées. Compilation/hygiène/diffcheck réussis, relancés après
staging documentaire; seul `data/local/.gitkeep` est suivi sous données privées.

**Suite finale après correction de jonction : 458 passed,3 skipped en137,49s.**
Trente régressions J supplémentaires par rapport à la baseline. Le test de vraie
jonction passe sur ce PC Windows; Ubuntu doit l'exclure, en plus des deux OCR.
Une nouvelle CI après9bcd06c est obligatoire. Ne pas traiter les deux checkpoints
58eb481/9bcd06c comme le dernier code de sûreté.

Commandes finales :

```powershell
python -m pytest -q --junitxml=data/local/lot-j-final-junit.xml
python -m compileall -q src tests scripts
python scripts/check_repo_hygiene.py
git diff --check
```

Les deux tests OCRréels nécessitent politique et opt-in explicites; ils restent
exclus. Troisième skiplocal : symlinkWindows sans privilège. Ces exclusions ne
prouvent aucune précisionOCR. Aucun fichier de test n'est une capture réelle.
Démo et benchmark agrégés locaux sous `data/local/lot-j-*.json`, non versionnés;
réponses/campagnePUBLIC sous le workspace marqué, hors Git, sans nettoyage privé.

## CI du SHA FINAL

Checkpoint de code (preuve distincte de la livraison documentaire finale) :
[run38688358580](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38688358580),
SHA `58eb481318650c33c133086fc952ff6e0c247a38`, deux jobs `success`.
Logs lus : Windows458 passed/2 skipped,82,15s; Ubuntu458 passed/2 skipped,41,79s.
Les deux lignes `ci_evidence` contiennent ce SHA exact. Ne pas substituer cette exécution
au dernier HEAD après le commit des rapports.

Après le dernier commit et push, comparer `git rev-parse HEAD`,
`git ls-remote origin refs/heads/work/pm-v1-lotj-final-readiness-windows` et
`headSha` du run GitHub Actions. Lire les DEUX jobs/logsWindows/Ubuntu : succès,
nombres/skips et `ci_evidence=TECHNICAL_TESTS_GREEN ... sha=SHA_FINAL` exact.
Les preuves de ce commit restent dans Actions, sans prétendre écrire un SHA dans
son propre contenu. Les résultats de checkpoint sont clairement distincts.
Le lien du runfinal accompagne le bilan terminal; aucun commit ensuite sans
revérifier sa propre CI. L'audit indépendantChatGPT reste une autre preuve.

## Limites et livraison

La matriceA–J et readiness conservent chaque objectif. Catalogue/normes/méta
incomplets, TrainerHill sans accès, OCRréel/calibration/3captures non testés,
récupération opérationnelle/ACL/chiffrement/purge/remplacement et schedulerOS
toujours partiels/bloqués. Parcours propriétaire cinq décisions préparé; aucun
compte/clientPokémon, capture réelle, achat/crédit, import/backup/clone/migration
personnel, tâcheOS ou installation exécuté. V1 NOT_RELEASE_READY.
STOP pour auditChatGPT, aucune brancheK/merge/release créée.
