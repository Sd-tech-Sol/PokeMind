# PM-0006C — attestations manuelles combat ↔ version

## Contrat livré

PokeMind peut maintenant prévisualiser puis enregistrer la déclaration explicite du
propriétaire qu'un combat local précis a utilisé une version exacte de 60 cartes.
La déclaration est un fait d'audit `owner_asserted`, jamais une preuve externe. Elle
ne démontre ni légalité, ni support TCG Live, ni possession, ni taux prédictif.

Les commandes restent locales et hors ligne :

```powershell
python -m pokemind deck link-candidates --deck principal --json
python -m pokemind deck link-battle --deck principal --battle-id ID --version 1 --dry-run --json
python -m pokemind deck link-battle --deck principal --battle-id ID --version 1 --apply --confirm-owner --json
python -m pokemind deck unlink-battle --deck principal --battle-id ID --dry-run --json
python -m pokemind deck unlink-battle --deck principal --battle-id ID --apply --confirm-owner --json
```

L'absence de `--apply` équivaut à une prévisualisation. `--apply` sans
`--confirm-owner` est refusé. Chaque appel cible une seule paire; aucune commande
`--all` n'existe. Les `battle-id` sont des clés SQLite stables sur la base locale,
pas des identifiants à publier. La liste n'affiche ni adversaire, journal, empreinte,
chemin ni contenu des 60 cartes.

## Schéma et transaction

Le schéma SQLite 8 ajoute `battle_version_attestations`, séparée de
`battle_deck_versions`. `effective_from` et `approved_at` gardent leur sens de dates
de version; `confirmed_at` est l'heure UTC réelle de la confirmation humaine.
L'audit conserve : combat, version, acteur normalisé
`owner_explicit_confirmation`, provenance `owner_asserted`, date réelle de partie
optionnelle, état actif/révoqué, `revoked_at` et motifs normalisés.

Un index partiel impose au plus une attestation active par combat. Sous
`BEGIN IMMEDIATE`, l'application revérifie que :

- le combat existe, est valide et déclare le même `deck_id`;
- la version appartient au deck, est confirmée et cohérente à 60/60;
- aucun lien ou attestation active contradictoire n'existe;
- un lien legacy non attesté n'est jamais écrasé.

Une confirmation identique est idempotente. Changer de version exige d'abord une
révocation distincte. La révocation horodate la ligne d'audit, la conserve et retire
seulement le lien actif appartenant à cette attestation. Elle refuse de supprimer un
lien legacy.

La migration 7→8 crée d'abord une sauvegarde cohérente avec `sqlite3.backup()`, puis
crée table et index dans une transaction. Une prévisualisation sur schéma 7 ouvre la
base en lecture seule : aucune initialisation, migration, sauvegarde ou écriture.

## Temps et provenance

`deck version-evidence` distingue maintenant `unlinked`,
`legacy_explicit_link_unattested`, `owner_attested_active`,
`owner_attested_revoked`, `conflict` et `temporal_unknown`. Une attestation confirmée
aujourd'hui ne compte jamais dans un `--as-of` antérieur. Après révocation, son ancien
résultat n'est plus attribué au diagnostic courant; l'audit demeure visible.

`analyze deck` expose séparément les liens propriétaire et legacy. Si la date réelle
de partie est inconnue, elle reste `unknown`. Une date déclarée antérieure à l'import
de la version n'est pas rejetée par simple comparaison de timestamps : la preuve est
la déclaration du propriétaire, non une inférence de date. La granularité historique
de `--as-of` reste la journée ISO; confirmation et révocation le même jour sont donc
présentées selon l'état révoqué à cette date.

## Validation synthétique

Les tests n'utilisent que des bases sous `data/local/test-runs`. Ils couvrent
prévisualisation byte-for-byte, refus sans confirmation, idempotence, faux IDs,
autre deck, combat invalide, versions inexactes ou non 60/60, lien legacy, deux
confirmations concurrentes incompatibles, révocation, lecture historique, JSON/texte,
caviardage et absence de réseau. La migration synthétique conserve quatre documents
et leur FTS5, cinq combats, decks, catalogue, règles et méta; sa sauvegarde schéma 7
est restaurée et contrôlée, et un échec simulé démontre le rollback.

PM-0006C n'a appliqué, révoqué, importé ni réanalysé aucun combat réel. L'usage sur
une donnée privée exige une action ultérieure du propriétaire, paire par paire.
