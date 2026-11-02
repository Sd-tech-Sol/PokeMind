# Premier usage PokeMind dans Codex — Windows 11

Depuis le dossier PokeMind ouvert dans Codex, demander « Lance le prévol puis
la démo synthétique hors ligne ». Les commandes sont :

```powershell
python -m pokemind preflight --json
python -m pokemind demo --json
```

Python 3.11+ et SQLite FTS5 sont requis. Aucune installation n'est lancée.
Le prévol vérifie FTS5 en mémoire, sans sélectionner la base personnelle.
Si Python est introuvable, son installation doit être décidée séparément.
La commande crée son propre sous-dossier temporaire sous `data/local/demo-runs`,
choisit une base neuve et retire seulement cet espace à la fin. Aucun argument
`--db` n'est accepté : elle n'utilise jamais la base personnelle par défaut.
Le rapport JSON contient des compteurs, citations et limites, sans chemin absolu.

Le parcours exécute réellement les CLI existantes : import idempotent des quatre
volumes, dix recherches citées, cartes fictives FR/EN, deux versions de 60 cartes,
comparaison et export/réimport PTCGL, cinq journaux synthétiques différents et leur
réimport dédupliqué, profil/leçons et conseil avec n=5 (une issue inconnue),
liaison explicite combat/version puis révocation, candidat60 exporté/réimporté
sous un autre identifiant sans changer le deck joué, trois tours annotés sur PNG
synthétique, correction conservant l'historique, conflit de contexte refusé,
relecture de mémoire depuis un processus neuf, actualisation dry-run et readiness.
Il simule aussi la cadence Toronto et install/status/uninstall Windows sans
contacter le planificateur. Chaque CLI est un nouveau processus Python : 79 appels,
13 checkpoints. Le [parcours reproductible E2E](PARCOURS_UTILISATEUR_E2E.md)
explique les commandes, les garde-fous réseau des tests et la récupération sur fixtures.

Résultat attendu : `SYNTHETIC_REHEARSAL_PASSED` et `NOT_RELEASE_READY`.
Un export exact de 60 cartes demeure de légalité inconnue; les noms fictifs
ne désignent aucun deck jouable. Le contrôle de structure officiel peut rester
`unknown`, faute d'identités et de règles entièrement prouvées. Les tests vérifient
séparément le total et l'absence de ligne dépassant quatre exemplaires.
Le PNG est fourni avec annotation, aucune lecture OCR n'est prétendue.
Les cinq combats ne prouvent ni cause de défaite ni collection. Seule la paire
explicitement attestée est attribuée à une version; sa révocation retire cette
attribution. Une issue ambiguë reste inconnue (ratio descriptif sur quatre issues).
Un second deck fictif résolu et des règles fabriquées produisent les trois états
`legal/not_legal/unknown`; aucune de ces règles n'est une norme Pokémon réelle.
Une source non vérifiée ou expirée reste `unknown`.

Pour conserver uniquement le rapport de la démonstration localement :

```powershell
python -m pokemind demo --json > data/local/demo-report.json
python -m pokemind match preflight --json
```

Le prévol OCR ne lit aucune image ni base et ne télécharge rien. Il rapporte
`OCR_ENGINE_NOT_INSTALLED` sur la machine de validation J. Un candidat présent
dans PATH reste `OCR_BINARY_UNATTESTED` : aucune exécution par défaut.
Une politique privée d'origine/empreintes et un opt-in d'exécution distincts
sont requis avant version/langues/benchmark. Voir `LOT_J_LOCAL_VISION.md`.

La suite concrète est le [parcours de validation propriétaire](VALIDATION_PROPRIETAIRE_V1_WINDOWS.md) :
cinq décisions séparées après audit ChatGPT (base/backup, clones/migration,
deck/journaux, OCR/captures d'entraînement permises, horaire/planificateur).
Cette documentation n'autorise aucun de ces actes.

## Retour après une nouvelle session

Ouvrir de nouveau **ce même dossier**, lire `AGENTS.md`, puis
`.orchestrator/HANDOFF.md` et `.orchestrator/NEXT_ACTION.md`. La mémoire durable
vient des fichiers et de SQLite; une nouvelle conversation ne l'efface pas.
La démo prouve cette propriété entre processus frais pendant son exécution;
sa base temporaire est ensuite retirée. Relancer la démo crée un nouveau scénario.
Elle ne prétend pas piloter `/clear` dans l'application Codex.

Pour les vraies données, préciser d'abord l'acte et la base autorisés. Les exemples
du guide CLI sans `--db` visent **la base personnelle par défaut** : ils ne font pas
partie de la démo et n'autorisent aucun import, migration ou backup implicite.
`MISE_EN_SERVICE_PROPRIETAIRE.md` sépare ces décisions.

| Demande courante | Commande de consultation après choix de la base |
|---|---|
| Trouve le passage sur la retraite | `python -m pokemind search "retraite" --db BASE --json` |
| Cherche la carte dans les deux langues | `python -m pokemind cards search "nom" --lang all --db BASE --json` |
| Compare deux versions déclarées | `python -m pokemind deck compare ID --from-version 1 --to-version 2 --db BASE --json` |
| Quelle confiance dans ces combats? | `python -m pokemind battle lessons --deck ID --as-of AAAA-MM-JJ --db BASE --json` |
| Reprends la séance autorisée | `python -m pokemind match show --session SESSION --db BASE --json` |
| Qu'est-ce qui manque pour la V1? | `python -m pokemind v1 readiness --db BASE --json` |

`BASE`, `ID`, `SESSION` et la date sont des valeurs à choisir explicitement;
aucune commande ne joue dans le client Pokémon. Sans Internet, les consultations
utilisent les connaissances déjà indexées et conservent les inconnues.
