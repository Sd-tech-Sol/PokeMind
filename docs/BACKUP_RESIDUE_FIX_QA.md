# Correctif Stage 1B — préservation des résidus de sauvegarde

2026-10-15. Rapport d'exécution Codex, **audit indépendant ChatGPT requis**.
Branche unique `work/pm-v1-lotj-final-readiness-windows`. V1 **NOT_RELEASE_READY**.
Commit de code/tests : `544a183d17e340433173ba030768d6e65bd97496` (4 fichiers).
Le commit suivant porte les rapports; sa CI finale reste à vérifier séparément.

## Diagnostic et portée

Prévol demandé : `git status`, `git log`, `git diff`, `git ls-remote`.
Le worktree était propre à `9d20dfe788debd1f2fbe83c41ead3539cfdeee30`, sans
correctif local inédit. GitHub était à `f2cae122fdc818c30695efdb85cb8bd2f03922f9`.
Fetch puis pull **ff-only** de trois commits d'orchestration, sans perte de travail.
Le correctif demandé n'existait donc pas encore; exécution du mandat ciblé dans
NEXT_ACTION, sans réexécuter J0–J6.

Le défaut confirmé à l'ancienne ligne 424 effaçait `.inprogress` quand le renommage
diagnostique vers `.failed` échouait. Le test de crash historique simulait seulement
la panne de copie : le renommage réussissait, et le test comptait un `.failed`.
Il n'injectait ni cette deuxième panne ni une collision du nom `.failed`.
Le `finally` du manifeste et la libération du verrou pouvaient aussi effacer des
éléments utiles après erreur; le temporaire SQLite n'était pas réservé exclusivement.

## Comportement du correctif

- Aucun renommage diagnostique ni fallback de suppression en cas d'erreur : le
  `.inprogress` reste à sa place, les `.failed` existants ne sont jamais remplacés.
- Réservation exclusive `xb` du fichier de travail avant ouverture par SQLite;
  vérification de son identité après copie. Les publications SQLite/manifeste
  restent des hardlinks sans écrasement; un nom occupé fait échouer l'opération.
- La création du manifeste conserve son `.tmp`, même si écriture, fsync ou
  publication échouent. Option interne utilisée uniquement pour le backup;
  comportement des autres utilisateurs de `_atomic_bytes` inchangé.
- Le verrou du backup est conservé sur exception, y compris lorsqu'une panne
  survient pendant sa création. Aucun vol ou nettoyage automatique de verrou.
  Les autres utilisateurs de `_ProcessLock` conservent leur politique précédente.
- Les deux alias temporaires restent présents jusqu'à la vérification privée de
  SHA/taille/manifeste/SQLite/schéma/FK/FTS/sidecars/identité. Cette vérification
  interne accepte uniquement les deux alias exacts, avec même identité et deux
  liens par fichier; elle ne constitue pas une preuve publique de succès.
- `backup verify` garde sa signature et refuse les hardlinks supplémentaires,
  ainsi que les résidus associés `.inprogress`, `.failed` et `.tmp` de manifeste,
  même si un alias a été remplacé par un autre fichier. Un champ brut
  `manifest.state=verified` conservé après panne ne suffit jamais à valider le pair.

Le nettoyage normal retire seulement le verrou et les alias créés par l'opération
**après** publication, flush et vérification réussis. Les deux fichiers finaux
conservent les octets; les identités et empreintes des alias et fichiers publiés
sont recontrôlées avant retrait. Le résultat est préparé avant nettoyage : aucune
nouvelle lecture/hash susceptible d'échouer après le dernier retrait d'alias.
Si la libération du verrou ou le nettoyage d'un alias échoue, aucune tentative de
rollback, suppression de secours ou répétition automatique; les fichiers restants
sont conservés et une erreur neutre est renvoyée. Un nettoyage partiellement
effectué peut avoir retiré un alias après les contrôles réussis; les octets restent
dans le fichier final et l'autre résidu empêche la vérification publique.

Ce nettoyage normal distingue le retrait d'un nom de travail possédé et attesté
de la destruction d'un résidu sur erreur. Il ne promet ni absence absolue de
suppression dans le chemin réussi ni transaction atomique entre plusieurs fichiers.

## Tests Windows sur fixtures seulement

`tests/test_backup_residue_preservation.py` : **21 passed en 7,23 s**.
Première passe ciblée récupération G/H/I/J : **89 passed, 1 skipped en 32,47 s**
(avant les quatre derniers cas d'identité et le refus des résidus détachés).
La suite complète ci-dessous est l'autorité pour le code livré.

Les 21 nouveaux cas comprennent :

- Panne de copie avec `os.replace` forcé à échouer : le nouveau chemin ne dépend
  plus du renommage, et les octets partiels sont conservés.
- Échecs `os.link` SQLite/manifeste, fsync SQLite/manifeste/verrou, flush de
  répertoire et vérification finale; refus de nettoyage verrou/alias.
- Collisions des noms final, `.inprogress`, manifeste et `.tmp`, plus `.failed`
  préexistant conservé. Aucun écrasement ou suppression du fichier occupé.
- Remplacement d'un alias ou du fichier final et ajout d'un hardlink externe
  après vérification : identité changée refusée, fichier externe conservé.
- Succès normal schéma 7 avec contrôles SQLite/FK/FTS/SHA et vérification publique
  après nettoyage; les alias et le verrou existaient pendant la preuve interne.

Chaque scénario d'erreur compare exactement octets, taille, date de modification,
volume et identité de la source et du pair de sauvegarde préexistant synthétiques.
L'inventaire ne compte que l'ancienne sauvegarde comme vérifiée. Les tests de
crash et de collision hérités sont adaptés au `.inprogress` conservé et à l'état
inconnu d'un pair publié mais non attestable; aucune assertion de sûreté retirée.
Toutes les fixtures résident dans le sous-répertoire UUID créé par `local_tmp`;
seul ce répertoire généré est retiré par le teardown des tests.

Première suite complète Windows, fuseau local Toronto : **478 passed, 3 skipped,
1 failed en 141,45 s**. L'échec est
`test_first_use_cli_offline_synthetic_and_fresh_session`, étape `recommend`.
Il est reproduit seul (**1 failed en 10,54 s**) et expliqué par le code inchangé :
`demo.py` choisit la date UTC, tandis que `collection._strict_date` compare à
`date.today()` locale. À 02:24 UTC le 16 octobre, Toronto est encore le 15 octobre;
la recommandation refuse donc la date comme future. Ce chemin échoue avant tout
appel au backup. Diagnostic effectué exclusivement dans le workspace synthétique
jetable de la démo; aucun détail personnel consulté ou publié.

La suite est aussi exécutée avec `TZ=UTC` dans l'environnement du processus de
test et de ses enfants (pas de changement du fuseau Windows), pour valider le
code dans le contexte UTC de la CI : **479 passed, 3 skipped en 143,69 s**.
L'anomalie locale de démo reste **ouverte**, explicitement distincte du correctif
de préservation des résidus; ni collection personnelle ni politique des dates
réelles n'ont été modifiées pour élargir ce mandat ciblé.

Compilation réussie; hygiène des fichiers suivis et diffcheck réussis. Les trois
skips locaux sont deux essais OCR réels sans politique/opt-in et un test de
symlink Windows sans privilège; la vraie jonction Windows synthétique passe.
Seul `data/local/.gitkeep` est suivi sous les données locales. Le XML de tests
est synthétique, ignoré par Git et n'est pas publié dans le dépôt.

Commandes exécutées, sans installation locale :

```powershell
python -m pytest -q tests/test_backup_residue_preservation.py
python -m pytest -q --junitxml=data/local/ci/backup-residue-fix-windows.xml
$env:TZ = 'UTC' # processus de test uniquement; reproduction du contexte CI
python -m pytest -q --junitxml=data/local/ci/backup-residue-fix-windows-utc.xml
python -m compileall -q src tests scripts
python scripts/check_repo_hygiene.py
git diff --check
```

Le workflow Windows et Ubuntu hérité reste inchangé. Après push du code et des
rapports, comparer HEAD local, `git ls-remote` et `headSha` du run final, puis lire
les deux logs `ci_evidence` avec ce SHA exact. Le bilan final contient le lien de
cette CI; aucun SHA ne peut être incorporé dans son propre commit. Une preuve
de checkpoint est explicitement distincte d'une preuve du HEAD final.

Checkpoint de code **544a183d17e340433173ba030768d6e65bd97496**, CI
[run 38840559195](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38840559195)
terminée `success`, deux jobs et logs lus directement :

| Job | Résultat | Durée pytest | SHA du log `ci_evidence` |
| --- | --- | --- | --- |
| Windows 116779422102 | 480 passed, 2 skipped | 132,47 s | `544a183d17e340433173ba030768d6e65bd97496` |
| Ubuntu hérité 116779421808 | 479 passed, 3 skipped | 48,88 s | `544a183d17e340433173ba030768d6e65bd97496` |

Compilation/hygiène/diffcheck et étapes de publication des preuves réussies.
Windows CI permet le symlink (un succès de plus que le PC local); Ubuntu exclut
le vrai test de jonction Windows. Les deux autres exclusions sont les essais OCR
réels sans opt-in. **Cette CI précède le commit documentaire final** : consulter
Actions et le bilan terminal pour le run de ce dernier HEAD, sans substituer le
checkpoint. La CI verte ne résout pas l'anomalie de date locale décrite plus haut.

## Limites et prochaine action

Aucune base personnelle ni ancienne sauvegarde réelle lue ou touchée. Aucune
sauvegarde réelle, installation, migration, restauration, purge, capture, tâche
Windows ou interaction Pokémon exécutée. Seuls code, rapports et fixtures
synthétiques ont été utilisés. Aucun chemin absolu, SHA ou contenu privé publié.

`RESTORE_EXISTING_TARGET_BLOCKED` et `RETENTION_EXTERNAL_EXCLUSION_UNPROVEN`
restent inchangés. Aucun nouveau développement Linux; Ubuntu reste uniquement
une non-régression du workflow existant. Les courses d'un programme externe entre
contrôle et opération restent possibles : le verrou est coopératif. ACL,
chiffrement, flush du namespace Windows et résistance aux coupures non qualifiés.
Ce correctif conserve les résidus; il n'ajoute aucune réparation automatique.

**STOP pour audit indépendant ChatGPT du dernier SHA distant et de sa CI exacte.**
Stage 1B réel reste suspendu; une nouvelle instruction explicite est nécessaire
après audit pour une éventuelle sauvegarde. Aucun LOT K ni promotion release.
