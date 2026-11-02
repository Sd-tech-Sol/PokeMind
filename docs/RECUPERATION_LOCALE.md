# Sauvegarde, clone neuf et rétention — état H

État actif J,2026-10-15 : `LOT_J_RECOVERY_PROTOCOL.md` et
`VALIDATION_PROPRIETAIRE_V1_WINDOWS.md` remplacent les anciens parcours : cinq
prévisualisations indépendantes, clone7 puis clone13 neuf, activation explicite
`--db`; aucune migration de l'original. Les exemples historiques ci-dessous ne
confèrent aucun consentement. Remplacement existant/purge demeurent bloqués.

État I,2026-10-15 : `LOT_I_RECOVERY_PROTOCOL.md` précise les limites Windows
ACL/flush, la publication séparée des fichiers et le protocole de clone neuf.
`atomic_publish=false` dans le plan; manifeste orphelin/sidecar/lock inventoriés.
Remplacement existant et purge restent bloqués. Les exemples ci-dessous demeurent
des actes propriétaires distincts; leur présence ne les autorise pas.

2026-10-14 Québec. Exemples préparés; aucune opération réelle autorisée par ce guide.
Les données, manifestes et sauvegardes restent privés sous `data/local/`, hors Git.

## Sauvegarder après un ordre distinct

```text
python -m pokemind owner-plan --step backup --json
python -m pokemind backup plan --destination data/local/backups --json
python -m pokemind backup create --destination data/local/backups --apply --confirm-owner --json
python -m pokemind backup verify --backup BACKUP --json
```

`backup plan` est en lecture seule. L'application utilise sqlite3.backup, y compris
sur source WAL active; le snapshot est autonomisé en journal DELETE. Intégrité,
FK et contenu FTS sont contrôlés. Fichier puis manifeste sont publiés sans écraser
une collision. Une panne entre les deux peut laisser un fichier non attesté :
`backup status` le signale comme résidu, jamais comme backup vérifié.

Le fichier est fsync; les entrées du dossier le sont sous POSIX lorsque l'appel
réussit. Windows ne fournit pas ici de fsync de répertoire portable. Le résultat
expose `durability`; **aucune garantie power-loss ou transaction multifichier**.
Un chmod 0600 n'atteste pas les ACL Windows; choisir un stockage privé demeure
une responsabilité propriétaire distincte. Un ancien verrou n'est pas repris
sur simple PID mort : préserver le fichier pour revue offline.

## Vérifier puis publier un clone neuf

```text
python -m pokemind restore plan --backup BACKUP --db CLONE_NEUF --migrate-clone --json
python -m pokemind restore verify --backup BACKUP --migrate-clone --json
python -m pokemind owner-plan --step clone --backup BACKUP --clone CLONE_NEUF --json
python -m pokemind restore apply --backup BACKUP --db CLONE_NEUF --migrate-clone --apply --confirm-owner --json
```

La vérification éphémère n'active rien. L'application vers un nouveau fichier exige
son propre ordre. Le source et son manifeste sont réattestés avant publication;
checksum, taille, identité de fichier et relecture SQLite doivent concorder.
Sidecars WAL/SHM/journal, header WAL ou alias hardlink d'un backup sont refusés.
Une capture d'attestation utilise le même handle avant/après le hachage et vérifie
l'identité du chemin. Cela détecte des races; ce n'est pas une exclusion externe.

Un lien dur publie le clone sans écrasement. Un système de fichiers sans liens
durs échoue sans repli destructif. Un fichier apparu concurrentiellement reste
intact. Une mutation externe du clone empêche sa suppression automatique sur
échec : `RESTORE_ROLLBACK_INCOMPLETE` préserve les octets incertains. Les exceptions
ordinaires et les erreurs de flush ne produisent pas de succès verified.

**Toute cible existante demeure bloquée**, même idle ou fermée, même après
`--confirm-owner`. WAL/SHM/journal donnent `TARGET_IN_USE_OR_WAL_ACTIVE`; sinon
`RESTORE_EXISTING_TARGET_BLOCKED`. Un verrou PokeMind ou un verrou SQLite ponctuel
ne protège pas contre un programme externe entre contrôle et publication.
Les anciens helpers de rollback testent seulement des fixtures isolées; aucune
option CLI ne permet le remplacement. Le choix futur d'activer un clone neuf
hors ligne est une décision distincte, sans remplacement automatique de la base.

## Rétention : prévisualisation seulement

```text
python -m pokemind backup retention --destination data/local/backups --keep-last 7 --max-age-days 90 --json
python -m pokemind backup status --destination data/local/backups --json
```

Le plan revalide les backups sains et leurs manifestes; corrompus, absents et
inconnus ne satisfont pas keep_last. Les chemins internes d'un manifeste ne sont
jamais suivis. L'inventaire annonce la limite de 1000 manifestes; aucune application
n'est possible avec un inventaire incomplet. Le token porte sur contenu et
inventaire, et une variation invalide le plan.

H0 a retiré l'ancienne suppression à étapes : un processus extérieur peut détruire
les exemplaires retenus pendant la purge, et ni rollback de paire ni fsync ne
rend la suppression multifichier atomique. **`apply` est toujours refusé avec
`RETENTION_EXTERNAL_EXCLUSION_UNPROVEN`**, même avec token/confirmation valides.
Aucun bypass privé de rétention. La fonction produit reste BLOCKED, pas supprimée
du périmètre V1. Les anciens tests de suppression sont devenus des tests de refus
sans mutation; les injections de publication/rollback et keep_last sain restent.

`backup status` expose un inventaire agrégé des résidus : backups sans manifeste,
travaux interrompus, quarantaine et anciens dossiers de staging. Consultation
sans exigence de droit d'écriture. Aucun résidu n'est réparé ou supprimé
implicitement; aucune vraie purge effectuée en H. Les compteurs de résidus sont
bornés et ne déclarent pas un inventaire complet quand la borne est atteinte.
