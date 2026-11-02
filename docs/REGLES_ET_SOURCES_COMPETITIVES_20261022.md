# Règles et sources compétitives — revue du 22 octobre 2026

`PM-V1-OFFICIAL-RULES-AND-COMPETITIVE-SOURCES`, audit technique partiel accepté.
Correction de reproductibilité : `PM-V1-RULES-GITHUB-REPRODUCIBILITY-001`,
**AUDITÉ DANS LA PORTÉE SQLITE SYNTHÉTIQUE**. Les opérations et comptes de la base Windows restent
**CODEX_LOCAL_REPORTED**, non reproduits depuis GitHub sur cette base existante.
V1 **NOT_RELEASE_READY**. Le catalogue descriptif et ses compléments FR restent
inchangés selon le rapport local; leur état sur le PC n'est pas certifié par la CI.

## Portée des preuves

| Élément | Preuve disponible |
|---|---|
| 4 références et 16 assertions de la revue | Directement recomptables dans le JSON versionné |
| Chargement SQL des deux registres, totaux15/22/1, rechargement, huit décisions | Reproduction hors ligne dans une SQLite neuve et sur six impressions **synthétiques**, exécutée par la suite CI |
| Chargement et décisions du cache PUBLIC déjà présent sur le PC | **CODEX_LOCAL_REPORTED**; aucune ouverture de cette base dans la correction |
| Texte intégral des deux PDF officiels | Revue locale Codex; réserve de l'audit indépendant conservée |
| Véritables listes et résultats compétitifs intégrés | **NOT_ACQUIRED**, zéro liste rapportée; aucune nouvelle collecte dans cette correction |

Reproduction depuis le dépôt, sans base personnelle ni réseau :

```powershell
python -m pytest -q tests/test_rules_versioned_registry.py --junitxml=data/local/ci/rules-reproduction.xml
```

La CI complète Windows/Ubuntu publie `rules_registry_evidence` dans les logs
et un résumé au **SHA testé**. Le publieur exige la propriété JUnit issue du test,
les empreintes des registres PUBLIC du checkout et les résultats attendus;
un simple total de tests verts ne suffit pas. Vérifier les deux jobs de livraison.
Le verdict sans impression de catalogue reste `unknown`. Les identifiants des
six impressions de fixture correspondent aux cas du registre, mais leurs marques
et métadonnées sont des entrées de test : aucune identité TCGdex réelle n'est
certifiée par cette reproduction. [Preuves de la correction](../.orchestrator/EVIDENCE_PM-V1-RULES-GITHUB-REPRODUCIBILITY-001.md).

## Ce qui est utilisable

Selon le rapport Codex local, quatre sources officielles complètes ont été
acquises et leurs passages pertinents revus :

| Source | Version/publication | Faits retenus |
|---|---|---|
| [Rotation Standard FR](https://www.pokemon.com/fr/actualites/rotation-de-la-saison-2026-du-format-standard-pour-le-jcc-pokemon) |9 janvier2026|H/I/J;26 mars Live,10 avril présentiel;deux exemples précis de réimpression |
| [TCG Tournament Handbook](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-tcg-tournament-handbook-en.pdf) |1 septembre2026,27pages|identité fonctionnelle et calendrier de disponibilité, sections4.1.2–4.1.3 |
| [Errata](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg_errata.pdf) |17 août2026,11pages|catégorie Outil;références Minior099/201 et Diancie086 |
| [Bannissements](https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-banned-card-list) |état observé22 octobre2026|zéro carte bannie en Standard présentiel;exemple Gouroutan UPR114 en Étendu |

Le [registre de cette revue](../knowledge/curated/official_rules_20261022.json)
contient **16 assertions** et les empreintes des documents publics. Son champ
`verified` désigne la revue documentaire de l'exécuteur; il ne remplace pas un
audit indépendant. Les copies brutes restent locales. Codex rapporte la lecture
des corps complets et le contrôle du tableau des marques du manuel en extraction avec
mise en page. Les symboles d'Énergie non restitués par l'extraction ne sont pas inventés.

La fenêtre de validation de cette revue est **2026-10-22 seulement**. Elle ne
prédit pas les changements futurs et ne reconstruit pas toute l'histoire normative.
La date `legal_from=2026-10-22` des quatre exemples signifie « jouable à cette date
selon l'exemple officiel », jamais « première sortie ou première légalité ce jour-là ».

Deux équivalences précises sont enregistrées : `sm1-129 → me01-125` (Super Bonbon)
et `swsh2-154 → me01-114` (Ordres du Boss). L'identité s'appuie sur les impressions
numérotées intégrées à l'annonce officielle, puis le catalogue local, pas sur un
rapprochement de noms. La fiche de réimpression affiche désormais format et plateforme.

Le moteur traite les anciennes impressions sans marque lorsque l'équivalence est
prouvée. Une marque admise et une liste de bannissements vide ne suffisent plus
quand la politique de disponibilité exige une preuve par impression. Une cible de
réimpression future, bannie ou mal étayée ne confère aucune légalité à l'ancienne.
Ce contrôle ne calcule pas une date de tournoi à partir d'une date TCGdex non normative.

## Consultation hors ligne

```powershell
$cataloguePublic = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind rules check-card sm1-129 --format standard --platform in_person --as-of 2026-10-22 --db $cataloguePublic --json
python -m pokemind cards reprints sm1-129 --as-of 2026-10-22 --db $cataloguePublic --json
python -m pokemind rules status --db $cataloguePublic --json
```

Résultats du cache PUBLIC local **rapportés par Codex** : les quatre impressions des deux exemples sont
`legal` **en Standard présentiel au22 octobre**; `sm5-114` est `not_legal` en
Étendu présentiel. Le cas Standard Live demeure `unknown`, sans preuve complète
des restrictions temporaires et du support de l'impression. La possession et la
fabrication restent inconnues. Le [support officiel](https://support.pokemon.com/hc/en-us/articles/51315704243476-Why-can-t-I-use-my-card-or-deck-in-Pok%C3%A9mon-TCG-Live)
confirme ces distinctions; cet article lu via le lecteur Web n'est pas ajouté
comme un corps HTTP intégral à la base.

Selon Codex, le cache compte15sources,22assertions et1règle de structure après chargement du
registre historique puis de cette revue. Les16 assertions sont les nouveaux faits;
les autres ne sont pas artificiellement redatées. La revue rafraîchit trois
identifiants de source existants et en ajoute un, sans contourner l'unicité des URL.
Les constats de corps HTTP et leurs revues sont séparés des assertions normatives.

## Sources compétitives : limites observées

Les pages publiques de résultats de [Louisville](https://limitlesstcg.com/tournaments/581)
(10octobre,2927participants annoncés), [Recife](https://limitlesstcg.com/tournaments/580)
(3octobre,1074) et [Frankfurt](https://limitlesstcg.com/tournaments/579)
(26septembre,2793) sont repérées. Leurs métadonnées ne constituent ni un corpus
de listes ni des statistiques de matchups. Le total annoncé d'un événement n'est
pas le nombre de listes disponibles et ces événements ne sont pas regroupés avec Live.

La documentation Limitless confirme son API publique et ses quotas; les formats
PTCG/Standard/PTCGL ont été observés dans `/games`. Une page de listes a toutefois
atteint la borne de8MiB : **arrêt Limitless sans retry**, réponse incomplète exclue.
La [source RK9 indépendante](https://rk9.gg/pairings/LO001-piALjQswPD3x0J)
corrobore l'événement de Louisville, mais son total de3430 a un périmètre non établi
par rapport aux2927 de Limitless; aucune fusion de populations, classification
de decks ou API privée n'en est déduite. **Zéro tournoi/listes ajouté aux tables méta**.
Il manque encore un échantillon de listes et de matchs datés, complet et séparé
par format, plateforme et BO1/BO3, pour étayer des recommandations compétitives fortes.

La page de légalité des promotions et les conditions générales Pokémon ont livré
une protection antirobot : acquisition fermée, pas de contournement. La détection
de cette réponse HTTP200 a été renforcée. Les conditions n'ont pas été relues
intégralement; aucun droit de redistribution des PDF/HTML n'est revendiqué.
Seuls faits courts, provenance et code synthétique sont publiés. Aucun deck,
journal, collection ou base personnelle consulté; aucune tâche Windows ou OCR lancé.

[Preuves et limites techniques](../.orchestrator/EVIDENCE_PM-V1-OFFICIAL-RULES-AND-COMPETITIVE-SOURCES.md).
Tous les budgets de cette tâche sont clos. **STOP pour audit indépendant ChatGPT**.
