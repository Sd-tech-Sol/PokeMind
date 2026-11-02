# I5 — clone neuf isolé sous Windows, protocole préparé

La répétition `test_lot_h_commissioning.py` et les tests I utilisent uniquement des
fixtures : vraie structure synthétique 7, backup SQLite autonome, manifeste vérifié,
clone neuf migré 13, comparaison des historiques, FK/FTS et octets du source.
Ce résultat ne correspond pas à une migration de la base personnelle.

Le plan de backup expose maintenant `atomic_publish=false`, publication séparée
de deux fichiers, `multifile_atomic=false`, `power_loss_guaranteed=false` et
`windows_acl_verified=false`. Chmod 600 ne prouve pas les ACL NTFS. Le refus des
jonctions/reparse points Windows complète les contrôles de symlinks; il ne fournit
pas d'exclusion durable contre un processus ayant les mêmes droits.

Une panne entre SQLite et manifeste peut laisser une base sans attestation : elle
est conservée et inventoriée, jamais présentée comme backup vérifié. Les résidus
incluent désormais manifeste orphelin, lock, WAL/SHM/journal, travail interrompu et
base non attestée. Aucun nettoyage automatique. Les suites G/H conservent les
pannes fsync, collisions, changement de source/manifeste, hardlinks, processus
idle/writer/WAL, disque plein, rollback et fichiers adverses.

## Alternative au remplacement de l'original — à faire autoriser séparément

1. Choisir explicitement le source, un dossier privé de backups et un **nouveau**
   nom de clone local. Fermer les applications et suspendre les écrivains externes
   par une procédure propriétaire auditée; ne jamais considérer l'absence de WAL
   ou un lock coopératif comme preuve suffisante d'exclusion.
2. Examiner les ACL du dossier choisi et l'accès disque/chiffrement local. I ne
   modifie aucune ACL et ne chiffre pas les fichiers; chiffrement/clé et garantie
   de flush/power-loss restent à établir pour la reprise opérationnelle finale.
3. Prévol `owner-plan --step backup` et `backup plan`, sur les chemins autorisés.
   Ces commandes lisent la base choisie, elles ne constituent pas l'autorisation.
4. Après ordre de backup distinct : créer puis vérifier le backup et son manifeste.
   Inspecter les résidus si échec; ne rien purger. Leur vérification ne prouve pas
   que la source est encore au même état après une nouvelle écriture externe.
5. Après ordre de clone distinct : `restore plan`, puis clone neuf sans écrasement;
   migration 7→13 dans ce clone seulement si explicitement autorisée. Refuser
   cible existante, alias, sidecars ou absence de publication sûre.
6. Comparer les historiques, contenus et FK/FTS. Une activation éventuelle consiste
   à choisir explicitement le clone via `--db`; elle ne remplace pas l'original.
   Garder source et backup. Réautoriser chaque nouveau clone/migration/activation.

**Remplacement existant et rétention/purge demeurent BLOCKED_WITH_REASON**, même
avec token/confirmation : exclusion externe et keep_last multifichier non prouvés.
Ce protocole préparé n'ouvre aucun bypass. Pour répétition sûre, utiliser
`python -m pytest -q tests/test_lot_h_commissioning.py tests/test_lot_i_safety.py`.
Pour des actes réels, consulter `MISE_EN_SERVICE_PROPRIETAIRE.md`.
