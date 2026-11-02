# PM-0006A-R1 — audit d'exécution Codex

Date : 2026-10-12

Branche : `work/pm-0006a-r1-temporal-redaction`

Statut : livré par Codex, en attente d'audit indépendant ChatGPT; aucune revendication
`VERIFIED`.

## Corrections bornées

1. Le diagnostic historique Limitless compare deux dates distinctes :
   `date_utc <= as_of` pour la date de l'événement et `fetched_at <= as_of` pour la
   disponibilité réelle du snapshot dans le cache local. Un tournoi du 1er mai
   capturé le 1er juin ne contribue pas au diagnostic du 15 mai, mais redevient
   admissible au 2 juin. `fetched_at` est une date locale de capture, pas une preuve
   de la date officielle de publication.
2. La dernière version du deck demeure sélectionnée. Si son `effective_from` est
   postérieur à `as_of`, ses faits statiques restent visibles avec
   `historical_applicability=not_applicable`, mais les règles restent `unknown` et
   aucun combat antérieur ne compte comme preuve de cette version. Aucune ancienne
   version n'est substituée.
3. Les erreurs catalogue/règles utilisent des messages fixes. Aucun `str(exc)` n'est
   recopié dans `unknowns`, en JSON ou en humain.

## Preuves synthétiques

- Snapshot : événement `2026-05-01`, capture `2026-06-01`, zéro tournoi au
  `2026-05-15`, deux tournois Live admissibles au `2026-06-02`; contexte physique
  séparé, événement futur exclu et date `as_of` invalide refusée.
- Version future : une impression synthétique explicitement interdite produit bien
  `not_legal` dans le moteur normatif isolé, mais `analyze deck` retourne `unknown`
  pour le contexte antérieur avec `LATEST_VERSION_OUTSIDE_AS_OF`; une liaison de
  combat antérieure reste non applicable.
- Confidentialité : exceptions artificielles contenant un chemin Windows, un token
  et un nom de carte synthétique; aucune chaîne ni sous-chaîne privée dans les sorties
  JSON ou humaines.
- Lecture seule : les tests existants conservent la vérification byte-à-byte des bases
  synthétiques; aucune migration, écriture applicative ou requête HTTP ajoutée au
  chemin `analyze deck`.

## Vérifications Codex

- Baseline avant correction : `181 passed`.
- Final : `185 passed`.
- `python -m compileall -q src tests` : réussi.
- `git diff --check` : réussi.
- SQLite privée : schéma 7 et `PRAGMA integrity_check=ok`; empreinte vérifiée
  inchangée sans la publier.
- Audit Git : aucun fichier SQLite, journal, image ou donnée sous `data/local/` suivi.

## Limites

Le filtre `fetched_at` prévient la connaissance future à partir du cache, mais ne
reconstruit pas une date officielle de publication. Les résultats Limitless restent
des observations descriptives. Ce correctif ne complète ni le catalogue, ni les
règles de construction, ni l'inventaire, et ne produit aucune recommandation,
estimation de crédits ou action dans Pokémon TCG Live.
