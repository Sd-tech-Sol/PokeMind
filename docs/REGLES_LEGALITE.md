# Règles officielles et légalité datée — LOT A

## Ce qui est livré

Le schéma SQLite 6 avait ajouté deux tables publiques et additives :

- `official_rule_sources` : document, URL, langue, publication, consultation,
  capture, empreinte, validation, droits et intervalle d'effet;
- `official_rule_assertions` : rotation, restriction, couverture, équivalence de
  réimpression, politique, délai, promo ou errata, toujours relié à une source.

Le schéma 9 du LOT A ajoute `official_deck_structure_rules`. Chaque version de
règle de construction possède un identifiant, une source officielle, un format et
une plateforme optionnels, une fenêtre d'effet, un payload validé, un statut et un
niveau de confiance. Les anciennes fenêtres et les conflits ne sont pas supprimés.

La migration d'une base existante crée d'abord une sauvegarde cohérente avec
`sqlite3.backup()`. Les tables de volumes/FTS5, catalogue, decks, combats et profil ne
sont ni vidées ni réinterprétées. Le registre public est chargé volontairement par :

```powershell
python -m pokemind rules load-official --json
```

Cette commande et toutes les consultations `rules` sont hors ligne. Le JSON externe
est validé strictement : taille bornée, dates ISO, types connus et URL HTTPS limitée à
`pokemon.com` / `play.pokemon.com`. Il est traité comme donnée, jamais comme code.

## Commandes

```powershell
python -m pokemind rules sources --json
python -m pokemind rules status --json
python -m pokemind rules check-card <tcgdex-id> --format standard --platform live --as-of 2026-10-11 --json
python -m pokemind rules check-deck principal --format standard --platform in_person --as-of 2026-10-11 --json
```

`check-card` exige une impression locale non ambiguë. La réponse donne la juridiction,
le format, la plateforme, la date, `legal` / `not_legal` / `unknown`, la confiance,
les `reason_codes`, les sources et les données manquantes. Les champs séparés
`live_printing_support`, `ownership` et `craftability` restent `unknown` : la légalité
réglementaire ne prouve aucun de ces états.

`check-deck` lit la version la plus récente, sans revenir silencieusement à une
ancienne version confirmée. La réponse expose son identifiant, son numéro,
`exact_confirmed`, le total enregistré, la somme réelle des quantités et un bloc
`structure_validation`. Chaque ligne doit être résolue par code TCG Online + numéro +
nom vers un seul ID TCGdex. Une ligne non résolue ou ambiguë est `unknown`.

Le LOT A évalue maintenant 60 cartes, la somme réelle, les copies regroupées par nom
anglais prouvé, l'exception des Énergies de base, la présence d'un Pokémon de base et
les exceptions/limites spéciales. Le registre réel prouve les règles générales avec
le livret officiel, mais marque volontairement les registres d'exceptions et de
limites spéciales incomplets. Par conséquent, un deck réel ne devient `legal` que si
toutes ces entrées sont explicitement complètes; une violation indépendante et
démontrée (59/61 cartes ou absence certaine de Pokémon de base) peut être
`not_legal`; sinon le résultat demeure `unknown`. Les tests synthétiques démontrent
le chemin `legal` avec un registre complet sans prétendre que le registre réel l'est.
Une carte individuellement `not_legal` reste décisive. Aucun export, association de
combat ou changement de deck n'est effectué.

## Logique conservatrice

1. Une restriction officielle exacte et active produit `not_legal`.
2. Standard exige une rotation unique pour la plateforme et la date.
3. Une marque admissible exige aussi une couverture complète et datée des
   restrictions avant de produire `legal`.
4. Une marque ancienne ou absente exige une équivalence fonctionnelle explicite.
   Même nom ≠ même carte; sans preuve, `unknown` et non `not_legal`.
5. Un délai documenté encore actif produit `not_legal`; le délai « typique » n'est
   jamais calculé sans date officielle propre au produit ou à la promo.
6. Expanded est séparé. L'éligibilité tournoi ne prouve pas le support réel dans
   Live; sans mappage d'identité et liste de restrictions complète, `unknown`.
7. Un conflit, une source absente/obsolète, une date future hors intervalle ou une
   impression manquante donne `unknown`.
8. Une assertion `verified` n'est normative que si sa source jointe est aussi
   `verified` et active à la date demandée. Un registre incohérent est rejeté avant
   toute écriture; les anciennes lignes SQLite incohérentes restent neutralisées à la
   lecture. `navigation_only`, `non_verified` et `conflict` ne peuvent produire ni
   `legal` ni `not_legal`.

Exemples de codes : `MARK_ELIGIBLE`, `RESTRICTIONS_NOT_FULLY_VERIFIED`,
`REPRINT_EQUIVALENCE_UNVERIFIED`, `WAITING_PERIOD_ACTIVE`,
`EXPLICIT_OFFICIAL_RESTRICTION`, `NO_UNIQUE_ACTIVE_ROTATION`,
`EXPANDED_LIVE_SUPPORT_NOT_PROVEN`, `UNVERIFIED_NORMATIVE_SOURCE`,
`CONFLICTING_OFFICIAL_SOURCES`, `DECK_VERSION_UNCONFIRMED`,
`DECK_QUANTITY_SUM_NOT_60` et `DECK_STRUCTURE_NOT_VERIFIED`.

## Couverture réelle au 2026-10-13

- Rotation Standard 2026 : dates Live / présentiel et marques H/I/J vérifiées.
- Politique de réimpressions : principe vérifié; aucune équivalence globale TCGdex.
- Bannissements : trois impressions officielles de Medicham V enregistrées sous
  identité officielle, sans inventer leur alias TCGdex.
- Errata et promos : sources connues, contenu exhaustif non chargé.
- Restrictions Standard : couverture incomplète, donc aucune impression réelle n'est
  faussement déclarée `legal` par le registre livré seul.
- Expanded Live : support incomplet explicitement séparé de la légalité tournoi.
- Structure : le livret officiel Pokémon consulté directement, pages 20–21, prouve
  exactement 60 cartes, quatre cartes du même nom sauf Énergies de base et au moins
  un Pokémon de base. Ses appendices montrent des limites spéciales; le registre
  exhaustif de ces exceptions demeure incomplet et empêche un faux `legal` global.
- Registre versionné : 14 sources, 6 assertions historiques et une règle de
  construction dans le fichier livré. Un `HEAD 200` confirme seulement
  l'accessibilité d'une URL; les deux PDF antérieurement non consultés demeurent
  `non_verified` malgré leur accessibilité réseau.

Les tests utilisent uniquement des IDs et decks synthétiques. Ils couvrent notamment
les versions non confirmées, 59/61 cartes, divergence total/quantités, cinq ou soixante
copies, Énergies de base, absence de Pokémon de base, exception incomplète, conflit,
source non vérifiée, fenêtre d'effet, migration 8→9, backup et rollback. Ils prouvent
les garde-fous du moteur, pas la légalité universelle du catalogue local partiel.
Audit des sources du lot : `docs/LOT_A_SOURCE_AUDIT.md`.
