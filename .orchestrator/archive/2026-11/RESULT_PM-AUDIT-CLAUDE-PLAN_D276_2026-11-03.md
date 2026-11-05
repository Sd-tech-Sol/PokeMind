# RESULT — PM-AUDIT-CLAUDE-PLAN : réinitialisation complète de PokeMind (D-276), 2026-11-03

Exécuteur : Claude Code (Opus 5.5). Demande du propriétaire : pouvoir remettre l'application comme à sa
toute première ouverture (parties, journaux, nombre de parties, connaissances, tout), avec un avertissement.
Session précédente (D-275, recherche web du coach) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D275_2026-11-03.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D275_2026-11-03.md).

## Fait (commit `1593f0b`)
- **Réglages → Données → Réinitialiser PokeMind** : avertissement (ce qui est retiré, ce qui n'est pas
  touché), case « Garder une copie de mes données actuelles (recommandé) » cochée par défaut, bouton par
  défaut « Annuler »; sans copie, une seconde confirmation.
- La fenêtre écrit seulement une demande (`data/local/reset-request.json`, avec son numéro de processus),
  se ferme sans réécrire les préférences et relance PokeMind (`desktop.app.relaunch` : même EXE, ou
  `python -m pokemind desktop` depuis les sources).
- Au lancement suivant, `pokemind.data_reset.apply` agit avant toute ouverture de fichier dans `data/local`,
  après la fin du processus précédent : tout le contenu de `data/local` passe en un bloc dans
  `avant-reinitialisation-AAAAMMJJ-HHMMSS` (même volume, déplacement instantané). Sans copie, ce dossier est
  renommé en dossier caché puis effacé. Un élément verrouillé : tout revient en place, rien n'est effacé, et
  la demande n'est tentée qu'une fois. Les copies antérieures ne sont jamais déplacées; le pointeur de
  dossier de données est conservé.
- Message au propriétaire (copie gardée et son emplacement, effacement, ou échec), puis l'assistant de
  bienvenue comme au premier lancement. `data_location.legacy_data` ignore la demande et les copies.
- Guides, PRIVACY et CHANGELOG à jour.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `1593f0b` : Qt 102, cœur 1559 réussis, 3 ignorés.
- Tests : copie datée par défaut et une seule exécution; effacement sans toucher une copie antérieure;
  verrou simulé = retour complet; demande invalide ignorée; attente de la fin du processus qui ferme;
  bouton (Annuler, seconde confirmation, fermeture sans préférences, relance unique); lancement qui applique
  la demande avant l'assistant.
- Captures hors écran sur racine inventée : ligne des Réglages et avertissement lisibles.
- EXE recompilé depuis `1593f0b` (78 modules `pokemind` identiques aux sources, aucun module QA; fumées projet, autonome et copie installée : sortie 0) et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-reset-<id>`); installateur non publié
  `dist/installer/PokeMind-Setup-0.9.1-reinitialisation.exe`.

## Limites
- Non exécuté sur les vraies données du propriétaire (aucun agent ne les ouvre).
- Pas touchés : le dossier de travail du terminal, les historiques gardés par Codex/Claude dans leurs propres
  dossiers, et, en mode dossier projet, l'original resté dans le projet après une copie hors du projet.
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
