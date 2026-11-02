# PM-V1-ONE-COMMAND-LOCAL-COACH-001 — preuves assainies

2026-10-25. **AWAITING_AUDIT**, constat d'exécution **CODEX_LOCAL_REPORTED**.
Le propriétaire a lancé manuellement le mandat D-229; aucune veille installée.

## Prévol et résultat réel prioritaire

Git propre au départ, synchronisé ff-only sans perte sur la branche autorisée à
`15ea275e735163be4500dd43adc087c4e5f96740`. [CI40257655262](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40257655262) :
Windows job121362877618 **1264 passed/2 skipped**, Ubuntu job121362877493
**1263 passed/3 skipped**, succès au même SHA. Neuf marqueurs hérités par job;
registres canoniques concordants. Prévol local **RUNTIME_READY**, sans DB privée.

Les seuls rapports canoniques dans le dossier dérivé autorisé ont été découverts
directement, bornés et validés avec `legacy_bridge.saved_report`. Le rapport réel
corrigé et son Learning Loop existaient; leur bilan, classement, preuves et
recommandations ont été affichés avant de coder. Aucun retraitement réel, scan
des journaux, accès à SQLite personnelle ou GET n'était nécessaire. Un premier
affichage Python direct a rencontré l'encodage CP1252; la même lecture a été
affichée en UTF-8. Aucune analyse répétée pour cet incident d'affichage.

Après développement, le véritable point d'entrée CLI a affiché ce même rapport,
avec joueur mémorisé exclusivement localement. La commande réelle sans argument
de joueur a ensuite réussi : pas de retraitement, DB ou réseau, et octets/mtimes
des snapshots, Learning Loop et fichiers de contrôle locaux inchangés. Les liens
HTTPS conservés sont affichés. Aucun nom, chemin absolu, empreinte privée,
classement personnel ou contenu des rapports n'est inclus dans cette preuve.

## Changement livré

`battle_coach` orchestre `battle_batch`, `legacy_bridge` et Learning Loop,
sans nouvelle base ni second moteur de connaissances. CLI traitée avant toute
recherche de racine ou DB implicite. Chemins fixes sous le projet; aucune option
de dossier/DB arbitraire ni racine tirée d'un autre projet.

Découverte directe :5 000 entrées,256Mio de candidats,32Mio par rapport. Validation
canonique et sémantique existante, rapports vides exclus du coaching réel;
classement date/version/mtime/nom stable, alias ignorés. Le Learning Loop apparié
est validé; un journal manquant/corrompu ne provoque pas une réanalyse. Index
`latest.json` récupéré via découverte validée, jamais suivi aveuglément; contrôles
16Kio, écriture staging/fsync/remplacement atomique, identité/stabilité avant
publication et fichiers immuables conservés. Index identique non réécrit.
Une panne/concurrence conserve les résultats précédents et peut laisser un
staging, sans suppression de fichier utilisateur.

Joueur conservé dans un fichier local distinct, non dans Git. Conflit de joueur
refusé. Sans rapport et avec journaux admissibles : une invocation batch existante
`apply=True`. `--update` réactualise les matchs et connaissances déjà locales,
sans appeler le collecteur PUBLIC. Aucun service ni watcher. Les statuts absent,
aucun match valide et blocage ont des codes de sortie distincts et neutres.

DB13 neuve compatible : imports idempotents existants sans attestation de version
jouée. Legacy7 : prévol/références selon moteur existant, import bloqué sans
migration, conseils/mémoire dérivée disponibles. DB absente : aucune création.
Le lot réel a seulement consulté les instantanés, sans ouvrir la vraie DB.

Le rendu partagé confondait la fin `s:/` de `https://` avec une lettre de disque
Windows. La borne du motif de masquage est corrigée; contrôles/HTML/chemins et
URL dangereuses restent neutralisés. Les compteurs PUBLIC historiques sont
qualifiés comme tels dans le coach, sans prétendre une collecte pendant l'appel.

## Vérification technique

**165 tests ciblés passés, 50 nouveaux et115 hérités**, sur les quatre chemins
littéraux `test_battle_coach.py`, `test_legacy_batch_bridge.py`,
`test_battle_batch.py`, `test_battle_logs.py`. Fixtures neuves conservées dans
un espace synthétique isolé; sans conftest, découverte, autochargement de plugins
externes, bytecode ou cache pytest. Garde locale interdisant réseau, accès aux
vrais emplacements privés et suppression. Aucun fichier réel utilisé en fixture.

Parcours intégrés : sortie absente, aucun log, ancien3/corrigé4, index
absent/corrompu/périmé/surdimensionné, mêmes octets/mtime à la reprise, nouvelle
partie et déduplication, historique immuable, vraie fixture SQL7 et DB13 neuve,
absence de DB, acteur manquant/conflit/invalide, CLI humain/JSON CP1252→UTF-8,
première analyse CLI puis update et reprise sans joueur, contenu hostile,
liens HTTPS, URL dangereuses, caps et refus hardlinks/redirections/reparse.
Les restrictions de symlink Windows sont couvertes par simulation du contrat
reparse si la création du lien est refusée, sans élévation ou commande de jonction.
Publication atomique interrompue/concurrente et échec mémoire ne remplacent pas
l'ancien index ou les snapshots.

Compilation en mémoire, tabnanny, hygiène Git et `git diff --check` contrôlés.
Première publication `216555f2a282bc65c292332aa9d6efd693371833`,
[CI40261934853](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40261934853) :
Ubuntu1313/3 réussi; Windows1314/2 mais une erreur de teardown synthétique
`WinError32` empêchait le succès du job. Le test CLI conserve le garde réseau
autouse mais rétablit maintenant son répertoire courant dans un contexte local
avant le nettoyage de la fixture. Aucun échec fonctionnel ni donnée propriétaire
concernés; ce premier run n'est pas présenté comme CI verte. Le correctif doit
être validé par une nouvelle CI complète au HEAD de cette livraison.
La CI complète GitHub utilise uniquement ses fixtures isolées; aucun workflow
modifié. **Contrôle final après push obligatoire** : HEAD distant égal au SHA
local publié, deux jobs terminés avec succès au même SHA, neuf marqueurs hérités
et deux empreintes canoniques des registres égales entre Windows et Ubuntu.
Le run Actions attaché au commit contenant ce document est la preuve durable
du contrôle technique final; aucun résultat privé du PC n'est certifié par CI.

## Arrêt

Aucun GET fournisseur, import réel, changement de schéma7→13, nouvelle DB,
backup, restauration, suppression, installation, OCR, capture, scheduler,
clipboard ou interaction avec le jeu. Code/tests/guides/rapports assainis seuls
publiés sur la branche autorisée; pas de merge ni force-push. **AWAITING_AUDIT**,
`execute_now=false`, `consumed=true`; aucun nouveau mandat READY. V1
**NOT_RELEASE_READY**, portes restantes inchangées.
