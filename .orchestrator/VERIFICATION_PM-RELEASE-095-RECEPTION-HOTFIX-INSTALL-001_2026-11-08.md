# Audit indépendant ChatGPT — PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001
Date : 2026-11-08. Commit de rapport : `ddded3201a51ed014ba5563e5a88b2f6e1b63708`. Code correctif `00eecb35a7667db23656eafb94a795b0cb1cb7f8`.

## Verdict
**HOTFIX_BINARY_INSTALLED_EXECUTOR_VERIFIED / DATA_PRE_FIRST_LAUNCH_NOT_VERIFIED / OWNER_RECEPTION_PENDING / NOT_RELEASE_READY**.
GitHub compare `6c686aa...ddded32` : uniquement fichiers de suivi privés, aucun code, build ni publication nouvelle. La vérification du PC est fondée sur les mesures dans RESULT.md **effectuées par Codex**, non rejouées indépendamment par ChatGPT.

## Vérifications du rapport
- Setup local SHA `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212`, EXE installé après SHA `45D4EBA935DCA32C1898D18FD942668F4F52DA5A9B77A07A6E1F6234815B8145`. Le second distingue le correctif du candidat initial, tous deux appelés 0.9.5.
- Installation Inno normale, code 0, même AppId production, 797/797 fichiers de programme conformes, raccourcis et clé de désinstallation corrects.
- Avant le Setup, **nouvelle sauvegarde privée complète 315/315, 359 275 701 octets, SHA-256 identiques, source stable, restauration à blanc propre**, préservée. Sauvegarde D-293 également revalidée, 306/306.
- Après installation, **315 → 320** fichiers personnels, zéro préexistant manquant, **trois anciens fichiers modifiés et cinq ajoutés**; deux JSON préexistants de même taille et un journal allongé. Leur contenu n'a pas été examiné.
- Codex a été privé de Computer Use natif; le propriétaire déclare avoir décoché « Lancer PokeMind ». Une entrée Inno Run existe et les fichiers ont changé après fermeture du Setup. L'entrée Run seule ne prouve pas qu'un lancement a effectivement eu lieu; la source exacte des écritures et leur innocuité logique ne sont pas démontrées.
- Fumée après installation non exécutée par Codex, STOP respecté; aucun rollback ni altération volontaire des données, aucun push public.

## Décision
**Ne pas réinstaller une deuxième fois, ne pas restaurer automatiquement, ne pas demander un autre cycle de développement.** L'installation binaire est confirmée par les mesures de Codex, mais la réception fonctionnelle et la protection logique des préférences/decks ne le sont pas encore.

**Prochaine action unique : inspection visuelle manuelle par le propriétaire**, sans capture de données sensibles, de Deck Lab (images du deck), Réglages > Coach IA (« Ce que le coach reçoit » ouvert/fermé, autorisations de partage), langue/thème, présence de ses decks, deck principal, journaux et statistiques de combats. Si les deux régressions sont corrigées et que les données/préférences semblent intactes, enregistrer réception utilisateur après son accord explicite; la traçabilité du delta 3+5 reste une réserve d'audit, pas une preuve de perte. Si anomalie, arrêter et autoriser séparément une investigation ciblée en lecture seule comparant uniquement les champs pertinents aux sauvegardes sans publier le contenu privé. Préserver les deux sauvegardes. Aucune publication sans GO ultérieur distinct.
