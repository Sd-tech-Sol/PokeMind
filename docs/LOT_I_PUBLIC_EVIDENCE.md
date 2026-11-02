# I2 — connaissances publiques, preuves et limites

2026-10-15 UTC. Deux commandes réelles sur un espace **PUBLIC uniquement**, neuf
puis réutilisé sous `data/local/public-campaigns/lot-i-qa-20261015`. Pas de lecture
de base personnelle. Bases, snapshots, noms de participants et réponses brutes
restent hors Git. Les nombres ci-dessous sont des observations Codex, non une
vérification indépendante ChatGPT.

```powershell
python scripts/lot_i_public_campaign.py --campaign qa-20261015 --create --execute-public-campaign
python scripts/lot_i_public_campaign.py --campaign qa-20261015 --phase details --tcgdex-budget 12 --meta-budget 0 --official-budget 0 --execute-public-campaign
```

Première commande : **19 GET / maximum 22** (12 TCGdex, 5 Limitless, 2 officiel).
Deuxième : **12 GET / maximum 12**, TCGdex détails. Total **31/34**. Délai 0,5 s,
timeout 10 s, clients existants pour quotas/retries/redirects. Aucun accès privé,
image, endpoint protégé de decks ou Trainer Hill. La campagne garde des curseurs
transactionnels locaux et refuse un espace non marqué PUBLIC, alias ou répertoire
déjà présent à la création. Sans `--execute-public-campaign`, aucun réseau/écriture.

| Scope TCGdex observé | Membres d'index après scan | Détails frais parmi ces membres après reprise |
|---|---:|---:|
| sets EN |220|2|
| sets FR |202|3|
| cartes EN |300|1|
| cartes FR |300|1|

Trois pages par scope, aucune fin confirmée : **dénominateurs et ratios inconnus**.
Union SQL initiale 223 sets/331 impressions; après détails 223/361. Une réponse de
set peut découvrir d'autres impressions; l'union ne remplace jamais les quatre
scopes de scans. Les compteurs de détails du tableau ne prétendent pas décrire
tous les détails présents dans la base ni l'univers fournisseur.

I garde les doublons internes aux pages, invalide la complétude lors d'erreur,
refuse un ratio sur scan trop étalé (>7 jours), et redémarre la tête d'un cycle de
refresh si sa sonde de reprise change. Les pages restent non atomiques : une dérive
non observée reste possible; aucun total fournisseur ni 100% mondial n'est certifié.
Les 404 FR, champs manquants, variantes, réimpressions, support Live et légalité
gardent leurs preuves distinctes; aucune équivalence par nom.

Limitless : un instantané complet **au moment du fetch**, PTCG/STANDARD/PTCGL,
online, événement 2026-10-15T03:35Z, fetch 04:28:56Z. Statut final fournisseur
inconnu; 9 pairings SWISS/BO1, 6 byes/pertes automatiques exclus, **n=3**
admissibles et classifiables; 3 placements classifiés. Ce petit événement peut
encore évoluer. Aucun winrate personnel/global ni représentativité supposés.

## Normes officielles

La page d'annonce rotation 2026 n'a pas produit de réponse exploitable dans le
budget; code neutre `OFFICIAL_INVALID_INPUT_OR_STATE`. La page officielle
[règles et ressources](https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources)
a retourné 200, corps non tronqué, SHA
`20f9efe47a10d93c722d16de 31ed5b07baa93543ab04d5da4e7f4cb87290c94b`.
**Ni son document complet ni tous ses documents liés n'ont été revus normativement.**
Une contre-vérification web des deux URLs le même jour retourne seulement un
iframe, sans texte normatif exploitable; ces deux consultations sont séparées
des 31 GET du collecteur. Aucun contournement de page de protection n'a été tenté.
Ce hash atteste une réponse, aucune règle nouvelle. Assertions ajoutées :0.
I invalide également une revue lorsque la date d'observation/revue est future.

| Dimension conservée | Preuve encore nécessaire avant assertion vérifiée |
|---|---|
| Standard Live / présentiel | documents entiers datés, dates d'effet séparées, version et passage |
| 60 cartes, quotas, exceptions et bans | texte complet, identité canonique, exceptions exhaustives par contexte/date |
| Expanded | périmètre des éditions, bans et prise en charge Live distincte |
| Promos | date d'admissibilité et impression précise |
| Errata | version du texte effectif, édition/langue et date |
| Réimpressions | équivalence officielle, texte effectif et conditions |
| Compatibilité Live | preuve client/officielle distincte du catalogue historique |

La file `knowledge official-queue`, la revue entière liée au hash et le registre
normatif versionné restent trois étapes distinctes. Une réponse 200/304, un hash ou
un opt-in de revue ne suffisent pas à rendre `legal`. Trainer Hill reste
`BLOCKED_WITH_REASON` faute de preuve primaire d'accès automatisé autorisé.

## Achèvement progressif

Choisir un identifiant PUBLIC neuf avec `--create` une seule fois. Prévisualiser
d'abord sans option d'exécution. Reprendre **le même identifiant** en `--phase index`
puis `details`, par petits budgets explicites; `refresh` redémarre/réconcilie les
index déjà découverts. Maximum 24 GET par commande, pas de boucle de centaines
d'appels. Pour une reprise d'index mouvant, préférer un budget permettant les
sondes et la progression des quatre scopes. Les erreurs 429/timeouts conservent
les checkpoints et signalent les gaps; réessayer plus tard après temporisation.
`latest-report.json` agrégé reste local. Ne jamais y copier une base propriétaire.
La complétude de contenu historique/normatif reste `PARTIAL_WITH_EVIDENCE`.
