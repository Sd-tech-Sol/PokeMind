# PM-AUDIT-CLAUDE-PLAN — exécution du plan d'audit, suite en prochaine session

2026-10-29 Québec. **Mandat actif. Exécuteur : Claude Code** (propriétaire, D-258 : « tu as toutes mes autorisations… fais tout »).
Plan de référence : [`docs/audits/AUDIT_CLAUDE_2026-10-29.md`](../docs/audits/AUDIT_CLAUDE_2026-10-29.md) §10. Dernière session : voir [RESULT](RESULT.md).

## Demande du propriétaire du 2026-11-01 — refonte visuelle et version publique (D-266 à D-271)
Fait : refonte visuelle (D-266); mode autonome, catalogue et installateur (D-267); licence MIT, logo original et audit
de l'historique (D-268); export public vérifié et signature branchée (D-269); fichiers publics au standard des autres
dépôts publics de `Sd-tech-Sol` et vérification des binaires (D-270, `a334dec`); dépôt privé renommé
`Sd-tech-Sol/PokeMind-dev`, pas d'intégration continue publique, profil inchangé (D-271).
Reste, sur décision du propriétaire seulement :
1. **GO de publication** (rendre PokeMind visible de tous sur GitHub). L'identité d'auteur est celle des autres dépôts
   publics (relevée sur leurs commits, non recopiée ici). Au GO : `docs/release-checklist.md` sections A (recompiler
   l'EXE et l'installateur : nouvelle `LICENSE` et avis), C (export, porte, `gh repo create Sd-tech-Sol/PokeMind`,
   préversion `v0.9.0` avec `.sha256`) et D (description, sujets, signalement privé).
2. **Signature** : avec un certificat, `Build-PokeMindInstaller.ps1 -SignArguments …`; sinon publier non signé.
3. Plus tard : actualiser le catalogue vers un commit TCGdex plus récent, avec repli sur l'instantané éprouvé.

## Réception propriétaire en attente
Ouvrir son `dist/PokeMind/PokeMind.exe` habituel et vérifier :
- **Installateur (D-267, facultatif)** : `dist/installer/PokeMind-Setup-0.9.0.exe` installe une copie autonome pour ton
  compte (`%LOCALAPPDATA%\Programs\PokeMind`, menu Démarrer). Elle utilise `%LOCALAPPDATA%\PokeMind` : si ta copie
  D-264 est à cet endroit, elle ouvre tes données (sans le mode dossier du chat); sinon elle démarre vide avec
  l'assistant de bienvenue et propose le catalogue (25 Mo, environ 1 min). Ne pas ouvrir les deux applications en
  même temps. Désinstaller : Paramètres Windows › Applications › PokeMind (tes données restent).
- **Mode du message (D-269)** : à gauche d'Envoyer, « Coach » (par défaut), « Recherche web » (collecte publique pour
  ce seul message) ou « Développement » (Codex/Claude sur le code). Aucun mot de la phrase ne change plus le mode.
- **Refonte visuelle (D-266)** : pendant une réponse, une carte rouge animée avec chrono apparaît au-dessus du champ;
  Entrée envoie; « Agrandir » (en haut du chat) ouvre la discussion en grande fenêtre et « Ramener » la remet. Les listes
  « Historique » et « Idées de questions » s'ouvrent en entier. Logo original (deux cartes et un cerveau, D-268) dans le
  menu, la barre des tâches et l'icône de l'EXE. Pages Réglages (onglets), Combats (tuiles et barres), Cartes & méta (classeur : la
  couverture s'ouvre, flèches ‹ › pour tourner les pages, clic sur une carte = fiche), Apprentissage, Terminal (un clic
  ouvre le moteur du chat). La langue suit ton choix enregistré, sinon celle de Windows (Réglages → Général pour
  changer); l'assistant de bienvenue ne s'affiche pas pour toi (préférences existantes).
- **Données hors du projet (D-264)** : au premier démarrage, PokeMind demande « Sortir tes données du projet » avec la
  destination (`%LOCALAPPDATA%\PokeMind`), la taille et le nombre de fichiers. Répondre **Oui** : barre de progression,
  puis « Copie vérifiée : N fichiers ». Vérifier ensuite combats, Deck Lab (« Mes decks »), discussions du coach,
  préférences et caches. Réglages → « Dossier de données » montre le nouveau chemin. En cas de problème : Réglages →
  « Revenir au dossier du projet », puis rouvrir. **Ne rien supprimer** : l'original reste dans `data/local` du projet;
  le retirer plus tard est une décision du propriétaire seulement.
- **Chat dans le dossier PokeMind (D-265)** : Réglages → « Le chat travaille dans le dossier PokeMind » est cochée.
  Écrire dans le chat comme à Claude Code : la première fois, accepter l'avertissement de confidentialité. Codex ou
  Claude répondent selon les règles du dossier, peuvent lire et modifier les fichiers du projet (mode Standard ou
  Accès complet) et gardent les outils du coach. Un journal collé reste traité par le coach isolé (deck enregistré
  comme avant). Décocher la case rend le coach isolé d'avant.
- **Coach (D-259, D-261)** : « fais-moi le meilleur deck avec Pikachu » avec **Codex**, puis avec **Claude** : un deck
  de 60 cartes en français avec codes et export TCG Live, validé (Codex : environ 3 minutes, compteur « Outils PokeMind ·
  consultation N » pendant l'attente), et non plus un bilan de statistiques. Réglages : la case d'envoi cloud doit être cochée.
  La réponse doit venir **même si la barre du bas indique une analyse en cours** (D-262); la liste « Reprendre une
  discussion » montre les titres complets.
- **Journal collé** (D-263) : Réglages → cocher l'envoi cloud et choisir « Ajouter statistiques… »; coller le journal
  d'une défaite (avec ou sans question) : le coach nomme le deck adverse, sépare cartes vues / déduites, valide 60 cartes
  et l'ajoute à **Deck Lab** (en tête, « Mon deck »). Barre du bas : « Deck ajouté à Mes decks : … ».
- **Terminal** (D-263, menu de gauche, dernier) : « Codex · yolo » ou « Claude Code · toutes permissions » → accepter
  l'avertissement de confidentialité une fois → écrire comme dans PowerShell. Ctrl+V colle, Ctrl+C copie la sélection
  (sinon interrompt), clic droit copie ou colle. Codex peut proposer une mise à jour : « Skip » garde la version éprouvée.
- **Supprimer** (D-260) : choisir une discussion, cliquer Supprimer, répondre Non puis Oui; elle disparaît de l'historique.
- Réglages (« Copier le diagnostic » montre maintenant une ligne par appel d'outil), fluidité du chat, mode développement.
Signaler tout écart; un retour arrière reste possible (anciens dossiers conservés sous `dist/`, voir RESULT).

## Prochaines étapes, dans l'ordre (une par session, `/clear` entre chacune)
1. ~~EXE à jour~~ : **fait le 2026-10-29**; reste la réception propriétaire ci-dessus.
2. ~~Données hors du dépôt~~ : **code fait le 2026-11-01 (D-264)**, copie vérifiée proposée au démarrage de l'EXE, original
   jamais touché; le CLI suit le même dossier. Reste la validation du propriétaire ci-dessus. Suites possibles : scripts
   autonomes de `scripts/`, EXE installé hors de `dist/` du dépôt, fixture `local_tmp` des tests hors de `data/local/test-runs`.
3. **Mode développement v2** (audit §4) : ~~terminal embarqué lançant `codex`/`claude` tels quels~~ **fait le 2026-10-31
   (D-263, ConPTY + pyte au lieu de xterm.js)**; reste éventuellement le client riche du chat (processus Claude persistant).
4. **Coach** : ~~outils et parité Codex/Claude/Ollama~~ **faits le 2026-10-29 (D-259)**; ~~A-8 mode explicite~~ et
   ~~A-7 contexte allégé~~ **faits le 2026-11-02 (D-269)**; reste éventuellement les permissions d'écriture du coach
   (annotation, proposition, decks privés) encore fondées sur les mots, à remplacer par une confirmation dans l'UI.
5. **Mémoire restante** (M-2 fin, M-4) : cache de `public_context`, analyse incrémentale par `semantic_identity`.
6. **Maintenabilité / publication** (§7, §9) : `ruff`, découpage de `cli.main`/`window.py`, client HTTP unique,
   crochets QA hors de l'EXE de production, licence et droits sur `source_material/`.

## Règles du mandat
- Porte locale `python scripts/local_gate.py` **VERTE** avant chaque push de code; comptes exacts dans RESULT.
- Aucune lecture/ouverture de `data/local` personnel ni de la copie sous `%LOCALAPPDATA%\PokeMind` par un agent; la copie
  se fait seulement dans l'EXE, sur « Oui » du propriétaire (D-264). Jamais de suppression de données ou de distribution précédente.
- V1 `NOT_RELEASE_READY`.

---

## Archives
Les mandats antérieurs (jusqu'à `PM-V1-LIVE-FR-EN-UI-001`) sont dans
[archive/2026-10/NEXT_ACTION_avant_2026-10-29.md](archive/2026-10/NEXT_ACTION_avant_2026-10-29.md). Aucune permission courante.
