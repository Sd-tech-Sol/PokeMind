# Guide V1 local — commandes courantes

Pour les seules listes de tournoi déjà PUBLIC :
[`meta competitive-preflight`](PUBLIC_DECK_LEGALITY_PREFLIGHT.md) compare les
preuves de légalité et leurs lacunes avec deux bases explicites, sans réseau.

Pour commencer sur une base **synthétique jetable**, exécuter
`python -m pokemind demo --json`; voir `PREMIER_USAGE_WINDOWS.md`.
Le [parcours E2E reproductible](PARCOURS_UTILISATEUR_E2E.md) détaille les
79 appels isolés, cinq journaux, attestations révocables et candidat60.
Les autres exemples sans `--db` ci-dessous visent la base personnelle par défaut
et exigent que l'acte demandé soit autorisé. La démo ne les exécute pas sur celle-ci.

Toutes les commandes se lancent depuis la racine PokeMind. Ajouter `--json` pour une
sortie structurée. Sans preuve datée, PokeMind répond `unknown`; TCGdex décrit une
impression, Pokémon officiel tranche les règles, Limitless décrit un échantillon, et
aucune de ces sources ne prouve possession ou disponibilité Live à elle seule.

## Bibliothèque et état

```powershell
python -m pokemind status --json
python -m pokemind search "question" --json
python -m pokemind knowledge status --json
python -m pokemind knowledge audit --json
python -m pokemind capability status --json
python -m pokemind v1 readiness --json
```

Une citation de bibliothèque porte fichier `.md`, date source et lignes. `status` et
les audits sont hors ligne et ne migrent pas une vieille base.

## Cartes, règles et métagame

```powershell
python -m pokemind cards search "nom" --lang all --json
python -m pokemind cards show ID-TCGDEX --lang fr --json
python -m pokemind cards reprints ID-TCGDEX --as-of 2026-10-13 --json
python -m pokemind cards coverage --json
python -m pokemind rules check-card ID-TCGDEX --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind rules check-deck principal --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind meta coverage --format standard --platform PTCGL --online true --json
```

Ne jamais transformer une réimpression de même nom en équivalence, un tournoi en
autorité de légalité ou une absence du cache en absence du jeu.

## Decks, collection, crédits et combats

```powershell
python -m pokemind deck import --deck principal data\local\deck.txt --json
python -m pokemind deck show principal --json
python -m pokemind deck compare principal --from-version 1 --to-version 2 --json
python -m pokemind analyze deck principal --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind recommend deck principal --format standard --platform live --as-of 2026-10-13 --collection --json
python -m pokemind log import data\local\combat.txt --deck principal --json
python -m pokemind battle lessons --deck principal --as-of 2026-10-13 --json
```

Les imports collection/crédits, notes, candidats et attestations ont un dry-run puis
`--apply --confirm-owner`; voir `docs/LOT_B_GUIDE.md` et
`docs/PM-0006C_MANUAL_ATTESTATIONS.md`. Une carte observée en combat n’est jamais une
preuve de collection ni une liste exacte de 60 cartes. Aucun crédit n’est dépensé.

## Coach d’entraînement

```powershell
python -m pokemind match capabilities --json
python -m pokemind match preflight --json
python -m pokemind match start --as-of 2026-10-13 --dry-run --json
python -m pokemind match observe --image data\local\screenshots\tour-1.png --turn 1 --mode training --dry-run --json
python -m pokemind match observe --image data\local\fixtures\synthetic.png --calibration data\local\fixtures\calibration.json --turn 1 --mode training --dry-run --json
python -m pokemind match observe --annotation data\local\annotations\tour-1.json --session SESSION --turn 1 --mode training --apply --confirm-owner --json
python -m pokemind match advise --session SESSION --turn 1 --format standard --platform live --as-of 2026-10-13 --json
```

Images explicitement fournies, éphémères, entraînement autorisé seulement. L’adaptateur
LOT F lit réellement les pixels PNG, mais seulement selon son ruleset de marqueurs
synthétiques; il ne constitue pas une reconnaissance générale de capture TCG Live.
Sans calibration explicite, l’image seule retourne `NEEDS_MANUAL_ANNOTATION`. Main,
pioche et Récompenses cachées restent inconnues. Aucun overlay, clic ou accès au
processus du jeu.

LOT G ajoute le profil `pokemind_tesseract_roi_v1`, moteur local optionnel. Ici,
aucun Tesseract n’est installé : tests de contrat avec OCR simulé seulement.
Les résultats restent `ocr_uncertain`, jamais une action attestée. Profil, limites
et décisions distinctes : `docs/LOT_G_LOCAL_VISION.md`.

## Actualisation publique et scheduler bloqué

```powershell
python -m pokemind knowledge update --mode daily --dry-run --json
python -m pokemind knowledge update --mode auto --deep-time 19:30 --dry-run --json
python -m pokemind knowledge update status --deep-time 19:30 --json
python -m pokemind knowledge scheduler --action install --daily-time 08:15 --deep-time 19:30 --windows-timezone "Eastern Standard Time" --dry-run --json
```

L’application publique exige `--apply --confirm-owner`. Le scheduler réel demeure
désactivé; le fuseau Windows Toronto doit être prouvé et un consentement futur
distinct est obligatoire. Voir `docs/LOT_D_PUBLIC_UPDATE_GUIDE.md`.

## Sauvegarde et restauration

```powershell
python -m pokemind backup plan --destination data\local\backups --json
python -m pokemind backup create --destination data\local\backups --apply --confirm-owner --json
python -m pokemind backup verify --backup data\local\backups\FICHIER.sqlite3 --json
python -m pokemind restore plan --backup data\local\backups\FICHIER.sqlite3 --json
python -m pokemind restore verify --backup data\local\backups\FICHIER.sqlite3 --migrate-clone --json
```

Créer un backup réel et restaurer la base personnelle sont deux décisions distinctes.
`restore verify` ne touche que son clone temporaire. Depuis LOT G, `restore apply`
publie seulement un clone neuf choisi avec `--db`; tout remplacement existant
est bloqué faute d’exclusion durable. WAL/SHM/journal et header WAL sont refusés.
Aucune restauration personnelle pendant G. Détails : `docs/RECUPERATION_LOCALE.md`
et `docs/MISE_EN_SERVICE_PROPRIETAIRE.md`.

## Chemins et confidentialité

- Données privées : `data/local/`, ignoré par Git.
- Sauvegardes : dossier privé configurable; jamais Git/cloud implicitement.
- Registre public versionné : `knowledge/curated/`.
- Exemples, CI et tests : synthétiques seulement.
- Une erreur CLI expose un code neutre et une remédiation, pas le chemin, token, nom
  ou texte technique interne.

## Ajouts H : préparation et preuves locales

```powershell
python -m pokemind owner-plan --step migration --json
python -m pokemind match benchmark-ocr --json
python -m pokemind match review --help
python -m pokemind match revoke-review --help
python -m pokemind knowledge review-official --help
python -m pokemind knowledge cadence --start-utc 2026-10-31T00:00:00Z --daily-time 01:30 --deep-time 05:00 --days 14 --json
```

H ne crée aucun moteur OCR, capture réelle ou tâche OS. Le benchmark rasterisé
affiche OCR_ENGINE_NOT_INSTALLED ici. Une revue d'observation reste une déclaration
révocable; une revue de document officiel ne valide pas automatiquement les règles.
Les rapports de catalogue séparent snapshots datés et union FR/EN. La rétention
est désormais preview seulement : apply refuse RETENTION_EXTERNAL_EXCLUSION_UNPROVEN.
Le remplacement d'une cible existante reste bloqué. Les actes personnels sont
préparés séparément dans `MISE_EN_SERVICE_PROPRIETAIRE.md`; V1 NOT_RELEASE_READY.
