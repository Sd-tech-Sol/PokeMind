# Audit du statut TCGdex absent — PM-0004B-R1

Contrôle ciblé effectué le **2026-10-11**, sans requête réseau réelle et sans
modifier la base locale de l'utilisateur.

## Cause et correction minimale

Après une réponse 404, l'UPSERT d'un bref de carte remplaçait `absent` par
`not_fetched`. De plus, les sélections de détails de cartes et d'extensions
acceptaient `detail_stale=1` sans exclure un statut `absent`. Un refresh pouvait
donc provoquer un nouveau GET sans `--recheck-absent`.

L'UPSERT conserve maintenant `present` **et** `absent`; il ne ramène à
`not_fetched` que les autres états prévus. Les sélections `_pending_card` et
`_pending_set` excluent explicitement `absent` lorsque `recheck_absent=False`,
même si le bref est périmé. Avec `--recheck-absent`, une réponse 200 repasse à
`present` et nettoie l'erreur ainsi que le drapeau d'obsolescence par le flux
existant. Aucune migration SQLite n'est requise.

## Preuves synthétiques

- Cartes et extensions, anglais et français : index, détail 404, refresh avec
  bref identique, puis modifié; le statut demeure `absent` et une phase détails
  sans autorisation émet zéro requête.
- Un recontrôle explicite qui reçoit encore 404 conserve `absent`; un recontrôle
  suivant qui reçoit 200 passe à `present`, remet `stale` à zéro et corrige les
  compteurs de couverture.
- Un détail `present` dont le bref change continue d'être rafraîchi sans
  `--recheck-absent`.
- Les tests existants conservent les scénarios `network_error`, reprise, quotas
  incluant les retries, hôte HTTPS imposé, confidentialité et bases temporaires.

Résultats Codex : `93 passed`, `python -m compileall -q src tests`,
`git diff --check` et `PRAGMA integrity_check=ok`. Ces résultats ne constituent
pas une vérification indépendante.

## Limites

Le correctif ne change ni la découverte, ni la pagination, ni le format des
decks, ni les combats, ni la collection, ni la légalité. Le catalogue local reste
partiel et TCGdex ne prouve pas la disponibilité dans TCG Live. Aucun essai réseau
réel n'était nécessaire pour cette correction de machine à états.
