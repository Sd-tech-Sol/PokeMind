# Audit indépendant ChatGPT — PM-RELEASE-095-RECEPTION-HOTFIX-001
Date : 2026-11-07. Code `00eecb35a7667db23656eafb94a795b0cb1cb7f8`. Rapport `b74a95705337b2c10b097529daff00adaf5050ca`.

## Verdict
**VERIFIED_SOURCE / HOTFIX_CANDIDATE_READY_FOR_OWNER_INSTALL / OWNER_RECEPTION_PENDING / NOT_RELEASE_READY.**

Le compare GitHub `b669def...b74a957` confirme deux commits, un de code/tests et un de suivi. ChatGPT a relu les différences et le rapport du dépôt privé. Les tests, fumées Windows et les binaires du PC sont des **preuves rapportées par Claude**, non exécutées ou inspectées de manière indépendante par ChatGPT.

### Constat confirmé dans le code
- Images absentes : les métadonnées TCGdex enregistrent `retrieved_at` en UTC, mais `as_of` est un jour local; à 21:54 au Québec, date UTC déjà au lendemain, `stamp[:10] > as_of` refusait tous les alias du catalogue et empêchait la résolution d'identité nécessaire à la récupération d'image. `database.local_day()` convertit les horodatages avec fuseau en date locale et conserve les dates nues. Appels ciblés dans `set_code_aliases`, `deck_library`, `deck_knowledge` et `local_ocr`.
- Contraste et géométrie : règles QSS explicites pour les items normaux/survolés/sélectionnés; sélecteurs de réglages ajustés au texte, repositionnés sous les explications longues; taille des textes d'aide augmentée. Tests Qt, langues et thèmes présents.
- Le test de régression du catalogue du soir est pertinent : il aurait échoué sur l'ancienne comparaison et cible le chemin de résolution réel.

### Résultats rapportés par Claude
- Porte complète isolée sur commit `00eecb3` : Qt 122, cœur 1639 réussis, 0 échec, 3 ignorés.
- Sur copie du catalogue et du cache publics : 0/13 illustrations avant; 12/13 après, le dernier élément étant fictif et absent du catalogue.
- Build Windows non signé depuis `00eecb3`, version 0.9.5, PYZ avec fix, scan confidentiel déclaré CLEAN, fumée gelée 7 pages.
- SHA-256 Setup local : `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212`. Chemin rapporté : `dist/installer-candidate-0.9.5-00eecb3/PokeMind-Setup-0.9.5.exe`. Aucune installation réelle, aucune publication.

### Réserves
- Le chemin de galerie sur la version EXE compilée n'a pas été parcouru en UI Automation après le hotfix, quoique le code corrigé ait été constaté dans l'archive et le chemin exécuté en Python Windows. L'installation propriétaire conserve l'ancien EXE jusqu'au GO.
- La correction du menu n'a pas encore été confirmée visuellement sur le PC de l'utilisateur. Un test de largeur n'est pas une garantie pour chaque DPI.
- D'autres comparaisons de timestamps UTC aux dates locales dans des fonctions d'import ont été signalées; pas de régression observée et aucun correctif hors portée nécessaire ici.
- **Important : cette 0.9.5 porte le même numéro que la 0.9.5 déjà installée.** La version seule ne distingue pas les deux binaires. Utiliser SHA-256 exact et source `00eecb3` pour tout contrôle, éviter une mise à jour automatique qui ne voit qu'une version égale.

## Prochaine action unique
Obtenir le **GO explicite pour remplacer l'installation réelle par le Setup hotfix 0.9.5**. Après autorisation, contrôler sauvegarde existante et son intégrité, fermer PokeMind, vérifier SHA-256 Setup exact et AppId de production, installer par assistant normal (décocher « Lancer PokeMind » pour inspection post-installation avant ouverture), vérifier la conservation des données par comparaison au snapshot pris immédiatement avant mise à niveau et la cohérence binaire; puis faire réception visuelle de la galerie du Deck Lab et du sélecteur Coach IA par le propriétaire. Ne pas déclarer réception validée avant confirmation. Préserver les sauvegardes et ancien installateur; pas de tag/push/release publique sans GO distinct.
