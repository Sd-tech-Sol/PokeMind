# J2/J3 — progression publique mesurée

2026-10-15 UTC, campagne neuve `j-public-20261015`, workspace PUBLIC créé par J
sous `data/local/public-campaigns/lot-i-j-public-20261015`. Le préfixe historique
du script I est conservé pour compatibilité; aucune base de campagne I ou base
propriétaire réutilisée. Réponses, SQLite, identifiants de tournois et rapports
locaux hors Git. Les chiffres sont des observations Codex, à auditer séparément.

| Commande réellement exécutée avec `python scripts/lot_i_public_campaign.py` | GET tentés/plafond |
|---|---:|
| `--campaign j-public-20261015 --create --tcgdex-budget 16 --meta-budget 6 --official-budget 2 --execute-public-campaign` | 23/24 |
| `--campaign j-public-20261015 --phase index --tcgdex-budget 20 --meta-budget 0 --official-budget 0 --execute-public-campaign` | 20/20 |
| `--campaign j-public-20261015 --phase details --tcgdex-budget 14 --meta-budget 8 --official-budget 2 --official-scope modern --execute-public-campaign` | 21/24 |

Total des trois commandes réseau : **64/68 GET** (TCGdex 50, Limitless 10,
Pokémon officiel 4), délai minimal 0,5 s, timeout 10 s, retries/redirections
comptés par les clients existants, au plus 24 par invocation. Aucune boucle
de collecte illimitée. Une reprise intermédiaire a été refusée avant réseau
(0 GET, plafond prévu 20) : le nouveau garde-fou confondait des lignes internes
d'un index FTS vide avec des données personnelles. Correction de l'allowlist des
tables internes, fermeture explicite SQLite, puis reprise réussie. Ce refus
n'est pas compté dans les 64/68 commandes ayant fait du réseau.

La reprise vérifie maintenant aussi l'absence de lignes dans les tables owner
et inconnues, avant tout GET. Un marqueur PUBLIC n'est pas une certification
cryptographique du contenu des colonnes publiques/metadata. Ne jamais copier une
base personnelle dans cet espace. Tests sans réseau dans les suites I/J.

| Scope | Pages/membres observés | Détails frais des membres à la fin |
|---|---|---|
| sets EN |4 pages, fin observée, 220 membres|3/220|
| sets FR |4 pages, fin observée, 202 membres|4/202|
| cartes EN |14 pages, 1 400 membres, fin non atteinte|1; dénominateur inconnu|
| cartes FR |14 pages, 1 400 membres, fin non atteinte|1; dénominateur inconnu|

Scans débutés 05:31:53–54Z; fin des sets 05:32:00–01Z; dernière page cartes
05:34:09–10Z. Union locale : 223 sets et 1 552 impressions après index, puis
1 568 après détails de sets. Une découverte via un set n'agrandit pas le
dénominateur du scan de cartes. Variants/champs/identités/réimpressions conservent
leurs compteurs et preuves distincts; aucune équivalence officielle ajoutée.

La fin observée des sets prouve uniquement les membres de ce scan non atomique.
Total mondial/fournisseur et exhaustivité FR/EN inconnus. J refuse la complétude
courante pour membership ancien v1, scan périmé/futur, durée excessive/inversée,
gap, doublons et erreur; les drapeaux historiques de curseur ne suffisent plus
à produire `cards coverage.complete`. Les suites de timeout/429/404 FR, reprise,
refresh mouvant, variants et reprints A–I restent exécutées.

## Métagame public

Deux snapshots complets au fetch, PTCG/STANDARD/PTCGL/online, événements du
2026-10-15 à 03:20Z et 03:35Z, dernier fetch 05:35:04Z. Statut de finalisation
fournisseur **unknown** pour les deux. 15 pairings SWISS/BO1, 10 byes/pertes
automatiques exclus, **n=5** admissibles et classifiables; 6 placements classifiés.
Biais de petits événements récents sélectionnés, événements susceptibles d'évoluer,
aucun winrate global/personnel et aucune représentativité du métagame total.
Trainer Hill : `BLOCKED_WITH_REASON`, accès automatisé primaire autorisé non établi.

## Documents officiels et limites d'accès

Les probes historiques donnent erreur neutre pour l'annonce rotation et 200 non
tronqué pour la page de ressources. Le nouveau scope `modern` permet deux voies
officielles publiques déjà vérifiées :

- [Documents Play! Pokémon](https://play.pokemon.com/en-us/resources/documents/) : 200 non tronqué,
  SHA-256 `c760626a4d5b4547432a3ffc98b791274809e4c8f4258df5ea33007d96320cb1`.
- [Rules & Formats Play! Pokémon](https://play.pokemon.com/en-us/resources/rules/) : 200 non tronqué,
  SHA-256 `ef13953075e7f3af308bd565d78e6669f77d6c3ddc8fc99b2f1a7a411c965d10`.

Navigation web séparée des 64 GET : pages modernes lisibles et liens officiels
vers handbook, errata et promos inspectés. L'annonce, le livret Mega Evolution,
le handbook, les errata et la page promo ciblés sur `www.pokemon.com` rendent
seulement un iframe dans l'outil de lecture. Aucune résolution/challenge de
protection contourné, aucun miroir non officiel employé comme preuve normative.
La page Rules & Formats décrit le principe général des réimpressions, sans
registre exhaustif daté des impressions ni preuve de support Live.

**0 nouvelle assertion normative**, aucun document réglementaire complet ciblé
nouvellement revu/audité. Un corps non tronqué, un hash ou une page de navigation
ne prouvent pas les règles. Pour Standard Live/physique, structure60/quotas/
exceptions/bans, Expanded, promos, errata, réimpressions et Live : conserver les
fenêtres/tri-state hérités et compléter documents entiers, passages, versions et
dates avant promotion. J ajoute le refus de réimpressions contradictoires même
si deux assertions sont marquées verified et d'une publication postérieure à
la date évaluée. `check-card` évalue rétrospectivement les règles effectives;
la disponibilité historique de connaissance reste distincte dans `normative_coverage`.

Sources techniques primaires revues : [pagination TCGdex](https://tcgdex.dev/rest/filtering-sorting-pagination),
[API Limitless](https://docs.limitlesstcg.com/developer),
[registre de droits PokeMind](SOURCES_CONNAISSANCES.md). Seulement JSON public
borné, aucune image ni réponse brute protégée dans Git. Collecte exhaustive et
normes complètes restent `PARTIAL_WITH_EVIDENCE`; poursuivre par campagnes choisies
et bornées, pas par une promesse de 100 %.
