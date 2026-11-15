# Vérification indépendante ChatGPT — candidat PokeMind 0.9.4 (2026-11-07)

## Portée
Revue GitHub en lecture du commit code `fae10daa7e4ad4cb1476a979c27b7a458e686836`, rapport exécuteur `90bd600`, du correctif loss-priority `5ee8c45`, des sources `services.py`, `welcome.py`, `window.py`, tests `test_loss_watch.py`, `test_version_metadata.py`, `make_version_info.py`, procédure `docs/release-checklist.md`, et `.orchestrator/RESULT.md`. Vérification des changements GitHub et cohérence des preuves rapportées. **Aucun accès ni exécution sur le PC du propriétaire, aucun re-run indépendant des tests Windows.**

## Verdict
**VERIFIED_SOURCE / CANDIDATE_FOR_OWNER_RECEPTION.** Aucune anomalie bloquante démontrée dans les éléments relus; **NOT_VERIFIED_WINDOWS, NOT_RELEASE_READY** tant que réception utilisateur et GO de publication distincts n'ont pas eu lieu.

## Confirmé indépendamment dans le code
- `owner_main_deck` conserve le nom, mais n'ajoute `export` que lorsque `private_decks_allowed`; cette condition découle des mots « deck » ou « liste » dans la question. L'export n'est pas envoyé avec une question sans rapport. Test de régression écrit.
- `SHARING_HINT` apparaît aux réglages et à l'assistant de premier lancement; README FR/EN et PRIVACY explicitent le partage cloud activé par défaut. Cela ne veut PAS dire que les données anonymisées ne contiennent aucune information sensible : l'envoi de listes complètes de decks sur question pertinente reste autorisé selon le choix de partage.
- `pyproject.toml` et `pokemind.__version__` indiquent 0.9.4; l'outil `make_version_info.py` est passé à PyInstaller, et Inno Setup reçoit `VersionInfoVersion`. Test de cohérence source présent.
- Le suivi `loss_watch.py` est dérivé du rapport sans stockage de deck adverse; le correctif précédent garde ses gardes d'écriture côté hôte (relecture ciblée antérieure).

## Preuves exécuteur, non reproduites par ChatGPT
- `python scripts/local_gate.py` : Qt 119, cœur 1624, 0 échec, 3 ignorés; même total sur export public dry-run.
- Staging Windows : 0.9.3 QA → upgrade 0.9.4 QA → désinstallation sans changement des 11 fichiers de données synthétiques; 7 pages disponibles. Installateurs QA avec AppId/nom/raccourcis modifiés, non le Setup de production.
- HTTPS API GitHub et TCGdex avec certificat valide; refus certificats invalides; analyse des 797 fichiers EXE et 320 modules archivés annoncée CLEAN.
- Version 0.9.4 extraite des ressources PE, icônes 9/9, SHA-256 binaire et installateur vérifiés par l'exécuteur.

## Limites connues
1. **Réception réelle manquante** : vraie mise à niveau 0.9.3 → 0.9.4 et préservation des données utilisateur non testées. Ne jamais l'inférer d'un essai QA isolé.
2. **Mise à jour depuis l'application (/RELAUNCH)** non rejouée pour ce candidat; preuve antérieure D-283.
3. **Comportement de vrais moteurs Claude/Codex** (qualité des réponses, outils) non testé.
4. `scripts/qa_unified_desktop.py` obsolète (6 pages au lieu de 7) et risque d'appeler de vrais comptes : NE PAS lancer ce script tant qu'il n'est pas sécurisé et corrigé. Son absence n'invalide pas les autres tests réellement exécutés, mais doit rester une dette visible.
5. Anciens decks adverses reconnus par leur nom seulement; autres restent présentés comme decks personnels.
6. Le candidat est non signé; un SHA servi par la même origine n'est pas une signature d'éditeur. Aucune CI GitHub.
7. Documentation source destinée à la future publication appelle 0.9.4 « préversion publique » alors que le dépôt public demeure 0.9.3; acceptable seulement comme préparation de release, ne pas présenter 0.9.4 comme déjà publiée.

## Prochaine action unique
**Réception Windows du propriétaire**, sous GO explicite pour installer (autorisation d'installation DISTINCTE du GO de publication). Avant mise à niveau, sauvegarder le dossier de données et vérifier le checksum du Setup candidat contre la valeur enregistrée. Vérifier démarrage, sept pages, vrais compteurs Saison/Cumul, ajout/deck principal, journal victoire et défaite sans création automatique de deck adverse, réponse du coach sur les défaites, Réglages/partage et Mises à jour. En cas de problème, interrompre la publication et documenter un correctif ciblé. Si accepté, demander **GO distinct** pour l'export public et la préversion v0.9.4 en respectant release-checklist.

Aucune modification de code ou publication produite pendant cet audit.
