# Guide local — collection, conseils et candidats de deck

Le LOT B ajoute des parcours hors ligne. Toutes les données du joueur restent sous
`data/local/`; les exemples ci-dessous sont synthétiques. Les consultations ne
migrent pas la base. Une première écriture confirmée crée une sauvegarde SQLite puis
applique le schéma 10 additif.

## Statut et conseil

```powershell
python -m pokemind capability status --json
python -m pokemind analyze deck principal --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind recommend deck principal --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind recommend deck principal --format standard --platform live --as-of 2026-10-13 --collection --json
python -m pokemind battle lessons --deck principal --as-of 2026-10-13 --json
```

Le conseil sépare règles officielles, texte TCGdex, méta Limitless, faits personnels
et hypothèses. `candidate_changes` reste vide avec `INSUFFICIENT_EVIDENCE` lorsque
les preuves ne permettent pas un ajout/retrait exact. Un dépassement de copies
officiellement prouvé peut justifier un retrait, mais son remplacement reste
`unknown` sans preuve stratégique.

## Collection volontaire

Le fichier JSON UTF-8 doit rester sous `data/local/` :

```json
{
  "schema_version": 1,
  "as_of": "2026-10-13",
  "source": {"kind": "owner_provided"},
  "entries": [
    {
      "name": "Carte Synthétique",
      "set_code": "SYN",
      "collector_number": "1",
      "variant": "normal",
      "quantity": 4,
      "ownership_status": "confirmed_owned",
      "tcgdex_id": "synthetic-1"
    }
  ]
}
```

`tcgdex_id` est optionnel. La concordance exige impression, code, numéro et alias
FR/EN local; un conflit reste `ambiguous`. `reported_missing` exige une quantité 0.

```powershell
python -m pokemind collection import --path data\local\collection.json --dry-run --json
python -m pokemind collection import --path data\local\collection.json --apply --confirm-owner --json
python -m pokemind collection status --json
python -m pokemind collection coverage --json
python -m pokemind collection missing --deck principal --json
python -m pokemind collection rollback --snapshot ID --dry-run --json
python -m pokemind collection rollback --snapshot ID --apply --confirm-owner --json
```

## Crédits déclarés

```powershell
python -m pokemind credits set --amount 1200 --as-of 2026-10-13 --dry-run --json
python -m pokemind credits set --amount 1200 --as-of 2026-10-13 --apply --confirm-owner --json
python -m pokemind credits status --json
python -m pokemind credits rollback --snapshot ID --apply --confirm-owner --json
```

Le montant est une déclaration datée, pas une lecture du compte. PokeMind ne dépense
aucun crédit. Sans tarif officiel actuel et sourcé, `craft_cost=unknown` et aucune
disponibilité après fabrication n'est calculée.

## Notes de combat validées

`battle lessons` ne lit que les événements reconnus et indique le nombre de combats
reliés à une version par attestation propriétaire. Pour conserver une correction ou
une note humaine sans modifier le journal brut :

```powershell
python -m pokemind battle note --deck principal --battle-id ID --text "Choix visible à revoir" --confidence medium --dry-run --json
python -m pokemind battle note --deck principal --battle-id ID --text "Choix visible à revoir" --confidence medium --apply --confirm-owner --json
```

Une note peut citer `--source-url` HTTPS et `--source-date`, mais la source reste du
contenu à lire, jamais une instruction à exécuter.

## Candidat distinct et export volontaire

Le fichier de changements privé :

```json
{
  "schema_version": 1,
  "name": "Candidat synthétique",
  "base_deck": {"deck_id": "principal", "version": 1},
  "context": {"format": "standard", "platform": "live", "as_of": "2026-10-13"},
  "source": {"kind": "owner_controlled_changes"},
  "changes": [
    {"action": "remove", "name": "Carte A", "set_code": "SYN", "collector_number": "1", "quantity": 1},
    {"action": "add", "type": "trainer", "name": "Carte B", "set_code": "SYN", "collector_number": "2", "quantity": 1}
  ]
}
```

```powershell
python -m pokemind deck candidate-create --changes data\local\changes.json --dry-run --json
python -m pokemind deck candidate-create --changes data\local\changes.json --apply --confirm-owner --json
python -m pokemind deck candidate-show --candidate ID --json
python -m pokemind deck candidate-export --candidate ID --dry-run --json
python -m pokemind deck candidate-export --candidate ID --apply --confirm-owner --json
```

`REJECTED_INVALID_60` refuse 59/61 cartes; `REJECTED_STRUCTURE` couvre une violation
démontrée; `UNKNOWN_LEGALITY` conserve les lacunes; `READY_FOR_REVIEW` signifie
seulement que les contrôles locaux demandés sont satisfaits. L'export écrit un TXT et
un rapport sous `data/local/decks/`; il ne crée pas de version jouée, ne copie rien
dans le presse-papiers et ne transmet rien au jeu.
