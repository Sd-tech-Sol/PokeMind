# Checklist de release

Décisions D-268 à D-271. La version publique est un **nouveau dépôt public d'un seul commit** de l'arbre
courant; le dépôt privé et son historique restent privés et intacts. Les sections C et D ne s'exécutent
qu'avec un **GO explicite** du propriétaire.

## A. Préparation locale — autorisée

1. Porte locale complète VERTE : `python scripts/local_gate.py` (jamais `-k` comme preuve).
2. EXE : `.\scripts\Build-PokeMindDesktop.ps1`, fumées en mode projet et en mode autonome sur la fixture
   inventée (`scripts/qa_unified_desktop.py --prepare-release`), sans jamais ouvrir `%LOCALAPPDATA%\PokeMind`.
3. Installateur : `.\scripts\Build-PokeMindInstaller.ps1`. Il refuse tout fichier personnel, lance
   `scripts/scan_binary_personal_paths.py --require-archive` (nom du compte, profil, chemin du dépôt, en
   ASCII, UTF-16LE et dans l'archive Python), puis écrit `PokeMind-Setup-<version>.exe` et son `.sha256`.
4. Installation silencieuse dans un dossier temporaire, fumée depuis la copie installée, désinstallation
   propre (raccourci et clé de désinstallation retirés).
5. Fichiers publics à jour : `README.md` / `README.fr.md` (ligne « Status »), `CHANGELOG.md`,
   `THIRD_PARTY_NOTICES.md`, `docs/RELEASE_NOTES_<version>.md`.

## B. Signature et distribution d'un binaire — action humaine séparée

- Sans certificat : publication non signée, avertissement SmartScreen documenté dans `CODE_SIGNING.md`.
- Avec une identité d'éditeur (Azure Artifact Signing, SignPath, certificat OV/EV) :
  `Build-PokeMindInstaller.ps1 -SignArguments …`; le SHA-256 est calculé après la signature.

## C. Publication — GO spécial obligatoire

0. Mise à jour d'un dépôt public existant : `git fetch` de celui-ci d'abord. Si le propriétaire y a fait des
   commits dans l'interface GitHub, les reporter dans le dépôt privé avant l'export, puis créer le commit
   « PokeMind x.y.z » **par-dessus** eux (`git commit-tree <arbre exporté> -p origin/main`), jamais à leur place.
1. Export propre, sans push :
   `python scripts/export_public.py <dossier hors dépôt> --author-name "<auteur>" --author-email "<noreply>"`.
   Le script refuse fichier privé, base, clé, secret, courriel personnel, nom d'utilisateur Windows et nom
   Git de ce PC (sauf s'ils forment l'auteur choisi), et vérifie que l'arbre publié est identique à HEAD.
2. Porte complète dans l'export : `python <dossier>/scripts/local_gate.py` (VERTE).
3. Création et premier push avec la session `gh` du propriétaire :
   `gh repo create Sd-tech-Sol/<nom> --public --source <dossier> --remote origin --push --description "…"`.
4. Préversion : `gh release create v<version> <installateur> <installateur>.sha256 --repo Sd-tech-Sol/<nom>
   --prerelease --title "PokeMind <version>" --notes-file docs/RELEASE_NOTES_<version>.md`.
5. Rapport assaini dans le dépôt privé (RESULT/HANDOFF/NEXT_ACTION/STATE).

Une mise à jour publique ultérieure se fait par un nouvel export appliqué dans le dépôt public (commit
« PokeMind x.y.z »), jamais par un push de l'historique privé.

## D. Réglages du dépôt GitHub — dans l'interface, pas dans le dépôt

- Description : « Pokémon TCG Live companion for Windows: battles, decks and cards remembered on your PC
  (unofficial fan project). »
- Sujets : `pokemon-tcg`, `pokemon-tcg-live`, `windows`, `desktop-app`, `python`, `pyside6`,
  `offline-first`, `deck-builder`, `tcgdex`.
- Issues activées, wiki désactivé, **signalement privé de vulnérabilités** activé (lien de `SECURITY.md`).
- Branche par défaut `main`.

## E. Identité publique — comme les autres dépôts publics de `Sd-tech-Sol`

- Auteur et mainteneur : le nom complet du propriétaire, lien <https://github.com/Sd-tech-Sol>.
- Licence MIT au même nom; commits signés de ce nom avec son adresse `noreply` GitHub.
- Divulgation de l'assistance IA dans `AI_ASSISTANCE.md` et dans la section « AI-assisted development »
  du README.
- Nom du dépôt : le nom du produit, `Sd-tech-Sol/PokeMind`. Le dépôt privé de développement a été renommé
  `Sd-tech-Sol/PokeMind-dev` (D-271) et l'adresse `origin` locale pointe vers lui.
- Pas d'intégration continue sur GitHub : la preuve reste la porte locale (D-271).
- Pas de mention dans le README du profil `Sd-tech-Sol` (D-271).
