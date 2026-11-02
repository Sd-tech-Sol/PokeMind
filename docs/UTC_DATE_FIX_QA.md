# PM-V1-UTC-DATE-001 — preuve synthétique du correctif UTC/local

Rapport d'exécution Codex, audit indépendant ChatGPT requis. Branche
`work/pm-v1-lotj-final-readiness-windows`. V1 `NOT_RELEASE_READY`.
Exécution commencée le 2026-10-17 Québec et terminée le 2026-10-18 Québec.

## Départ et reproduction

Arbre initial propre; fetch puis pull ff-only, sans perte de travail local, de
`c243cd4140610c31154139462a0d57e1700fc954` vers
`eeb477bfa3a9cbe03759e9c8b091a65fe3932bcf`. STATE et premier NEXT_ACTION :
`PM-V1-UTC-DATE-001 / READY`, lancement explicite du propriétaire reçu.
[CI initiale 39094542951](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39094542951)
vérifiée avant développement au SHA complet : Windows 480 pass/2 skip, Ubuntu
hérité 479 pass/3 skip; deux jobs completed/success et logs ci_evidence concordants.

Avant modification du produit, le nouveau test déterministe
`winter-utc-tomorrow` échoue avec `DEMO_CLI_STEP_FAILED:recommend` : **1 failed
en 8,08 s**, arrêt au premier échec attendu. Instant simulé
`2026-01-16T00:30:00+00:00`, date de Toronto `2026-01-15`. L'ancienne démo
transmet `2026-01-16` à la vraie CLI de recommandation, dont la collection refuse
le lendemain local. Cela reproduit le défaut décrit dans
`docs/BACKUP_RESIDUE_FIX_QA.md`, sans rapport avec une sauvegarde réelle.

## Correctif et couverture

Seul changement produit : `src/pokemind/demo.py` choisit `date.today()` au moment
de lancer la recommandation, conformément à la validation locale collection/crédits.
`collection._strict_date` est inchangé et continue de refuser les dates futures.
Les autres dates de la démo restent inchangées : les leçons filtrent les imports
horodatés en UTC et doivent encore retrouver les trois combats synthétiques.
La recommandation conserve ses restrictions de preuve historique lorsque des
imports UTC sont postérieurs au jour local. Aucun horodatage stocké n'est réécrit.

`tests/test_demo_dates.py` exécute quatre répétitions complètes de la démo :

| Instant UTC simulé | Date Toronto attendue | Décalage | Cas |
| --- | --- | --- | --- |
| 2026-01-16 00:30 | 2026-01-15 | UTC−5 | UTC au lendemain local, hiver |
| 2026-01-16 05:01 | 2026-01-16 | UTC−5 | Minuit local passé, hiver |
| 2026-07-16 00:30 | 2026-07-15 | UTC−4 | UTC au lendemain local, été |
| 2026-07-16 04:01 | 2026-07-16 | UTC−4 | Minuit local passé, été |

Les tests utilisent la zone Toronto portable existante pour calculer la date
attendue. Les horloges sont remplacées dans le test et ses vrais processus CLI
enfants avant import de la CLI : horodatage UTC des écritures synthétiques et
date locale du validateur. Aucun réglage d'OS, variable TZ ou mécanisme d'horloge
ajouté au produit. Les accès réseau sont bloqués dans le parent et les enfants.

Chaque cas exige : vraie validation acceptant le jour local et refusant le
lendemain, date locale effectivement transmise à recommend, parcours complet
réussi, trois combats visibles, conflit de contexte coach refusé, processus CLI
distincts, une seule base explicitement synthétique, espace temporaire retiré,
aucun accès propriétaire/OCR réel/planificateur. Le test E2E ordinaire reste
exécuté aussi avec les horloges réelles et la CLI habituelle.

## Validation Windows locale

- Prévol : `RUNTIME_READY`, Python 3.13.15, SQLite 3.50.4, FTS5 présent;
  aucune base propriétaire ouverte, aucun réseau, aucune installation.
- Tests ciblés démo/dates/collection : **19 passed en 68,14 s**.
- Suite complète : **483 passed, 3 skipped en 189,43 s**, zéro échec.
- Skips : deux essais OCR réels sans moteur attesté/opt-in; un test de lien
  symbolique Windows sans privilège. Le test de jonction Windows synthétique passe.
- Compilation `src tests scripts`, hygiène Git et `git diff --check` réussis.
- Environnement local de test : aucune variable TZ définie; aucun passage forcé
  en UTC pour masquer le problème. Aucun paquet installé.

Commandes de preuve (répertoires générés synthétiques seulement) :

```powershell
$env:POKEMIND_TEST_OFFLINE = '1'
python -B -m pytest -q tests/test_demo_dates.py -x # avant correctif : échec attendu
python -B -m pytest -q tests/test_demo_dates.py tests/test_lot_i_e2e.py tests/test_collection.py
python -B -m pytest -q
python -m compileall -q src tests scripts
python -B scripts/check_repo_hygiene.py
git diff --check
```

## Livraison et limites

Code, tests et rapports assainis seulement; aucune donnée personnelle consultée
ou publiée. Aucune base personnelle, sauvegarde existante ou migration personnelle
touchée. Aucun changement aux migrations, règles datées, scheduler ou workflow CI.
Les tests hérités de récupération restent limités aux fixtures synthétiques.

CI du commit de livraison : **PENDING_CI à la publication**. Résoudre son SHA
depuis la branche distante et lire les deux jobs Windows/Ubuntu héritée et leurs
logs ci_evidence au SHA exact; la CI du départ ne la remplace pas. Les résultats
finaux demeurent consultables directement dans GitHub Actions à ce SHA.

`AWAITING_AUDIT / NOT_VERIFIED` par l'exécuteur, puis **STOP audit indépendant
ChatGPT**. Ce correctif ne ferme pas les autres portes V1 et ne réactive aucune
autorisation de backup, clone/migration, OCR ou planificateur.
