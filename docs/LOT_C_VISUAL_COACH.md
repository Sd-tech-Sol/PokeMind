# Coach visuel d’entraînement — LOT C

## Portée et sécurité

Ce parcours est réservé à une partie d’entraînement où l’assistance externe est
permise. PokeMind ne capture pas l’écran, ne surveille pas Pokémon TCG Live, ne lit
pas son processus, n’injecte rien, ne crée aucun overlay et n’automatise aucun clic.
Il n’est pas destiné à un tournoi qui interdit l’assistance.

Les images sont choisies explicitement sous `data/local/`. PNG, JPEG et WebP sont
acceptés après contrôle du chemin, des liens symboliques, de la signature, de
l’extension, de la taille, des dimensions, du nombre de pixels et de l’orientation.
Les octets vivent seulement pendant la commande : aucune image, chemin absolu ou
empreinte de capture n’est écrit dans SQLite, Git, les rapports ou les sauvegardes.
Le fichier source n’est pas supprimé; le propriétaire peut le retirer manuellement.

## Parcours

Prévisualiser puis ouvrir une séance textuelle :

```powershell
python -m pokemind match start --as-of 2026-10-13 --dry-run --json
python -m pokemind match start --as-of 2026-10-13 --apply --confirm-owner --json
```

Inspecter une image sans écriture :

```powershell
python -m pokemind match observe --image data\local\screenshots\tour-1.png --turn 1 --mode training --dry-run --json
```

Sans backend local fiable, le résultat attendu est
`VISION_BACKEND_UNAVAILABLE` / `NEEDS_MANUAL_ANNOTATION`. Ce statut signifie que
l’image n’a **pas** été interprétée. Aucun service distant ou téléchargement de
modèle n’est déclenché.

Le LOT E ajoute un diagnostic sans import ni installation :

```powershell
python -m pokemind match capabilities --json
```

Il détecte seulement la présence éventuelle de Pillow, OpenCV, pytesseract,
Tesseract, EasyOCR et ONNX Runtime. Une bibliothèque présente ne rend pas la vision
opérationnelle : un adaptateur local, un modèle/ruleset identifié, une calibration
sur images synthétiques, des seuils par champ et un essai réel autorisé restent
obligatoires. Sur la machine LOT E, aucun de ces composants Python n’était présent;
aucun paquet ou modèle n’a été téléchargé. La reconnaissance réelle reste
`PARTIAL_WITH_EVIDENCE` et passe au LOT F avec consentement distinct.

Une annotation locale minimale peut être prévisualisée puis conservée :

```powershell
python -m pokemind match observe --annotation data\local\annotations\tour-1.json --turn 1 --mode training --dry-run --json
python -m pokemind match observe --annotation data\local\annotations\tour-1.json --session train-... --turn 1 --mode training --apply --confirm-owner --json
python -m pokemind match advise --session train-... --turn 1 --format standard --platform live --as-of 2026-10-13 --json
```

Corriger, relire, révoquer une correction et clore :

```powershell
python -m pokemind match correct --session train-... --observation 1 --annotation data\local\annotations\tour-1-corrige.json --dry-run --json
python -m pokemind match correct --session train-... --observation 1 --annotation data\local\annotations\tour-1-corrige.json --apply --confirm-owner --json
python -m pokemind match revoke-correction --session train-... --observation 2 --apply --confirm-owner --json
python -m pokemind match show --session train-... --json
python -m pokemind match close --session train-... --apply --confirm-owner --json
```

## Annotation versionnée

Exemple synthétique réduit :

```json
{
  "turn": 1,
  "phase": "attack",
  "turn_owner": "self",
  "sides": {
    "self": {
      "active": {
        "visibility": "visible",
        "card": {
          "name": "Nom confirmé",
          "tcgdex_id": "identifiant-public-exact",
          "provenance": "owner_annotated",
          "confidence": "certain"
        },
        "damage": 20,
        "energies": [{"type": "Colorless", "count": 1, "provenance": "owner_annotated"}],
        "provenance": "owner_annotated"
      },
      "hand": {"visibility": "partial", "count": 3, "cards": []},
      "prizes": {"apparent_count": 4}
    },
    "opponent": {
      "active": {"visibility": "ambiguous", "provenance": "ocr_uncertain"},
      "hand": {"visibility": "hidden", "count": 5},
      "prizes": {"apparent_count": 5}
    }
  },
  "unknown_fields": ["Banc adverse partiellement masqué"],
  "recognition_errors": []
}
```

Provenances du contrat : `visual_certain`, `ocr_uncertain`, `owner_annotated`,
`inferred`, `unknown`. Correctif D0 : une annotation propriétaire ne peut pas
s’autoattribuer une vision/OCR; sans adaptateur local attesté, `visual_certain` est
normalisé en `owner_annotated` et `ocr_uncertain` en `unknown`. Une inférence n’est
pas utilisée comme fait. Le contenu des Récompenses, une main ou défausse cachée et
l’ordre de la pioche sont toujours neutralisés, même si le JSON prétend les révéler.

## Mémoire et conseils

Le schéma SQLite 12 conserve `training_sessions` et `training_observations`, puis
retire seulement l’ancienne unicité historique qui empêchait A→B→A. Une séance reçoit
un identifiant aléatoire; les observations sont textuelles, dédupliquées lorsqu’elles
sont actives et isolées. Une correction crée une révision et marque l’ancienne comme
remplacée; sa révocation restaure l’état précédent sans supprimer l’historique. Une
prévisualisation ne crée ni base ni migration.

Les options de conseil sont `verified_possible`, `conditional` ou `not_supported`.
Le moteur livré ne promeut actuellement aucune action à `verified_possible`, car la
couverture des effets de tour et règles contextuelles n’est pas assez complète. Il
peut proposer conditionnellement une attaque seulement lorsque l’impression exacte,
son texte public, la date/contexte de séance et les types d’Énergie visibles sont
compatibles; une Énergie spéciale ou un modificateur inconnu force l’abstention. Il
n’affiche ni « meilleur coup » absolu, ni prédiction de victoire, ni carte cachée.

Une nouvelle image n’est utile qu’après une pioche/recherche/effet déterminant ou un
changement majeur. Le skill est disponible sous `.agents/skills/` pour Codex et sous
`.claude/skills/` pour Claude Code; les deux copies sont testées comme identiques.
