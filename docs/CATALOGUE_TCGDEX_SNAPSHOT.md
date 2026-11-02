# Catalogue public FR/EN — instantané complet

Complément2026-10-22 : les [textes français publiés](ENRICHISSEMENT_TEXTES_FR.md)
ajoutent 15 439 champs attribués sur 10 556 cartes dans ce cache PUBLIC, dont
9 605 descriptions. Les valeurs et comptes natifs ci-dessous restent inchangés;
les champs non résolus restent inconnus. Aucun complément ne prouve une édition FR.

2026-10-22, `PM-V1-CATALOG-COMPLETE-001`. Résultat local rapporté par Codex,
**PINNED_CATALOG_COMPLETE / AWAITING_AUDIT**; V1 **NOT_RELEASE_READY**.
Le périmètre complet est l'arbre occidental `data/` du dépôt officiel TCGdex au
commit `cbddf7e54033b1b58e44af1049c88832e55b94d0`. Les langues asiatiques
`data-asia/`, le total mondial, la légalité et la compatibilité Live sont séparés.

| Mesure | Anglais | Français |
|---|---:|---:|
| Fiches descriptives disponibles | 23 771 | 22 192 |
| Langue indisponible pour un détail valide | 93 | 1 672 |
| Extensions disponibles | 220 | 202 |
| Extensions sans nom dans cette langue | 3 | 21 |
| Détails en attente / erreur / périmés | 0 / 0 / 0 | 0 / 0 / 0 |

Union : **23 864 impressions et 223 extensions**. Les 23 873 fichiers Card
contiennent neuf objets supplémentaires partageant un identifiant avec un objet
d'une autre langue; les origines sont conservées et les conflits de langue sont
refusés. Aucun identifiant n'est fusionné d'après son nom. Une disponibilité
exige un nom de carte et un nom d'extension référencée dans la langue demandée.
Une fiche indisponible peut donc contenir quelques champs traduits en amont;
`absent` décrit ici l'indisponibilité du détail, jamais une réponse HTTP404.

Les champs absents restent inconnus. Exemple mesuré : 14 noms d'attaque manquants
sur 31 050 attaques EN et 140 sur 29 039 FR; 20 noms de talent manquants sur
4 429 EN et 34 sur 4 171 FR. Aucun des Pokémon disponibles ne manque de PV.
Les champs facultatifs `level` et `weight` sont pris en charge, mais aucun objet
de cet instantané ne les fournit. Les prix, images et assertions de légalité ne
sont pas importés. Les compteurs de set `total` sont dérivés du maximum entre le
compteur officiel déclaré et les membres disponibles, pour le contrat du schéma;
ils ne constituent pas une preuve de total mondial.

## Consultation locale

La base PUBLIC neuve demeure hors Git :
`data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3`.
Le deck, les parties et la base personnelle n'ont été ni lus ni modifiés.
Pour consulter ce catalogue, choisir explicitement sa base :

```powershell
$cataloguePublic = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind cards coverage --db $cataloguePublic --json
python -m pokemind cards search Pikachu --lang fr --db $cataloguePublic --json
python -m pokemind cards show base1-58 --lang en --db $cataloguePublic --json
```

La recherche, les fiches et la couverture fonctionnent hors ligne. Une seconde
invocation de l'importateur sur ce cache complet donne `CACHE_HIT_COMPLETE`, zéro
réseau et zéro modification SQLite. Ne pas utiliser une commande de synchronisation
ou de migration de la base personnelle pour accéder à ce résultat.

## Importateur manuel

`python -m pokemind.public_catalog_snapshot --source <source-PUBLIC-revue> --campaign <nom>`
est une prévisualisation sans lecture de source, réseau ou création. Le commutateur
`--execute-reviewed-public-snapshot` exécute uniquement l'import hors ligne;
`--create` exige un nouvel espace PUBLIC inexistant. Un run incomplet est clos,
pas repris automatiquement. Le téléchargement et l'attestation de source restent
une étape manuelle autorisée; aucun watcher, scheduler ou téléchargement implicite.

Le lecteur vérifie arbre complet, objets Git, volume, chemins et types, puis lit
une grammaire de données littérales sans `eval`, import Python/JS ni exécution TS.
Seules les concaténations de constantes texte sont admises. Les références se
résolvent dans la table des modules déjà vérifiés. Toutes les fiches sont validées
avant la création SQLite. Le schéma global de la base personnelle reste inchangé;
deux tables auxiliaires propres au cache PUBLIC conservent payloads et reçus.

Chaque traduction garde URL de fichier immuable, date et empreinte du payload.
Le reçu contient commit, objet Git et toutes les origines candidates; la notice
MIT complète est conservée localement. La source est le
[dépôt officiel épinglé](https://github.com/tcgdex/cards-database/tree/cbddf7e54033b1b58e44af1049c88832e55b94d0/data),
avec sa [licence MIT](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/LICENSE).
Les droits sur marques et illustrations sont distincts.

## Limites et audit

La collecte API neuve a d'abord fermé sur HTTP503; elle demeure fermée. Le résultat
ci-dessus provient exclusivement de l'archive officielle vérifiée, importée dans
un second espace vierge, sans copier cette collecte ni une ancienne campagne.
Le HEAD amont est resté identique lors du dernier contrôle. Toutes les preuves
de ce travail figurent dans
[EVIDENCE](../.orchestrator/EVIDENCE_PM-V1-CATALOG-COMPLETE-001.md).
Les opérations locales sont rapportées par Codex; les CI et l'audit GitHub ne
peuvent pas les certifier indépendamment sur le PC. Les autres critères V1 restent
dans leur état antérieur jusqu'à des preuves adaptées et un audit indépendant.
