# Plan d’exécution — LOT C

Date d’exécution : 2026-10-13. Branche :
`work/pm-v1-lotc-visual-training-coach`.

Le lot reste local, hors ligne et réservé aux entraînements où l’assistance est
permise. Les essais utilisent uniquement des bases et images synthétiques sous
`data/local/test-runs`. Aucune capture réelle, donnée de compte ou interaction avec
Pokémon TCG Live n’est utilisée.

## C0 — réserves du LOT B

- Sélection historique des collections et crédits selon la date d’observation **et**
  la date locale de création de l’instantané. Une preuve créée plus tard retourne
  `NOT_AVAILABLE_AS_OF`; la succession et les rollbacks sont rejoués sans prendre
  le statut actif actuel comme raccourci.
- `recommend deck --as-of` transmet la borne aux trois lectures collection/crédits.
- La validation des candidats n’impose plus artificiellement une section Dresseur
  ou Énergie. L’obligation d’un Pokémon de base dépend d’une règle officielle active.
- La catégorie déclarée est comparée à la catégorie publique de l’impression exacte.
  Une contradiction sourcée est rejetée; une catégorie absente ou conflictuelle
  demeure `UNKNOWN_LEGALITY`.
- Preuve ciblée initiale : `25 passed` dans `test_collection.py`,
  `test_recommendations.py` et `test_candidates.py`.

## C1 — image locale éphémère

Valider chemin privé, absence de lien symbolique/traversée, extension, signature,
taille en octets, dimensions, pixels et orientation. Ne conserver ni chemin, ni
octets, ni empreinte dans la réponse publique ou SQLite. Le mode est explicitement
`training`; aucune capture automatique ou suppression du fichier propriétaire.

## C2 — état observable prudent

Définir un contrat versionné pour les deux côtés, actif/banc, ressources visibles,
main, défausse, Récompenses, tour, phase, inconnues et erreurs. Accepter une
annotation JSON locale réconciliable. Un backend visuel local absent doit retourner
`NEEDS_MANUAL_ANNOTATION`, jamais un plateau inventé.

## C3 — mémoire textuelle multi-tours

Ajouter un schéma SQLite additif pour séances, observations, corrections et
révocations. Prévisualisation sans migration; écriture seulement avec `--apply
--confirm-owner`. Dédupliquer une observation identique, isoler les séances et ne
jamais stocker de pixels ou de chemin de capture.

## C4 — conseil conditionnel

Produire options `verified_possible`, `conditional` ou `not_supported`, avec ordre,
conditions, compromis, preuves publiques disponibles et prochaine annotation
minimale. Aucun meilleur coup absolu, taux de victoire ou action automatisée.

## C5 — parcours et audit

Assembler la CLI et le skill portable, couvrir l’E2E synthétique, mettre à jour le
guide, la matrice et les fichiers d’orchestration. Terminer par suite complète,
compilation, diff, intégrité/FTS5, contrôle des fichiers suivis et des secrets, puis
push sur la branche du lot et arrêt pour audit indépendant.

## Résultat d’exécution

C0, C1 et C3 sont `DONE`. C2, C4 et C5 sont `PARTIAL_WITH_EVIDENCE` : le contrat,
le repli manuel, le conseil conditionnel et l’E2E sont démontrés, mais aucun backend
local de vision fiable n’est installé et le mandat interdit une vraie capture pendant
le développement. La matrice `LOT_C_ACCEPTANCE_MATRIX.md` porte les preuves finales.
