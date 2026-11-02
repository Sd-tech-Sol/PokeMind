# PokeMind — démarrage local

PokeMind est un projet actif, encore en V1. Il consulte localement des volumes
stratégiques, un catalogue public TCGdex, des règles Pokémon officielles et de petits
instantanés publics Limitless. Les mécanismes des LOTS A à D sont livrés avec leurs
limites; le LOT D attend l’audit indépendant. LOT E reste obligatoire.

## Installation sous Windows 11

Depuis la racine du dépôt privé :

```powershell
python -m pip install --no-index --no-build-isolation -e .
python -m pokemind import-seed
python -m pokemind knowledge status --json
```

Une ancienne base est migrée seulement par une commande d'écriture explicite, avec
sauvegarde SQLite préalable. `knowledge status` et `knowledge audit` demeurent en
lecture seule et signalent plutôt `MIGRATE_WITH_BACKUP`.

## Poser une question à Codex

Demander `$knowledge cherche cette carte`, `$knowledge explique son effet`,
`$knowledge quelles réimpressions sont vérifiées?`, `$knowledge est-elle légale
Standard Live au 2026-10-13?` ou `$knowledge montre le métagame de cet archétype`.
Le skill de projet utilise seulement le cache local pendant la consultation, cite la
source et la date et conserve les inconnues.

Une synchronisation publique n'est jamais implicite. Elle exige une commande et un
budget borné. Ne pas mettre dans Git ni envoyer à une API la base, un deck, une
collection, des crédits, un journal, une capture, une clé HMAC ou un identifiant.

Prévisualiser l’updater sans réseau ni écriture :

```powershell
python -m pokemind knowledge update --mode daily --dry-run --json
python -m pokemind knowledge update status --json
```

La réconciliation mardi/vendredi exige une heure Toronto choisie. Le planificateur
Windows n’est pas installé : `knowledge scheduler ... --dry-run` ne fait que rendre
la configuration, et toute tentative réelle est bloquée pendant LOT D.

## État et limites

- Catalogue historique complet : cible conservée, couverture réelle partielle tant
  que les scans FR/EN et détails ne sont pas terminés.
- Réimpressions, exceptions de construction, restrictions, promos et errata : seules
  les assertions officielles vérifiées peuvent produire un verdict; sinon `unknown`.
- Métagame : échantillon public Limitless filtré, jamais le métagame mondial.
- Trainer Hill : bloqué faute d'accès public automatisable vérifié; aucun scraping.
- Vision locale réelle, couverture publique exhaustive, Trainer Hill et stabilisation
  finale restent partiels ou futurs. Aucun scheduler, merge ou action TCG Live n'est
  installé ici.

Après chaque lot, ChatGPT effectue l'audit indépendant depuis GitHub. Une annonce de
Codex n'est pas une validation `VERIFIED`.
