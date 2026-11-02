# PM-V1-E2E-WINDOWS-READINESS-FIX-001 — preuve assainie

2026-10-21 Québec. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
Correction ciblée sous fixtures; **V1 NOT_RELEASE_READY**.

## Mandat et prévol

Relais manuel reçu pour l'ID FIX exact, concordant avec STATE et premier NEXT_ACTION.
Synchronisation ff-only, arbre initial propre, de
`a78b3aafaed833c8f64023a4e0ccfbbf3f80c9a0` vers
`eb8a612f32b30aa069b22c0bfdb24018180b7a4d`, branche
`work/pm-v1-lotj-final-readiness-windows`. Aucune perte de travail local.
AGENTS, continuité/adoption V2, STATE, premier NEXT_ACTION, HANDOFF/RESULT/DECISIONS,
skill exécuteur, autonomie, mandat FIX intégral et audit E2E consultés.

CI initiale [39638367492](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39638367492)
au SHA exact **eb8a612f32b30aa069b22c0bfdb24018180b7a4d** :
Windows **1 failed/542 passed/2 skipped**, Ubuntu **542 passed/3 skipped**, success.
Même unique test connu : enfant `v1 readiness`, `DEMO_CLI_STEP_FAILED:v1`.
L'exception explicite au prérequis de CI verte s'applique à ce seul échec.
Les logs des deux runs historiques
[39467579068](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39467579068) et
[39468575580](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39468575580)
confirment le même arrêt. Ils restent rouges dans l'historique.

## Reproduction avant correctif : cause établie

Une base vide au schéma courant est créée dans un sous-répertoire temporaire neuf
de `data/local/test-runs`. Le helper `_guarded_command` existant lance uniquement
`python -m pokemind v1 readiness --db FIXTURE --json`, dans un enfant frais.
Audit hook, refus sockets/DNS, DB/fichiers hors fixture et processus externes restent
actifs. Aucun chemin de base/backup personnel n'est sélectionné ou inventorié.

Comparaison **avant modification produit**, même appel et même garde :

| Interpréteur Windows déjà installé | Retour enfant | Résultat |
|---|---|---|
| Python3.11.9 | 1 | `E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED` |
| Python3.13.15 | 0 | `NOT_RELEASE_READY` |

La trace enfant lue temporairement est réduite à cette chaîne sans chemin ni donnée :

```text
v1_readiness -> platform.system -> platform.uname -> platform.win32_ver
-> platform._syscmd_ver -> subprocess.check_output -> subprocess.Popen
-> garde E2E : refus du processus externe
```

L'implémentation **installée de CPython3.11.9** a été inspectée avec `inspect`.
`platform._syscmd_ver` essaie `ver` avec `shell=True`; même demander le nom du
système via `platform.system()` peut donc **tenter de lancer une commande système**
sous Windows. Le garde refuse cette tentative avant exécution. Le premier défaut
observé n'est ni une requête fournisseur ni une ouverture de DB extérieure.
La cause n'était pas un échec de facturation GitHub ou un test à supprimer.

Une régression dédiée a ensuite été ajoutée **avant le correctif produit** :

```powershell
py -3.11 -m pytest -q tests/test_windows_readiness_e2e.py -k fresh_guarded
```

Résultat avant correctif : **1 failed**, diagnostic neutre
`returncode=1`, `fault=E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED`,
`audit_event=subprocess.Popen`. Aucune sortie brute enfant n'est versionnée.

## Correctif produit minimal

`readiness.py` évite les helpers `platform.system/machine` sous Windows :
famille système issue de `sys.platform`, architecture issue de
`PROCESSOR_ARCHITEW6432`, puis `PROCESSOR_ARCHITECTURE`, comme le helper
Windows de CPython3.11, avec `unknown` si les deux manquent. Aucune commande
externe de repli. L'architecture déclarée par le processus n'atteste pas le matériel.
Les valeurs OS/architecture et le contrat JSON restent disponibles; le calcul
du support Python/OS utilise le même nom système sans une seconde sonde.
Le chemin non-Windows conserve ses appels existants; aucune nouvelle capacité Linux.

Aucun changement de schéma, règle Pokémon, conseil, données de joueur,
lecture des backups, source privée, calibration OCR ou planificateur.
Le rapport demeure `NOT_RELEASE_READY`, en lecture seule et sans réseau.

## Garde et diagnostic enfant

Toutes les conditions de refus dans `sys.addaudithook` sont conservées.
Le message de refus processus/réseau précise maintenant le nom de l'événement
audité, sans ses arguments. Le test parent restitue seulement étape, code retour,
famille de faute et événement d'une liste fermée; jamais stdout/stderr brut,
chemin ou contenu. Un test de confidentialité utilise des secrets **fictifs**
dans les deux flux et prouve leur absence du résumé.

Les cinq sondes négatives historiques sont conservées. Deux nouvelles sondes
injectées au début du calcul readiness tentent respectivement d'écrire un fichier
fictif hors de sa sous-fixture et de lancer un exécutable fictif : le même garde
les refuse, le fichier n'est pas créé et les octets DB restent identiques.
Aucun skip, xfail, xpass ou exception Windows n'a été ajouté au test.

## Validation locale

Environnement principal : Windows, Python3.11.9, pytest8.4.2 déjà présent.
Aucun paquet téléchargé/installé. GitHub conserve son pytest9.1.1 épinglé.

| Commande | Observation locale |
|---|---|
| `py -3.11 -m pytest -q tests/test_windows_readiness_e2e.py tests/test_user_journey_e2e.py tests/test_readiness.py tests/test_lot_g_readiness.py tests/test_lot_h_readiness.py` | **27 passed**, 36,20s; inclut le scénario E2E entier avec79 enfants et ses cinq sondes négatives |
| `python -m pytest -q tests/test_windows_readiness_e2e.py` sous Python3.13.15 | **4 passed**, 1,51s |
| `py -3.11 -m pytest -q` | **546 passed/3 skipped**, zéro échec, 300,46s |
| `py -3.11 -m compileall -q src tests scripts` | réussi |
| hygiène Git, inspection des seuls chemins préparés, `git diff --check` | réussis, y compris les nouveaux fichiers au staging final |

Trois skips locaux hérités : deux essais OCR réel absent/non attesté et un essai de lien symbolique non permis sur ce Windows. Aucun skip ajouté.

Quatre nouveaux cas : enfant readiness frais sans processus/écriture,
deux refus négatifs spécifiques readiness, résumé sans sortie brute.
Le scénario de79 CLI revalide la correction; aucun ancien mandat fonctionnel
E2E/BULK/PUBLIC n'est relancé comme une tâche ni campagne réseau.
Les suites recovery héritées utilisent exclusivement leurs fixtures jetables.

## Livraison et limites

Code, tests et guides publiés sur la branche autorisée seulement, sans merge,
reset ou force-push. STATE/RESULT/HANDOFF/NEXT_ACTION à AWAITING_AUDIT à livraison,
execute_now=false, autorisation FIX consommée, budget privé exécuté zéro.
CI finale **PENDING_CI au moment de publication** : contrôler Windows et Ubuntu
au SHA exact contenant ce rapport après push. Les résultats Actions à ce SHA sont
la preuve durable; la réussite locale ne remplace pas ce contrôle.

Les échecs antérieurs restent documentés à leurs SHA. Aucun statut VERIFIED
n'est attribué par Codex. La CI et ce correctif ne qualifient ni OCR réel,
captures d'entraînement, catalogue/normes mondiales, scheduler OS, ACL/durabilité
ou migration personnelle. Ancien clone7 toujours BLOCKED/0 plan; aucune nouvelle
création de backup moderne. Aucun accès/lecture/métadonnée de donnée personnelle,
GET fournisseur, installation, compte ou interaction TCG Live.

**STOP après livraison et contrôle CI pour audit indépendant ChatGPT.**
