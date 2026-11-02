# VERIFICATION_PM-0006B — audit indépendant ChatGPT (2026-10-12)

## Verdict
**PM-0006B ACCEPTÉE EN REVUE STATIQUE INDÉPENDANTE POUR SA PORTÉE.** Les commandes de comparaison d'exports et d'audit des liens combat→version sont implémentées, sans écriture et sans accès réseau sur leur chemin d'exécution. Ce verdict n'est pas une attestation que la SQLite réelle a été directement examinée par ChatGPT ni que les tests de Codex ont été relancés indépendamment.

## GitHub examiné
- Repo privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0006b-version-evidence`, commit fonctionnel Codex **`2093bf695f53c876cbafe375f39d34922fe78769`**, parent d'orchestration `9b0536cedb5461545efbdc4b532ce33510933451`.
- **1 commit d'avance, 0 de retard, 8 fichiers modifiés/ajoutés.** Code `src/pokemind/version_evidence.py` (801 lignes), CLI et `tests/test_version_evidence.py` (494 lignes), README et documents examinés directement.
- Arbre Git complet **132 entrées, truncated=false**, aucun fichier `data/local` privé, SQLite, vraie decklist, journal personnel, capture, backup ou secret détecté dans les chemins suivis. Cela ne constitue pas une vérification du contenu complet de chaque donnée hors Git.
- Le fournisseur GitHub retourne **0 statut CI et 0 workflow PR** au commit. `185 passed` au prévol, **`203 passed`** à la livraison, `compileall`, `git diff --check`, intégrité schéma SQLite 7 et conservation byte-for-byte de la base personnelle sont **rapportés par Codex uniquement**.
- Codex rapporte qu'il y a **une seule version réelle exacte et cinq combats valides, sans aucun lien explicite combat-version**. Ces chiffres proviennent de l'exécution Codex sur la machine locale; ChatGPT ne les a pas obtenus de la SQLite.

## Comparaison : conforme
1. `compare_deck_versions` exige deux numéros explicites, du même `deck_id`, distincts, tous deux confirmés, avec exactement 60 cartes, somme concordante, lignes et dates valides. Une seule version rend `INSUFFICIENT_DECK_VERSIONS`; un numéro absent/étranger ne provoque pas de substitution.
2. La clé de comparaison `card_type + set_code + collector_number + card_name` après normalisation Unicode NFC/casse/espaces conserve les différentes impressions et ne présume pas d'équivalence de réimpressions. Un changement d'ordre seul ne produit aucune différence; les ajouts/retraits/changements de quantité compensent `delta_total=0` entre deux versions valides. Toute identité sans set ou numéro est signalée `IDENTITY_UNCERTAIN`.
3. Le rapport par défaut ne contient que des agrégats, des dénominateurs et des références de versions. Les véritables noms de carte/changements ne sont émis que sur `--show-changes` explicitement demandé avec avertissement local. Aucune exportation ni mutation n'a été ajoutée.

## Audit des liens combat→version : conforme à sa définition
1. `version_evidence` relit `battle_logs` et `battle_deck_versions`, dédoublonne les journaux valides par source_sha256 sans afficher le hash, contrôle deck/version lié, exactitude 60/60, cohérence des dates stockées et disponibilité avant `as_of`. Un `battle_logs.deck_id` seul **n'est jamais une preuve d'une version**.
2. Sépare les liens explicites cohérents, parties sans lien, conflits vers un autre deck, versions non exactes, dates douteuses, évènements incohérents, issues W/L/nul/ambigu et dénominateurs. Les listes à confirmer sont de simples références opaques et dates d'import locales; aucune attribution automatique. Les cinq parties sans lien donnent zéro succès attribué à une version, indépendamment de W/L.
3. Une date d'import n'est pas nécessairement la date réelle d'un match : une liaison existante cohérente en SQLite ne constitue pas une preuve externe cryptographique. Le moteur affiche cette limite et **ne calcule pas de taux prédictif** ni une comparaison des performances de versions.

## Confidentialité, périmètre, réserves
- Les deux fonctions ouvrent `connect_readonly`, `PRAGMA query_only=ON`, gèrent base absente/schéma manquant et caviardent les exceptions `sqlite3.DatabaseError` dans les rapports. Tests d'absence de réseau, sorties JSON/humaines et empreinte DB identique inclus.
- Le gestionnaire d'erreurs CLI global utilise toujours un `str(exc)` sur certaines autres commandes; cette voie générale constitue une amélioration future possible et ne doit pas être présentée comme un audit de confidentialité universel.
- `--as-of` et les dates de jeu restent bornés par dates d'import locales, faute de date réelle de partie fiable. Un lien préexistant ne garantit pas que le propriétaire ait confirmé la version réellement jouée; **aucune nouvelle liaison** n'est produite pendant cette tranche.
- Il n'y a encore ni preuve de légalité globale complète, ni collection/crédits à jour, ni métagame avec archétypes fiables correspondant au deck local. Aucune recommandation d'achat, score de rendement ou meilleure version ne doit en être inférée.
- **Pas de merge**, de changement default branch, de scheduler Windows, d'interaction avec Pokémon, de dépense de crédits ni de modification par ChatGPT des données privées.

## Suite permise par le feu vert durable
Préparer **PM-0006C**, outil de confirmation **manuelle, explicite, locale et révocable** des liens combat↔version avec horodatage de l'attestation et conservation de l'historique; ne jamais importer ni attribuer automatiquement les cinq parties historiques. Aucun effet sur le deck ni les résultats, aucun accès réseau. Cette nouvelle capacité devra être livrée/testée sans l'exécuter sur les vraies parties tant que le propriétaire n'a pas confirmé chaque liaison au moment de l'utilisation. Si l'on ne peut maintenir une provenance datée et une annulation sûre, préparer d'abord une conception/documentation, sans mutation.
