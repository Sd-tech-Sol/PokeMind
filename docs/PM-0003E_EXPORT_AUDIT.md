# Audit PM-0003E — sortie de decks pour Pokémon TCG Live (2026-10-10)

## Conclusion et niveau de preuve

PM-0003E fournit le pont local `deck → texte` et le format de candidat réutilisable.
Le sérialiseur est vérifié par aller-retour interne et par tests synthétiques, mais
aucun vrai deck de l'utilisateur n'était importé dans SQLite et aucun aller-retour
dans le client n'a été autorisé. Le statut demeure donc
**`OUTPUT_FORMAT_NOT_FIELD_VALIDATED`**. Un fichier placé dans `import_ready` signifie
« 60 cartes et identités d'impression complètes, prêt à essayer », pas « accepté par
le client, légal, possédé ou fabricable ».

## Audit du format

Sources consultées le 2026-10-10 :

- Pokémon.com, *Pokémon Trading Card Game Live Starter Deck Strategies—March 2025* :
  sections `Pokémon`, `Trainers`, `Energy` et lignes `quantité nom code numéro`;
  <https://www.pokemon.com/us/features/pokemon-trading-card-game-live-starter-deck-strategies-march-2025>.
- Pokémon.com, anciennes listes copiables : bannières historiques, sections
  `Pokémon - N`, `Trainer Cards - N`, `Energy Cards - N` et `Total Cards - 60`;
  <https://www.pokemon.com/us/strategy/shake-up-your-deck-with-sun-moon-lost-thunder>.
- Forum officiel Pokémon, signalement communautaire non normatif de décembre 2024 :
  certains exports Live comptent les intitulés distincts dans les en-têtes plutôt
  que les quantités; <https://community.pokemon.com/en-us/discussion/15230/decklist-export-incorrectly-lists-counts>.

Les pages officielles démontrent la structure, mais ne constituent pas une
spécification versionnée de l'import presse-papiers 2026. Par prudence :

1. le parseur accepte uniformément les en-têtes qui comptent les quantités **ou**
   les entrées distinctes;
2. le sérialiseur PM-0003E émet les nombres d'entrées distinctes, les trois sections
   et `Total Cards: 60`;
3. chaque ligne conserve le nom Unicode, le code d'extension et le numéro exacts;
4. deux impressions du même nom restent deux lignes;
5. aucun ID, set, nom, statut de rotation ou coût n'est inventé.

## Commandes et sorties privées

```powershell
python -m pokemind deck export principal --json
python -m pokemind deck prepare --proposal data\local\decks\proposals\candidat.json --json
python -m pokemind deck export principal --copy --json
python -m pokemind deck copy data\local\decks\import_ready\principal_v1.txt --json
```

`--copy` est une action explicite. Le texte passe par l'entrée standard d'une
commande PowerShell fixe; il n'est jamais interpolé dans une commande. Le `.txt`
contient uniquement le texte destiné à TCG Live. Le `.json` adjacent contient le
statut, la provenance, 60/60, la couverture des codes d'impression, les
avertissements, `possession: unknown` et `availability: not_verified`.

Les noms sûrs sont dérivés localement. Les écritures utilisent un temporaire dans le
même dossier, puis un lien atomique qui échoue si la cible existe; aucune sortie
existante n'est remplacée. Une proposition CLI doit rester sous `data/local`, et
`deck copy` accepte seulement un `.txt` résolu sous `data/local/decks/import_ready`.

## Schéma JSON de proposition, version 1

Le document est UTF-8, limité en taille et refuse les champs inconnus. Tous les
objets `cards` sont requis; la somme des quantités doit être exactement 60 et les
trois types doivent être présents au moment de sérialiser.

```json
{
  "schema_version": 1,
  "name": "candidat-local",
  "source": {
    "kind": "agent_proposal",
    "reference": "référence locale ou source datée"
  },
  "verification_tags": ["human_review_pending"],
  "cards": [
    {
      "type": "pokemon",
      "quantity": 4,
      "name": "Nom exact Unicode",
      "set_code": "SET",
      "collector_number": "001",
      "provenance": "source locale ou publique vérifiée",
      "verification_tags": ["printing_verified"]
    }
  ]
}
```

Types permis : `pokemon`, `trainer`, `energy`. `set_code` et `collector_number`
sont fournis ensemble ou tous deux absents. Une absence, ou l'absence de l'étiquette
`printing_verified`, produit `DRAFT_PRINTINGS_UNRESOLVED` sous `drafts`; une liste
complète et ainsi vérifiée produit `READY_TO_TRY_UNVERIFIED_FORMAT` sous
`import_ready`. Un candidat d'agent ne devient
pas une version confirmée du joueur et n'est pas ajouté à SQLite par cette commande.

## Vérifications automatisées

- aller-retour `parse(serialize(deck))`, réexport identique et 60/60;
- conventions d'en-têtes quantités et entrées;
- Unicode français/anglais, apostrophes, énergies et impressions distinctes;
- refus des totaux 59/61, champs JSON inconnus et identités partielles;
- brouillon hors `import_ready`, collision sans écrasement et nettoyage en erreur;
- copie simulée, texte transmis seulement par stdin, traversée de chemin refusée;
- aucune donnée utilisateur, sortie privée ou liste réelle ajoutée au dépôt.

## Limites et test terrain restant

Le premier test terrain devra suivre : export TCG Live volontaire → import PokeMind
→ génération `.txt` → copie explicite → import TCG Live. Il sera non destructif et
ne devra ni publier le deck ni déclencher « Exchange All ». Jusqu'à cette preuve,
le client vérifie lui-même format, légalité, disponibilité et fabrication. Les trois
faux positifs des journaux PM-0003T ne sont consultés ni utilisés par ce module.
