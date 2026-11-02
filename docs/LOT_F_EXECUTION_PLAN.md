# Plan d’exécution — GRAND LOT F

Date : 2026-10-14. Branche : `work/pm-v1-lotf-completion-vision`.

Ce plan a été exécuté par Codex sur des données synthétiques et publiques seulement.
Il ne vaut ni audit indépendant, ni autorisation d’agir sur la base personnelle.

| Tranche | Résultat | Preuve principale | Limite conservée |
|---|---|---|---|
| F0 — reprise critique | `DONE_SYNTHETIC` | `test_recovery.py`: course source/manifeste, WAL, verrou, rollback, hash de rétention | aucune restauration/purge personnelle |
| F1 — vision locale | `PARTIAL_WITH_EVIDENCE` | pixels PNG réellement décodés, calibration ROI, provenance interne, mémoire/conseil, occlusion fail-closed | marqueurs synthétiques seulement; aucun essai réel propriétaire |
| F2 — connaissances | `PARTIAL_WITH_EVIDENCE` | micro-campagne TCGdex publique bornée; défaut `exu-?` corrigé; rapports x/y et `unknown` préservés | couverture historique/règles/méta incomplète; Trainer Hill bloqué |
| F3 — produit/CI | `DONE_LOCAL` / `PASS_OBSERVED` | `test_lot_f_e2e.py`, `v1 readiness`; run `38509657380` Windows/Linux vert | ne prouve pas la capacité visuelle réelle |
| F4 — mise en service | `DONE_PLAN_ONLY` | `MISE_EN_SERVICE_PROPRIETAIRE.md` avec portes séparées | aucune action propriétaire exécutée |
| F5 — clôture | `DONE_DOCUMENTATION` | matrice LOT F, readiness, RESULT/HANDOFF/NEXT_ACTION/ROADMAP/DECISIONS | V1 `NOT_RELEASE_READY` |

## Séquence réalisée

1. F0 a précédé toute autre modification : la source et son manifeste sont attestés
   sous verrou immédiatement avant publication; les cibles WAL/SHM ou verrouillées
   sont refusées; le target antérieur est rétabli si la validation publiée échoue.
2. La rétention recalcule un inventaire de sauvegardes réellement vérifiées, lie le
   plan aux SHA/mtime/file-id, revalide sous verrou et met fichier+manifeste en zone
   de transit avec rollback avant effacement.
3. F1 ajoute un adaptateur standard-library sans installation. Il décode réellement
   RGB/RGBA PNG 8 bits, mesure chaque ROI et n’accorde `visual_certain` que par la
   voie interne calibrée. Une annotation JSON demeure incapable de forger ce statut.
4. F2 a exécuté une campagne publique jetable et bornée. Deux pages EN/FR ont
   produit 221 sets distincts; un identifiant TCGdex réservé a révélé un défaut,
   corrigé puis revalidé par un GET public de 100 cartes EN. Rien n’a été conservé.
5. F3 compose un rapport offline unique sans nom de backup, chemin, montant ni carte
   privée. Le E2E traverse vision → mémoire → backup → restore → readiness.

## Conditions de clôture

Le mécanisme F0 est prêt pour audit de code et tests, pas pour exécution personnelle
implicite. La vision réelle d’une capture du jeu, les données propriétaire, le
scheduler et les couvertures publiques complètes exigent encore consentements ou
preuves externes. Aucun objectif n’est supprimé : ils passent à G+.
