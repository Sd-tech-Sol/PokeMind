# PM-RELEASE-095-CONTROLLED-OWNER-INSTALL-011 — BLOCKED_PREINSTALL / AWAITING_AUDIT / STOP

2026-11-12. Branche privée `work/pm-v1-lotj-final-readiness-windows` synchronisée en fast-forward `8c7f88d` → **`3d4a843e422b09e954372baabea516c8e9729d59`**, arbre initial propre. GO propriétaire D-305 reconnu. **Arrêt en phase A : fichier SQLite principal absent au chemin canonique dans la racine active vérifiée. Aucune sauvegarde ni installation commencée.** Constat local de l'exécuteur, non vérifié indépendamment sur Windows par ChatGPT.

## Contrôles effectués

| Contrôle | Résultat |
|---|---|
| Setup 009 exact, fichier et ancêtres sans reparse; SHA-256 recalculé et fichier `.sha256` adjacent concordants | PASS |
| Setup : 39 825 876 octets, version PE 0.9.5, bootstrap Inno x86 | PASS |
| EXE de staging : 3 964 765 octets, version PE 0.9.5, charge utile x64, SHA-256 recalculé | PASS |
| Clé uninstall HKCU de production, lue dans les vues 32/64 : PokeMind 0.9.5, chemins cohérents avec DefaultDirName et désinstallation | PASS |
| EXE installé : version 0.9.5 et architecture x64; session non élevée | PASS |
| Raccourci menu Démarrer et raccourci bureau lorsqu'existant : cibles cohérentes | PASS |
| Aucun processus PokeMind ni mutex testé présent | PASS |
| Racine autonome et pointeur exact du projet concordants; override courant absent | PASS |
| Présence du fichier SQLite principal attendu dans cette racine | **STOP : ABSENT** |
| Deux noms `synthetic_v2.txt` et `synthetic_v2.json` : métadonnées de présence/type seulement | PRÉSENTS, non reparse |
| Inventaire complet, ACL, capacité, sauvegarde SQLite et copies de secours | SKIP, arrêt préalable |
| Installation, contrôles après installation et réception GUI | SKIP |

Identité publique des artefacts, recalculée avec `Get-FileHash -Algorithm SHA256` :

- Source du candidat 009 : `231e6ebc9b99c2adbba95ca217287542bb3e897c`.
- Setup : `ab83f9755c84ff34a3c08b8c3c978236fbfc794e20734daaf5cd51e3627feeac`.
- EXE de staging : `25ffe17e64b8714e1ffc9fe8de17fb0ad617bbf6d0831c5c7d9bac6598114837`.
- AppId de production contrôlé : `{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}`. Candidat déclaré non signé; aucune signature revendiquée.

## Barrière respectée et limites

La localisation a été déterminée sans import applicatif selon le contrat `standalone` de `data_location.py`; seul le pointeur de configuration borné a été lu pour extraire l'entrée exacte du projet. Le chemin de la DB a été dérivé du nom canonique de `paths.py`. Un contrôle ciblé de métadonnées a confirmé son absence après l'échec initial `ItemNotFoundException`; ce diagnostic n'est ni une nouvelle tentative de sauvegarde ni une recherche d'autres bases. Aucune conclusion sur une perte de données, leur emplacement alternatif ou leur intégrité générale.

| Protection préalable | Créée / vérifiée |
|---|---|
| Nouvelle sauvegarde SQLite | non / non |
| Copie complète des données | non / non |
| Copie de l'ancien programme | non / non |

Phase A : **STOP**; phases B/C : **SKIP**; phase D : rapport assaini. Setup exécuté **0 fois**, code retour **N/A**; nouvelle empreinte installée **non contrôlée**, candidat 009 **non installé**. Programme initial laissé en place, non lancé et aucun processus fermé. Réception GUI : **PENDING_OWNER**, sans sollicitation d'acceptation post-installation puisqu'il n'y a pas eu d'installation.

Aucun contenu de DB/deck/journal/préférence/export lu ou haché; les deux exports sont laissés en place. Aucun parcours de l'arbre privé, copie, répertoire de secours, sauvegarde, restauration, nettoyage, import, démo, test source, build ou publication. Aucune donnée personnelle, valeur du pointeur, chemin absolu, hash privé ou log brut dans Git. Les seules écritures concernent l'orchestration assainie; RESULT 010 archivé.

Statut **BLOCKED_PREINSTALL**, raison `ACTIVE_DATABASE_ABSENT_AT_EXPECTED_PATH`. Mandat 011 **CONSUMED**, sans relance automatique; audit ChatGPT requis avant tout diagnostic ciblé ou reprise du mandat. GO d'installation conditionnel enregistré mais non exécuté, aucune autorisation de publication. Vérification du HEAD distant et des checks au SHA exact du rapport après push; aucune nouvelle CI verte ni réception GUI revendiquée. **NOT_RELEASE_READY / STOP.**
