# RESULT — PM-AUDIT-CLAUDE-PLAN : journal collé → deck adverse enregistré; terminal intégré (D-263, 2026-10-31)

Exécuteur : Claude Code (Opus 5.5). Autorisation : D-258; ordre du propriétaire en session (« go, change-moi ça »).
Code : **`3cd633566386d3f116bb1063ff9a1ec9e171ef62`** (fonctionnalités) puis **`62a5229867590645941fd79009141e4ceb852be2`** (EXE : `OpenConsole.exe` embarqué). Sessions précédentes (D-259 à D-262) :
[archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_D259-D262_2026-10-31.md](archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_D259-D262_2026-10-31.md).

## Demande du propriétaire
1. Coller le journal d'une défaite → le coach dit quel deck l'a battu, complète les cartes non vues d'après les listes
   publiques, lui donne un nom et **l'enregistre tout seul dans sa liste de decks**, avec Codex comme avec Claude.
   Constaté avant : son texte disparaissait, « journal détecté », puis seulement un bilan victoires/défaites.
2. Parler à Codex (/yolo) et à Claude Code (toutes permissions) **dans l'application, comme dans PowerShell** (étape 3 du plan).

## Causes
- `split_message` ne gardait autour du journal que les lignes commençant par pourquoi/comment/analyse… : « c'est quel
  deck qui m'a battu? » était avalé avec le journal; l'en-tête français « Mise en place » n'était pas reconnu.
- Sans question gardée, la fin d'importation n'affichait que les totaux du corpus; aucun outil ne pouvait enregistrer un
  deck nommé (`save_candidate` ne garde qu'un seul candidat anonyme).

## Correctifs
- `ingestion.py` : tout texte du propriétaire avant ou après le journal est la question, sauf une ligne qui ressemble à
  un événement de partie; « Mise en place » reconnu.
- `window.py` : après un journal sans question, demande fixe au coach (archétype adverse, 60 cartes : vues d'abord,
  le reste d'après les listes publiques, nom, enregistrement); totaux du corpus dans la barre d'état; sans consentement
  cloud + « Ajouter statistiques… », le chat dit quoi cocher. Le Deck Lab se recharge quand le coach a enregistré un deck.
- `services.py` + `tools.py` : opération coach **`save_deck`** (Codex, Claude, Ollama) : nom (80 caractères max) +
  liste validée à exactement 60 cartes, `data/local/battle-intelligence/my-decks/deck-<sha256>.json`, création seule
  (`ALREADY_SAVED` si la même liste existe; jamais d'écrasement); permise après un journal collé ou une demande
  explicite. Decks listés en tête du Deck Lab, référence personnelle, version jouée non attestée.
- `provider.py` : consignes du coach pour un journal collé (cartes observées / déduites, `validate_deck`, `save_deck`,
  nom court, « reconstruction, pas la liste exacte »).
- **Terminal** (`desktop/terminal.py`, page « Terminal ») : ConPTY via pywinpty 3.0.5 + rendu pyte 0.8.2 dans un widget
  Qt (police Cascadia Mono, palette Campbell, sélection/copie, collage, défilement, molette transmise aux applications
  plein écran comme Codex). Filtre des séquences clavier (`CSI > 4;2 m`, protocole Kitty) que pyte lisait comme un
  soulignement; réponses immédiates aux questions de conhost (ConPTY attendait 3 s sans réponse) et aux questions de
  couleur. Onglets **Codex · yolo** (`--dangerously-bypass-approvals-and-sandbox`), **Claude Code · toutes permissions**
  (`--dangerously-skip-permissions`, via `cmd /c` pour le lanceur npm) et **PowerShell**, dans le dossier de développement.
  Consentement de confidentialité existant exigé pour Codex et Claude (portée `terminal-full-access`); fermeture d'onglet
  ou de l'application avec confirmation, arrêt de l'arbre de processus (`taskkill /T`). Marqueurs d'une session Claude
  parente retirés de l'environnement. QtWebEngine + xterm.js écarté : environ +350 Mo pour l'EXE.
- Dépendances épinglées (`desktop`, `desktop-build`) : `pyte==0.8.2`, `wcwidth==0.2.13`, `pywinpty==3.0.5` (Windows);
  binaires winpty/ConPTY embarqués; licences copiées dans le portable et notées dans `docs/DESKTOP_THIRD_PARTY_NOTICES.md`.

## Preuves
`python scripts/local_gate.py` (copie hors dépôt, sans `data/local`, hors ligne, Qt `offscreen`) au SHA du code :
| Étape | Résultat |
|---|---|
| Compilation, hygiène Git | OK, OK |
| Tests Qt | **75 passed** |
| Tests du cœur | **1509 passed, 3 skipped (OCR non attesté)** |
| **Total** | **1584 réussis, 0 échec** — PORTE LOCALE : **VERTE** |

Deux exécutions complètes précédentes ont été arrêtées volontairement (arbre de processus tué, copie retirée) parce que
du code avait changé après leur copie; seule l'exécution sur l'arbre définitif est retenue.

Nouveaux tests (tout inventé) : journal collé seul → le coach reçoit la partie et la reconstruction et enregistre le
deck nommé, Deck Lab et barre d'état à jour; texte du propriétaire avant le journal gardé comme question; `save_deck`
refusé sans demande, sans nom, à 59 cartes, sans écrasement; touches (Ctrl, AltGr, flèches), rendu sans soulignement
parasite, titre, réponse de couleur, sélection/copie/collage (avec collage encadré), historique; programme réel aller-retour
par ConPTY (code de sortie 3); page Terminal : Codex/Claude lancés avec leurs drapeaux seulement après consentement,
PowerShell sans dialogue, consentement mémorisé, fermeture confirmée; lanceur npm via `cmd /c`; marqueurs de session retirés.

**Essais réels dans la vraie fenêtre** (racine jetable : copies des seuls caches PUBLICS, journal **inventé** d'une défaite
contre Fantyrm / Dispareptil / Lanssorien-ex, joueurs anonymes) :

| Moteur | Durée | Résultat |
|---|---|---|
| Claude (journal seul) | 73 s | « Lanssorien-ex (Dragapult ex) », cartes vues / déduites séparées, `validate_deck` corrigé puis 60 cartes sans problème, `save_deck` → « Dragapult ex - adversaire du 2026-10-31 (reconstruction) » |
| Codex (question + journal) | 113 s | même archétype, liste validée, `save_deck` → deck enregistré (nom trop long coupé à 80 : consigne « nom court » ajoutée) |

Sur cette racine jetable, aucune liste publique n'était disponible (attestation de l'espace public absente : artefact de
test); les deux moteurs l'ont dit et ont marqué les cartes déduites comme hypothèses. Terminal : PowerShell, Claude Code
(« bypass permissions on ») et Codex rendus correctement dans un dossier vide, rien tapé; page Terminal de la vraie
fenêtre capturée avec un onglet PowerShell fonctionnel. GitHub Actions : bloqué par le budget; non revendiqué.

## EXE
- Premier build depuis `3cd6335` (794 fichiers) : `OpenConsole.exe` et `winpty-agent.exe` absents (`--collect-binaries`
  ne garde que les DLL); essai avec les seuls binaires de ce portable : **aucune console ne démarre**; avec le jeu complet
  du paquet : démarre. Corrigé dans `62a5229` (les deux `.exe` nommés dans `Build-PokeMindDesktop.ps1`), porte locale
  **VERTE** sur ce commit (**Qt 75, cœur 1509 passed / 3 skipped, 0 échec**). Ce premier build n'a jamais été installé.
- Build depuis `62a5229` (staging neuf, paramètres de production) : **exit 0, 796 fichiers, 118 Mo** (avant : 788 fichiers, 117 Mo).
- Archive figée lue sans exécution : **68/68 modules `pokemind.*` identiques** aux sources (dont `desktop.terminal`),
  entrée `app` identique, **0 module QA**, ni pytest ni `winpty.tests`; `winpty`, `pyte`, `wcwidth` embarqués.
- ConPTY lancé avec **exactement les binaires `winpty` du portable** (code Python du paquet installé) : console démarrée.
- **Smoke du vrai EXE** sur une fixture **inventée** neuve, seul `POKEMIND_DESKTOP_SMOKE=1` actif : **exit 0**, figé, visible,
  **7 pages**, rapport, liste exacte 60, galerie, import, activité, **`terminal_available: true`**; 5 bases synthétiques
  inchangées; capture inspectée (interface ordinaire, entrée « Terminal » dans le menu).
- Permutation, application du propriétaire fermée (vérifié avant), PowerShell 7 : ancien `dist/PokeMind` (**788 fichiers**)
  conservé intact sous `dist/PokeMind-before-terminal-…`; **796 fichiers installés identiques** au candidat (SHA-256);
  ConPTY revérifié avec les binaires installés. `data/local` jamais ciblé.
- **Retour arrière** (non exécuté) : fermer l'app, renommer `dist/PokeMind` en un nom neuf, renommer
  `dist/PokeMind-before-terminal-…` en `dist/PokeMind`.

## Non fait / limites
- Aucune donnée personnelle ouverte; `data/local` personnel jamais lu. Les réglages réels du propriétaire (consentement
  cloud, partage) restent inconnus : si « Ajouter statistiques… » n'est pas choisi, le chat le lui dit.
- La liste reconstruite reste une hypothèse : cartes non vues déduites, légalité présumée, collection et crédits inconnus.
- Pas de bouton pour retirer un deck de « Mes decks » (création seule, comme demandé); les fichiers restent dans `data/local`.
- Terminal : rendu pyte (pas d'écran alternatif ni d'images); Ctrl+V colle du texte (pas d'image dans Claude); Codex
  propose lui-même une mise à jour 0.166 au démarrage : le coach est éprouvé avec 0.163.
- Le Python système du PC avait `pywinpty` 3.0.5 pour un autre paquet; une installation 2.0.15 l'a brièvement remplacé,
  puis 3.0.5 a été remise (`pip check` sans conflit) et adoptée pour PokeMind.
- A-8, A-7, M-4 et l'étape 2 (données hors du dépôt) restent à faire.
