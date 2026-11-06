# RESULT — PM-AUDIT-CLAUDE-PLAN : archiver et restaurer depuis l'application (D-281), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Demande du propriétaire après D-280 : pas de script ni de zip à la main;
l'archive doit être **dans l'interface**, avec l'explorateur Windows pour choisir où la mettre.
Session précédente (D-280) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D280_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D280_2026-11-05.md).

## Réglages → Données (commit `b3c533c`)
- **« Archiver… »** : la vraie boîte « Enregistrer sous » de Windows (Bureau, clé USB, OneDrive…), nom proposé
  `PokeMind-AAAAMMJJ-HHMMSS.zip` dans Documents. PokeMind reste ouvert : l'archive se fait en arrière-plan
  (pourcentage dans la barre d'état) et seulement quand aucune analyse, aucun import ni réponse du coach n'est
  en cours (sinon un message l'explique); rien de nouveau ne démarre pendant ce temps. Le zip est écrit sous
  un nom partiel, relu entier (CRC, mêmes noms et tailles), puis gardé; message final avec le chemin, la taille
  et un bouton « Afficher dans l'explorateur ».
- **« Restaurer… »** : la boîte « Ouvrir » de Windows pour choisir un zip; confirmation qui dit où les données
  actuelles seront archivées (à côté du zip choisi); un zip qui n'est pas une archive PokeMind, ou placé dans
  le dossier des données, est refusé tout de suite, rien n'est changé. Sinon PokeMind se ferme (comme la
  réinitialisation, l'opération en cours est arrêtée) et le lancement suivant, avant toute ouverture de
  `data/local` : archive vérifiée des données actuelles, puis données du zip en place avec la date de chaque
  fichier (chaque partie reste dans sa saison), puis un message. Un échec laisse tout en place.
- L'application ne touche que `data/local` (et l'espace `workspace` du terminal quand les données sont hors du
  projet); les tests synthétiques (`test-runs`) et les restes cachés de réinitialisation ne sont jamais
  archivés. Une archive faite par les scripts (dossier entier) se restaure aussi depuis l'application.
- Les scripts de D-280 restent, pour le dépannage seulement (PokeMind fermé). Ce sont les boîtes natives de
  Windows ici, alors que les autres boîtes de fichiers de l'application restent celles de Qt (langue choisie).

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `b3c533c` : Qt 110, cœur 1589 passed, 3 skipped.
- Tests : archive de l'application à l'endroit choisi (nom sans `.zip` complété, `test-runs` et restes exclus,
  refus dans le dossier des données); restauration demandée puis appliquée au lancement (données remplacées,
  dates gardées, ancien contenu archivé à côté du zip, une seule tentative); zip étranger ou placé dedans refusé
  avant la fermeture; zip abîmé au lancement : rien de changé; archive des scripts restaurable. Fenêtre : bouton
  « Archiver… » avec boîte native et zip vérifié, refus expliqué pendant une analyse; bouton « Restaurer… » :
  « Non » ne change rien, « Oui » écrit la demande et ferme. Capture de la section Données vérifiée.
- EXE recompilé depuis `b3c533c` et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-archive-ui-<id>`); installateur non publié `dist/installer/PokeMind-Setup-0.9.1-archive.exe`.

## Limites
- Pas de restauration d'une seule saison : une saison passée reste consultable dans le choix « Saison », sans
  rien déplacer (D-280).
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
