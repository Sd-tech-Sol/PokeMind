# PM-0005A-R1 — audit des garde-fous de légalité (2026-10-11)

## Portée

Ce correctif ferme uniquement les deux chemins de faux verdict démontrés dans
`.orchestrator/VERIFICATION_PM-0005A.md`. Il n'ajoute ni validateur complet de
construction, ni source externe, ni migration, ni réseau, ni fonction PM-0005B.
Toutes les régressions utilisent des données synthétiques sous le répertoire temporaire
de pytest. La base, le deck, les combats et le catalogue privés restent en lecture
seule et hors Git.

## Défaut 1 — verdict global d'un deck

### Avant

`check_deck` consultait la dernière ligne de `deck_versions` sans exposer
`exact_confirmed`, puis calculait le statut uniquement à partir des verdicts de cartes.
Une seule impression individuellement `legal`, une version de 59 cartes ou 60 copies
identiques pouvaient donc mener à un verdict global `legal` dans un corpus synthétique
avec couverture normative complète.

### Après

La version la plus récente est toujours présentée, y compris lorsqu'elle est non
confirmée; aucune ancienne version confirmée n'est choisie à sa place. La réponse
expose :

- `deck_version_id`, `deck_version` et `exact_confirmed`;
- `total_cards` enregistré et `quantity_sum` réellement lu;
- `structure_validation.status`, ses contrôles et ses `reason_codes`;
- les règles non encore prouvées : quotas et exceptions, Énergies de base, Pokémon de
  base et exceptions de construction datées.

Sans validateur officiel complet, `DECK_STRUCTURE_NOT_VERIFIED` interdit tout verdict
global `legal`. Les incohérences ajoutent des raisons précises :
`DECK_VERSION_UNCONFIRMED`, `DECK_RECORDED_TOTAL_NOT_60`,
`DECK_QUANTITY_SUM_NOT_60` ou `DECK_TOTAL_QUANTITY_MISMATCH`. Une carte prouvée
`not_legal` rend toujours le deck `not_legal`, mais le bloc structurel demeure
`unknown`.

## Défaut 2 — cohérence source et assertion

### Avant

Le chargement validait séparément les valeurs de statut sans interdire une assertion
`verified` liée à une source `navigation_only`, `non_verified` ou `conflict`.
`check_card` filtrait l'assertion, mais pas le statut ni l'intervalle d'effet de sa
source jointe.

### Après

Le registre entier est validé en mémoire avant l'ouverture de SQLite. Toute assertion
`verified` dont la source n'est pas `verified` lève `RulesError`; la version, les
sources, les assertions et les métadonnées déjà présentes restent inchangées.

À la lecture, `check_card` exige simultanément : assertion `verified`, source
`verified`, intervalle de l'assertion actif et intervalle de la source actif. Cette
défense couvre les anciennes bases ou fixtures modifiées directement. Une source
conflictuelle retourne `CONFLICTING_OFFICIAL_SOURCES`; une source non normative,
`UNVERIFIED_NORMATIVE_SOURCE`; une assertion non vérifiée,
`UNVERIFIED_OFFICIAL_ASSERTION`. Le filtrage tient compte du sujet : une assertion
visant une autre impression ne bloque pas artificiellement la carte consultée.

## Contre-exemples et régressions synthétiques

- version non confirmée et version non confirmée plus récente qu'une confirmée;
- total enregistré à 59, somme des quantités à 59 avec total enregistré à 60;
- 60 exemplaires identiques et deck sans Pokémon de base, avec carte individuelle
  délibérément `legal`, mais verdict global toujours `unknown`;
- carte individuelle `not_legal` décisive et entrée non résolue conservée `unknown`;
- lignes et empreintes des versions inchangées après consultation;
- rejet atomique pour rotation, restriction, couverture et équivalence de
  réimpression, croisés avec les trois statuts de source non normatifs;
- mêmes incohérences injectées directement dans SQLite, assertion `non_verified` et
  source expirée avant son assertion;
- cas normaux 2026 préservés : dates Live/présentiel, H/I/J, ancienne marque sans
  équivalence, restriction Expanded, conflits, promo et réimpression explicite.

## Preuves Codex

- baseline : `99 passed`, SQLite schéma 6, registre 13 sources / 6 assertions,
  `PRAGMA integrity_check = ok`;
- final : `128 passed`;
- `python -m compileall -q src tests` et `git diff --check` réussis;
- consultation hors ligne réussie; empreinte de la base privée identique avant/après
  `rules check-deck`; compteurs locaux inchangés;
- aucune requête réseau réelle, migration ou écriture de données privées.

Ces preuves sont produites par Codex et attendent l'audit indépendant ChatGPT. Elles
ne constituent pas un statut `VERIFIED`.

## Limites assumées

Le correctif n'implémente volontairement pas un validateur structurel partiel. Par
conséquent, aucun deck ne reçoit encore un verdict global positif. Les verdicts carte
par carte demeurent disponibles et sourcés. La couverture du registre public et du
catalogue local reste partielle; compatibilité Live, possession et fabrication restent
des dimensions séparées et inconnues.
