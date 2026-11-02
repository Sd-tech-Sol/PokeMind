# J4 — récupération Windows préparée

Addendum Stage 1B (2026-10-15) : le correctif ciblé conserve désormais le
`.inprogress`, le `.tmp` de manifeste et le verrou sur erreur, sans renommage
vers `.failed`. Le nettoyage normal des alias possédés intervient après
publication et contrôles réussis; les résidus ne sont pas une attestation.
Lire [les preuves et limites du correctif](BACKUP_RESIDUE_FIX_QA.md).
Stage 1B personnel reste suspendu jusqu'à audit et nouvel ordre explicite.

2026-10-15. Tests J et suites F/G/H/I sur fixtures : identité/empreinte source et
manifeste, hardlinks, symlinks/reparse points, WAL/SHM/journal, écrivains concurrents,
collision de publication, panne entre SQLite et manifeste, rollback/résidus,
schéma historique 7→13 et recherche/FK/FTS. Aucun backup/clone/migration personnel J.

Le prévol propriétaire de clone utilise maintenant le même refus de reparse points
que la récupération. Les étapes `owner-plan --step verify` et `activate` complètent
les cinq prévisualisations : backup, verify, clone neuf, migration dans un clone
distinct, activation par sélection explicite `--db`. `activate` exige un schéma
courant sain et un backup vérifié. Ce contrôle ne prouve pas que le backup et le
clone représentent encore la dernière écriture du source : comparaison locale
des historiques et décision du propriétaire demeurent indispensables.

La revue finale J a aussi corrigé la CLI : `_db_for` et `_private_path` contrôlent
le chemin lexical et ses ancêtres **avant** `resolve()`, qui aurait effacé une
jonction. Un test Windows crée une vraie jonction synthétique sans privilège de
symlink, puis vérifie le refus CLI de base, backup et clone avant toute lecture/
création. La jonction de test seule est retirée, sans suppression récursive de
sa cible. Cette régression a son propre commit et sa propre CI finale; l'ancienne
CI documentaire9bcd06c ne suffit pas. Les races externes après contrôle restent
une limite, aucun verrou d'exclusion universel n'est revendiqué.

Tout fichier existant reste protégé par `RESTORE_EXISTING_TARGET_BLOCKED`;
`apply_retention` reste fermé par `RETENTION_EXTERNAL_EXCLUSION_UNPROVEN`.
Aucun flag de bypass. Alternative de conservation : garder source, backups,
manifestes, clones et résidus; choisir de nouveaux noms plutôt que supprimer.
Les prévisualisations de rétention permettent seulement d'estimer les besoins.

Les publications de fichiers individuels ne forment aucune transaction multifichier.
Les tests d'exceptions ne prouvent pas la durabilité lors d'une panne de courant.
`windows_acl_verified=false`, chiffrement non implémenté/constaté, flush du
namespace Windows non prouvé. Aucun changement d'ACL ou de chiffrement effectué.

Après décision propriétaire, vérifier localement les droits du dossier choisi
(propriétaire, héritage, groupes autorisés, accès de sauvegarde) et la protection
du volume déjà disponible. Ne pas publier identités/ACL/chemins/clés dans Git.
Ne pas activer chiffrement, modifier ACL, fermer des programmes ou changer un
service sous couvert d'un simple prévol. Faire attester leur portée séparément.
Un verrou coopératif ou l'absence de sidecar n'exclut pas un autre programme.

## Modèle d'audit à remplir localement, après autorisation

Créer volontairement un rapport sous `data/local/validation-owner/`, jamais dans
Git. Ce modèle ne contient aucune valeur personnelle; il ne crée rien par lui-même.

```text
action_id / ordre exact reçu / date UTC : À REMPLIR LOCALEMENT
source / backup / manifeste / clone choisi : À REMPLIR LOCALEMENT
version code / commande exécutée / résultat neutre : À REMPLIR LOCALEMENT
ACL et stockage examinés / chiffrement disponible : inconnu tant que non observé
exclusion des écrivains externes : non prouvée par PokeMind
identité + SHA avant/après de chaque artefact : À MESURER LOCALEMENT
schéma source / clone; intégrité / FK / contenu FTS : À MESURER LOCALEMENT
comptes et comparaison des versions, combats, liens, observations : À COMPARER LOCALEMENT
résidus / erreurs / aucun effacement implicite : À CONSIGNER LOCALEMENT
activation --db choisie et annulation possible : ordre séparé requis
preuve audit indépendant : absente avant revue
```

Le [parcours propriétaire](VALIDATION_PROPRIETAIRE_V1_WINDOWS.md) donne les commandes
de chaque prévisualisation et les gestes futurs. Les répétitions automatiques
restent `tests/test_lot_h_commissioning.py`, `test_lot_j_recovery.py` et suites de
récupération héritées; aucune preuve personnelle n'est simulée en succès.
