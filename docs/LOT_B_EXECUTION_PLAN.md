# Plan d'exécution — LOT B

Date d'exécution : 2026-10-13. Branche exclusive :
`work/pm-v1-lotb-personal-deck-advisor`.

## Invariants

- Les données personnelles restent sous `data/local/`, hors Git et hors API.
- Le développement et les tests utilisent uniquement des bases et fichiers synthétiques.
- Les consultations sont hors ligne et en lecture seule. Toute écriture propriétaire
  exige `--apply --confirm-owner`, cible un seul objet logique et conserve un audit.
- Collection, deck joué, cartes observées, crédits, légalité, disponibilité Live et
  coût de fabrication restent des dimensions séparées. Une preuve absente vaut
  `unknown`.
- Aucun deck réel n'est remplacé, aucune partie réelle n'est liée, aucun crédit n'est
  dépensé et aucun compte Pokémon n'est contacté.

## Checkpoints prévus

1. **B0 — sécurité TCGdex.** Partager une allowlist stricte entre URL initiale,
   redirection et URL finale; débiter chaque GET réel avant transmission; couvrir
   quota, boucle, cible interne, cible interdite, 429 et conservation du cache.
2. **B1 — mémoire volontaire.** Ajouter un schéma SQLite additif avec sauvegarde de
   migration pour instantanés de collection et crédits, formats JSON déterministes,
   prévisualisation, application confirmée, historique, couverture, cartes manquantes
   et rollback sans suppression d'audit.
3. **B2/B3 — conseil et leçons.** Composer analyse, résolution TCGdex, règles,
   collection, attestations de version, événements reconnus et méta. Produire faits,
   hypothèses, changements candidats conditionnels, questions et dénominateurs sans
   causalité ou synergie inventée. Les notes validées sont versionnées et idempotentes.
4. **B4 — candidats de 60 cartes.** Construire un candidat distinct du deck joué à
   partir de changements explicitement fournis, valider 60 cartes/sections/identités,
   quotas et Pokémon de base lorsque les preuves le permettent, puis prévisualiser et
   exporter volontairement sous `data/local/` sans créer de version jouée.
5. **B5 — parcours et audit.** Ajouter les commandes et un skill Markdown portable,
   les scénarios E2E synthétiques et le statut de capacité. Rejouer toute la suite,
   compiler, contrôler SQLite/FTS5, confidentialité, secrets et diff; publier la
   matrice d'acceptation et la passation.

Chaque checkpoint devient un commit cohérent récupérable. Les défauts techniques
ordinaires découverts par les tests sont corrigés et retestés dans le lot, sans
transformer une fonction partielle en fonction vérifiée.
