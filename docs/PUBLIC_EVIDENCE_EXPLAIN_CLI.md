# Lire les preuves PUBLIC dans la CLI

Mandat `PM-V1-PUBLIC-EVIDENCE-EXPLAIN-CLI-001`, 23 octobre 2026.
**V1 NOT_RELEASE_READY.** Les observations des caches du PC sont
`CODEX_LOCAL_REPORTED`; les tests GitHub utilisent des données inventées.

## Consulter toutes les compositions ou une seule

Lancer depuis la racine PokeMind. La commande utilise seulement les deux caches
PUBLIC fixes déjà autorisés. Elle ne recherche aucun dossier, ne télécharge
rien et ne sélectionne jamais la base personnelle.

```powershell
python -m pokemind meta public-identity-explain --as-of 2026-10-23
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --json
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --selector 581:1
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --selector 581:1 --json
```

Sans filtre, les 28 compositions du cache observé sont affichées. Un sélecteur
désigne une composition : si plusieurs placements ont la même liste, leurs
sélecteurs restent affichés ensemble. `581:1`, `581:10` et `582:5` désignent ainsi
une même composition observée. Un sélecteur inconnu produit une erreur lisible
et le code de sortie 2, sans recherche d’une autre source.

La commande exige `--as-of YYYY-MM-DD`. Elle n’accepte pas `--db`,
`--reference-db`, un chemin alternatif ou une option de téléchargement.
Un cache absent ou refusé arrête la lecture. Ne pas utiliser cette commande
depuis un autre dossier pour essayer de retrouver les données.

## Comprendre la sortie

`SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE` signifie que les enregistrements
SQLite sont observables, mais que les sources complètes des listes n’ont pas
été revalidées. Les marqueurs, registres de requêtes et pages nécessaires à ce
contrôle demeurent hors du périmètre. La commande ne remplace pas ce contrôle.

Chaque composition montre :

- ses sélecteurs et la couverture des identités de catalogue, en lignes et copies;
- les identités inconnues avec quantité, nom, code et numéro;
- les blocages séparés du Standard présentiel (`in_person`) et de Live;
- les métadonnées publiques de source et leur date, explicitement non revalidées;
- la prochaine preuve requise et une commande pour relire cette composition.

La matrice distingue toujours le nom de liste et les candidats descriptifs du
catalogue. Par exemple, `Fire Energy MEE 10` et le candidat `Basic Fire Energy`
ne deviennent pas équivalents par ressemblance de nom. Le code `30C` reste
ambigu entre les éditions du pont. Une preuve directe de l’identité et de
l’édition demeure nécessaire. Les dix inconnues (7 MEE et 3 30C) restent
inconnues; aucune équivalence nouvelle n’est ajoutée.

Les deux registres de rotation du cache ne fournissent aucune rotation vérifiée
active au 23 octobre : la dernière revue est bornée au 22 octobre. C’est une
limite des preuves du cerveau, pas une conclusion sur les règles externes.
Les exceptions de quotas, limites spéciales et disponibilités Live par
impression ne sont pas certifiées. Les 28 statuts présentiel et Live demeurent
`unknown`, même si une liste a 60 cartes ou un candidat de catalogue concordant.

## Comparer les bons dénominateurs

Le résumé global observé est de 32 placements / 28 compositions,
158 identités résolues sur 168 identités listées uniques,
626 lignes résolues sur 698, et 1439 copies résolues sur 1680.
Les compositions identiques sont dédupliquées; les placements ne multiplient
pas leurs cartes. Les copies ne sont pas des identités supplémentaires.

Le filtre conserve ce résumé global à titre de contexte et calcule séparément
les totaux de la sélection. Les lignes et copies de la matrice filtrée se
rapportent seulement aux compositions retenues. Ne pas comparer un numérateur
filtré au dénominateur global.

## JSON et erreurs

Le contrat est `schema_version=1`, `model=public-identity-explain-v1`.
`totals` décrit le cache entier; `selected_totals`, `compositions` et
`identity_matrix` décrivent la sélection. Chaque composition conserve
`in_person=unknown`, `live=unknown`, `blockers` et `next_evidence` par plateforme.
`normative` compte les assertions actives dans le cache sans certifier les règles
actuelles externes. `ok=true` signifie que la consultation a réussi.

Les erreurs retournent `ok=false`, `status=BLOCKED_WITH_REASON`, un code neutre
et le code de sortie 2. Date invalide, sélecteur inconnu, cache absent, format
SQLite refusé ou changement pendant la lecture ne proposent aucun chemin de
remplacement. Les sorties humaine, JSON et erreurs sont en UTF-8, y compris
après un démarrage Windows avec `PYTHONIOENCODING=cp1252`.

Le JSON exclut les chemins locaux et empreintes des caches, payloads bruts,
marqueurs et preuves non présentes. Les URLs descriptives affichées sont
limitées aux hôtes publics attendus, sans identifiants ni paramètres; une URL
non admissible n’est pas affichée. Aucune URL n’est consultée par cette commande.

## Portée technique et vérification

Le lecteur existant `scoped_identity_rules_observations` est réutilisé, sans
nouveau moteur ou stockage. Les seuls fichiers de données admissibles sont :

```text
data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3
data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3
```

La branche CLI s’exécute avant la recherche générale de racine et la sélection
de DB. Les gardes du lecteur restent actives : ancêtres littéraux, refus de
redirections/liens multiples et du format WAL; SQLite `mode=ro&immutable=1`,
`query_only`, comparaison d’octets et de métadonnées avant/après. Ces
comparaisons ne démontrent pas l’exclusion d’un écrivain concurrent ni une
isolation complète contre une course de namespace.

Les tests ciblés nommés utilisent exclusivement des SQLite et listes inventées :

```powershell
python -B -m pytest -q --confcutdir=tests -p no:cacheprovider tests/test_public_identity_rules_scoped.py tests/test_public_evidence_explain_cli.py
```

Ils couvrent la vraie entrée `python -m pokemind`, les vues et filtres,
l’encodage CP1252 vers UTF-8, les erreurs, l’idempotence et la non-mutation.
Un garde d’audit dans des sous-processus précharge le code statique nommé puis
refuse toute ouverture autre que les deux fichiers, toute troisième DB,
écriture, découverte de noms, réseau et usage des routes racine/DB par défaut.
La suite locale générale n’est pas lancée sous cette restriction de fichiers;
la CI complète Windows/Ubuntu demeure exigée au SHA livré.

[Preuves du lot](../.orchestrator/EVIDENCE_PM-V1-PUBLIC-EVIDENCE-EXPLAIN-CLI-001.md).
La prochaine étape est l’audit indépendant ChatGPT; aucun autre lot ou accès
privé, réseau Pokémon, jeu, OS, OCR, planificateur ou sauvegarde n’est autorisé.
