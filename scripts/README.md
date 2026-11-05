# Scripts

Ce dossier contient uniquement les utilitaires locaux déclenchés manuellement.
PM-0001 n'installe aucun service, planificateur ou automatisme du client de jeu.

`local_gate.py` est la porte de qualité à lancer avant chaque push de code :
`.venv-ci311\Scripts\python.exe scripts\local_gate.py` (arguments pytest acceptés, ex. `-k motion`;
`--keep` conserve la copie). Il copie le dépôt sans `data/local` dans un dossier temporaire court et rejoue
compilation, hygiène Git, tests Qt et suite complète hors ligne, comme la CI.

Pour le joueur, l'archive et la restauration sont dans l'application (Réglages, Données : « Archiver… » et « Restaurer… », avec l'explorateur Windows). Les scripts servent au dépannage. `archive_data.py`, `reset_data.py` et `restore_data.py` (PokeMind fermé) : un zip vérifié de
tout `%LOCALAPPDATA%\PokeMind` dans `%LOCALAPPDATA%\PokeMind-archives`; une remise à zéro qui archive tout
d'abord et ne garde que le pointeur et des dossiers vides; une restauration qui archive d'abord le contenu
actuel et garde la date de chaque fichier (elle place chaque partie dans sa saison). Aucun contenu n'est lu.

`pokemind_build_backend.py` est un petit backend d'installation hors ligne. Il
ne lance aucune commande externe et n'accède pas au réseau.

`pokemind_update.ps1` est le lanceur déterministe des futures tâches publiques : il
appelle uniquement la CLI Python, jamais Codex ou un LLM. Il ne crée, n’active et ne
supprime aucune tâche Windows. Le LOT D teste seulement les manifests et commandes
simulées; l’activation réelle reste bloquée sans une future autorisation distincte.

Le lanceur exige maintenant une DB explicitement déclarée dans un espace PUBLIC
marqué; `knowledge update --public-only` contrôle ce périmètre avant mise à jour.
Aucun repli vers la base personnelle n'est permis. Un manifeste sans DB sélectionnée
contient un substitut obligatoire et ne peut pas être utilisé tel quel.

`collect_public_catalog.py` prépare par défaut un plan sans réseau ni fichiers.
Après autorisation ciblée du propriétaire seulement, son option d'exécution crée
un cache PUBLIC **neuf**, avec une enveloppe cumulative (GET et corps lus),0,5s
minimum entre GET, aucune redirection et aucun retry après erreur source.
Les limites maximales du programme ne constituent pas une autorisation de collecte.
Un dossier existant est refusé; le programme ne reprend pas une campagne arrêtée.
Un STOP source/local retourne un code non nul, avec compte rendu local conservé.
