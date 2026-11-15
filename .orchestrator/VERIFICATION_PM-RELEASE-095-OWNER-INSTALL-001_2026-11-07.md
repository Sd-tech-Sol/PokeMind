# Audit indépendant ChatGPT — PM-RELEASE-095-OWNER-INSTALL-001
Date : 2026-11-07. Rapport GitHub `b319ef7f1ceedb3239380fbaee0c64a940f0e496`. Source de la version 0.9.5 `24e9cc5`.

## Verdict
**INSTALLATION_REPORTED_SUCCESS / OWNER_RECEPTION_PENDING / NOT_RELEASE_READY**.
Le compare GitHub `f858b9f...b319ef7` confirme un seul commit de suivi/orchestration, sans code nouveau. L'audit est fondé sur le rapport complet de Claude et ses preuves structurées; ChatGPT n'a aucun accès direct aux fichiers binaires, au registre, à la sauvegarde ou aux données du PC de l'utilisateur. Les exécutions et hachages sont **rapportés par Claude, non rejoués indépendamment**.

## Éléments confirmés par lecture du rapport
- GO utilisateur pour installation seulement, pas publication.
- Sauvegarde avant installation sur volume local privé distinct du répertoire de données; 306/306 fichiers, 183 206 893 octets, SHA-256 source/copie égaux, source stable, simulation de restauration sans différence; sauvegarde conservée hors Git.
- Setup 0.9.5 local : SHA-256 déclaré identique à l'empreinte attendue `6E7E5CB2D63FA05BB96123E3A9DF6CFACEB37E90D21C9CD7417564526C0D68CB`; version 0.9.5, AppId de production correspondant à la 0.9.4 existante; non signé attendu.
- Installation interactive Inno, code 0, pas de désinstallation préalable, registre après 0.9.5, EXE SHA-256 `7121BBEB277594164621DDEECD6FAA3331FAFFB87EABD55024BB2BD6E0E9E6FF` déclaré identique au candidat, 797/797 fichiers de programme.
- Fumée EXE installé en root **synthétique vide** : 7 pages et démarrage, code 2 attendu compte tenu d'absence de decks/journaux de test.
- Aucun fichier de données préexistant manquant; 306 → 315 fichiers; **5 fichiers préexistants changés**, 9 nouveaux après démarrage de l'application, principalement catalogue/caches/journal/état. Les attributs de ces fichiers ne prouvent pas seuls l'absence de perte logique.
- Anomalie spécifique : fichier racine de réglages passé de 406 à 352 octets, contenu non consulté : aucun constat possible de conservation des préférences. L'installateur a laissé l'option « Lancer PokeMind » cochée et l'application s'est ouverte avant le contrôle d'intégrité post-installation. Ces faits sont clairement consignés et ne doivent pas être masqués.
- Aucun tag/release/push public.

## Réserves et prochain contrôle
**Ne pas qualifier V1 RELEASE_READY avant réception visuelle du propriétaire.** Lui demander d'inspecter dans l'interface, sans donner de contenu personnel à l'agent : langue, thème, modes de partage IA, deck principal, decks enregistrés, historique et statistiques des combats, Deck Lab > Statistiques (source/date/échantillon), historique du coach. Prioriser le réglage d'autorisation cloud suite au changement de taille du fichier préférences et aux notes de version 0.9.5 indiquant que le partage avec le coach peut être actif par défaut pour les nouvelles installations. Ne pas supposer que la mise à niveau a réinitialisé ce choix.

Si les paramètres sont incorrects, STOP avant toute restauration; établir localement une comparaison ciblée de **champs** entre sauvegarde et fichier actuel, sans exposer les valeurs ni secrets dans Git/chat, après permission explicite et sans modifier le fichier. Une mise à niveau ne devrait pas effacer silencieusement les choix de confidentialité. Préserver la sauvegarde. Ne pas lancer un mandat Claude Code additionnel avant cette inspection.

Une fois réception confirmée, publication seulement sur un **GO explicite distinct**.
