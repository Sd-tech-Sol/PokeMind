# Audit indépendant ChatGPT — PM-V1-UTC-DATE-001

**Verdict : VERIFIED — correctif ciblé du comportement de date de la démo synthétique, livré sur GitHub et testé au SHA exact.** PokeMind V1 reste **NOT_RELEASE_READY**.

## Sources vérifiées directement dans GitHub
- Branche `work/pm-v1-lotj-final-readiness-windows`; HEAD Codex à l'ouverture de l'audit `4c3bb9b09d481479b34f4933e1e596b0e15b8bd8`. Base du mandat `eeb477bfa3a9cbe03759e9c8b091a65fe3932bcf`. Comparaison : **1 commit, 8 fichiers**.
- Deux fichiers produit/tests : `src/pokemind/demo.py` (**import `date` et un seul appel `recommend --as-of date.today().isoformat()`** au lieu de date UTC), `tests/test_demo_dates.py` (4 scénarios synthétiques complets hiver/été avant et après minuit local). Nouvelle preuve `docs/UTC_DATE_FIX_QA.md` et changements uniquement documentaires dans `.orchestrator/{DECISIONS,HANDOFF,NEXT_ACTION,RESULT,STATE.json}`. Aucune modification de `collection._strict_date`, du module de migrations, du moteur de sauvegarde ni des configurations CI.
- Lecture statique des tests : horloges isolées dans le parent et des CLI filles, déclenchement du chemin réel `recommend`, assertions sur date locale et refus du lendemain local, 3 combats, confinement des données synthétiques, réseau bloqué, absence de fichiers temporaires après la démo. Pour ce défaut, la régression est appropriée. **Limite :** les instantanés simulés testent UTC−5 et UTC−4, pas le jour précis du basculement DST.
- `docs/UTC_DATE_FIX_QA.md` rapporte la **reproduction avant correction** à `2026-01-16 00:30 UTC` (Toronto encore `2026-01-15`) par un test échouant `DEMO_CLI_STEP_FAILED:recommend`; résultat local **19 tests ciblés réussis** puis suite Windows **483 passed/3 skipped**, sans forçage de TZ. Ceci est une **attestation Codex locale**, non une observation de ChatGPT sur son Windows.

## GitHub Actions à SHA exact
[Run 39095686576](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39095686576) : **completed/success**, `head_sha=4c3bb9b09d481479b34f4933e1e596b0e15b8bd8`.
- Windows job `117581525488` : **484 passed, 2 skipped**, 75,05 s, log `ci_evidence=TECHNICAL_TESTS_GREEN ... sha=4c3bb9b09d481479b34f4933e1e596b0e15b8bd8`.
- Ubuntu historique job `117581525687` : **483 passed, 3 skipped**, 82,49 s, même SHA dans le log de preuve.
- Compilation, hygiène dépôt, `git diff --check` réussis sur les deux jobs. Windows CI et Windows local ont des nombres de skips différents (2 contre 3) : sur le PC l'essai symlink a été ignoré faute de privilèges; les logs CI Windows ne montrent aucun échec.
- La CI utilise des fixtures; elle **ne prouve pas les opérations sur la base personnelle**. Aucun changement privé n'est visible dans le diff.

## Décision
- **ACCEPTED / VERIFIED pour PM-V1-UTC-DATE-001.** Correction restreinte à la démo : le contrôleur des dates réelles demeure inchangé, les autres dates UTC de la démo restent utiles au filtrage des trois journaux synthétiques.
- La permission d'exécution de ce mandat est **consommée**. Pas de relance du correctif ni d'élargissement implicite à `data/local/`.
- **Ne PAS déclarer V1 terminée** : schéma personnel source historiquement 7 contre logiciel 13, migration uniquement sur clone distinct, lacunes de données publiques et de normes, validations visuelles/OCR, scheduler OS, confidentialité/durabilité et bug historique `POST_VERIFY_RESIDUE_OR_UNSAFE_FILE` = `CAUSE_NON_RECONSTRUITE`.
- Suite proposée : préparer la transition sûre vers la validation terrain du clone 7→13 en commençant par une **revue technique sur fixtures et des prérequis** ne touchant aucune donnée privée. Aucune création de clone réel, lecture de backup personnel ou migration n'est autorisée par ce constat. Toute opération privée requiert un nouveau mandat et consentement distinct.
- GitHub reste la source de vérité, utilisateur messager entre ChatGPT et Codex, conformément au noyau V2 portable. Aucune surveillance automatique ajoutée.
