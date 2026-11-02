# PM-V1-FRENCH-TEXT-ENRICHMENT-001 — preuves assainies

2026-10-22 Québec. **AWAITING_AUDIT**, V1 **NOT_RELEASE_READY**.
Observations sur les sources reçues et le cache local : **CODEX_LOCAL_REPORTED**,
non certifiées indépendamment sur le PC. Ordre manuel : chercher sur Internet
les textes français manquants, sans cartes japonaises. Préférence confirmée :
« Non, seulement du français déjà publié et sourcé ». Aucune traduction de l'agent.

## Prévol avant travail fonctionnel

AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, premier NEXT_ACTION,
HANDOFF/RESULT/DECISIONS et preuves antérieures, skills executor/knowledge,
PROJECT_SPEC, NEXT_PROMPT et mandat intégral lus. Arbre initial propre,
fetch/pull ff-only sans perte, déjà à jour au SHA
`ec67dd70c25aa5d9ed9c450654abbe392c2a0f20`.
[Actions39814584101](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39814584101) :
Windows119949630281 et Ubuntu119949630041 **completed/success** au même SHA,
avant toute lecture fonctionnelle. Prévol RUNTIME_READY Python3.13.15 /
SQLite3.50.4, sans base personnelle. `knowledge status` uniquement sur la base
PUBLIC explicitement sélectionnée. Aucun besoin d'attente initiale.

Un audit documentaire concurrent a ensuite été découvert à
`23dbca251038a2b4deeaa090cb3e37d60734868d`. Aucun nouveau travail fonctionnel
après cette découverte. Les tests déjà lancés se sont terminés; les vingt pièces
locales assainies ont été préservées dans Git, puis synchronisation **ff-only**
et restitution des mêmes sources/tests, sans écraser l'audit. Les nouveaux rapports
conservent cet audit et sa proposition de mandat **non autorisée**, sans la lancer.
L'état, les archives et D-189 de l'auditeur sont conservés; D-190 décrit cette
livraison distincte. [CI39817448810](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39817448810)
Windows119959551328/Ubuntu119959549859 completed/success à23dbca2 également.
Cette synchronisation documentaire n'est pas une nouvelle autorisation d'exécution.

## Source qualifiée et bornes observées

Nouvelle recherche publique distincte; aucune ancienne campagne rejouée et
**zéro appel TCGdex API**. Le catalogue PUBLIC occidental terminé est consulté
et enrichi, ses anciennes archives et journaux de collecte ne sont pas repris.

Source retenue : [Poképédia](https://www.pokepedia.fr/), API MediaWiki publique
en lecture seule. Robots relu; aucune route de recherche spéciale, connexion ou
page oldid téléchargée. Les liens oldid servent uniquement à citer les révisions
reçues par API. Notice et métadonnées de droits relues :
[droits d'auteur](https://www.pokepedia.fr/Pok%C3%A9p%C3%A9dia%3ADroits_d%27auteur),
[CC BY-NC-SA3.0 France](https://creativecommons.org/licenses/by-nc-sa/3.0/fr/).
Attribution, historique des auteurs, usage non commercial et partage à l'identique
des adaptations conservés; aucune requalification MIT du corpus.
L'encyclopédie officielle Pokémon ne donnait qu'un contenu iframe exploitable
insuffisant; aucune donnée obtenue ni protection contournée. Pokécardex non retenu
comme source d'import qualifiée.

| Consommation nouvelle | Observé | Plafond |
|---|---:|---:|
| Recherches/ouvertures Web | 10 | 40 |
| GET directs de découverte | 6 | 40 |
| GET de données | 640 | 4 000 |
| Corps directs lus, octets cumulés | 18 424 279 | 134 217 728 |

Intervalle configuré >=1seconde, une tentative par ressource, réponses <=4MiB,
redirections refusées, arrêt sur refus/challenge/erreur terminale/plafond.
Aucun refus terminal ou challenge observé, aucun compte, clé, paiement ou image.
Budgets maintenant **clos**, aucun téléchargement futur implicitement autorisé.
Le journal local et les réponses ne sont pas publiés.

268 lots de titres initiaux, 145 catégories occidentales, 226 lots de titres
exacts et un lot supplémentaire de neuf impressions de référence. Les 495
réponses de révisions fournissent **10 625 pages** uniques. La phase initiale
comporte des titres inexistants signalés dans le JSON MediaWiki; ce ne sont pas
des HTTP404 ou des refus à réessayer. Les rapprochements de catégories ont servi
à sélectionner les titres exacts, sans répéter une requête échouée.

## Identité, textes et résultat local

Inventaire : **16 237 champs manquants /10 712 cartes**, avec valeur EN connue.
Neuf impressions supplémentaires servent uniquement de références descriptives.
Correspondance exacte extension/numéro/nom et PV lorsque disponibles. Les alias
d'extension sont revus et les préfixes promotionnels restent limités à leur set.
Attaques par nom concordant ou signature coût/dégâts unique, jamais par rang;
talents ambigus exclus. Modèles wiki limités aux données et affichages statiques
revus; aucune exécution de code, requête sémantique, instruction amont ou HTML.
Une correspondance de nom unique prime sur un coût/dégâts fortuitement identique.

| Champ FR | Lacunes avant | Ajouts publiés | Lacunes après |
|---|---:|---:|---:|
| Description de Pokémon |9 681|9 605|76|
| Nom de carte |1 672|1 584|88|
| Nom/effet d'attaque |4 045|3 497|548|
| Nom/effet de talent/pouvoir |599|521|78|
| Effet de Dresseur/Énergie |240|232|8|
| Total de champs |16 237|15 439|798|

**10 556 cartes enrichies**; **395 cartes** gardent au moins une lacune.
Un nom et un effet comptent séparément. Les champs sans valeur EN connue ne
font pas partie du dénominateur; aucune absence mondiale n'est déduite.

Trois provenances : **10 798** champs `published_french_transcription`,
**4 567** `published_community_translation`, **74** `published_parallel_description`.
Ces dernières sont uniquement des descriptions déjà publiées pour une autre
impression : paragraphe EN identique après espaces/NFC et mêmes identifiants
nationaux du Pokémon, un seul texte FR candidat. Source et impression de
référence restent visibles; aucune équivalence fonctionnelle n'est affirmée.
Tous les champs gardent `official_text_verified=false` et
`french_printing_proven=false`, révision, date, URL, historique, réception,
empreinte de réponse, paramètre wiki et licence.

26 conflits de PV et quatre conflits d'identité sont exclus; 14 pages sans cible
exacte et deux modèles à imbrication non acceptée ne contribuent pas de champs.
Zéro conflit de valeur sur un même champ importé. Aucun appariement forcé pour
faire disparaître une lacune. Les 76 descriptions restantes ne sont pas prouvées
inexistantes sur Internet; les sources consultées ne suffisent pas.

Aucune carte d'extension japonaise recherchée/importée, aucun champ japonais
retenu; zéro valeur ajoutée avec écriture japonaise. Des métadonnées japonaises
et liens interlangues peuvent apparaître dans les pages brutes occidentales;
ils sont ignorés. Pocket appartient au catalogue occidental mais reste distinct
du client Live, de la légalité et du Standard.

## Import et vérification hors ligne

Seul cache enrichi :
`data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3`.
Corpus PUBLIC propre à cette tâche dans un espace ignoré; aucune DB, archive,
réponse brute, empreinte de DB ou texte réel de carte dans Git.

Import en transaction après dry-run de tous les champs, refus d'écraser le natif
ou d'importer hors cache attesté PUBLIC. Trois tables auxiliaires de champs,
documents et FTS; aucun changement du schéma global personnel. Les **51 tables
préexistantes sont inchangées**, comparaison locale des lignes/contenus avant
et après. Valeurs originales et reçus EN/FR inchangés.

SQLite integrity_check=ok, foreign_key_check=0. FTS natif :47 728 sources et
47 728 lignes, zéro divergence de contenu. Complément :15 439 champs frais,
10 556 documents et entrées FTS cohérents. Empreintes de valeur et des payloads
natifs contrôlées; les références parallèles revérifient aussi l'impression liée.
Les comptes natifs restent23 864impressions,223extensions,23 771détailsEN,
22 192FR et93/1 672indisponibilités de langue.

Cinq CLI réelles `cards show/search/coverage` exécutées avec `--db` PUBLIC
explicite, JSON valide et exit0, sous garde refusant sockets/getaddrinfo/processus.
Fiche FR communautaire, référence descriptive, fiche EN sans complément,
recherche FR et compteurs séparés vérifiés. Second import identique : empreinte
et mtime de DB inchangées, aucune requête réseau. Aucun fallback de nom/effet EN
dans les champs français. Les comptes de compléments sont stockés; l'affichage
et la recherche revérifient leur fraîcheur au moment de la consultation.

## Tests et livraison

705 passed /3 skipped, suite complète locale finale Python3.13.15 (287.23s);42 tests ciblés.

42 tests ciblés synthétiques : parsing strict, provenance, mauvaise identité/PV,
attaque ambiguë, refus des modèles, source altérée, budgets, droits, rollback,
cache non PUBLIC, pas d'écrasement, payload périmé, faux extrait FTS, idempotence,
paragraphe/espèce de référence exacts et invalidation de la référence modifiée.
Deux tests OCR restent sans opt-in/moteur attesté; symlink Windows indisponible.
Aucun OCR, dépendance, service, scheduler, jeu, backup, migration privée, purge,
deck, journal, collection ou base personnelle consulté/modifié.

Compilation, hygiène et diff préparé vérifiés avant commit; seuls code, tests
synthétiques, agrégats et documentation assainis sont publiables sur la branche
autorisée. La CI de livraison est celle du **HEAD contenant ce rapport** : deux
jobs `completed/success` au SHA exact à contrôler après push, avec `ci_evidence`
dans les logs. Le prévol ci-dessus ne remplace pas cette CI finale.

**AWAITING_AUDIT**, execute_now=false, consumed=true; STOP audit indépendant
ChatGPT. Aucun nouveau mandat/retry préparé et aucune auto-certification.
Guide : [ENRICHISSEMENT_TEXTES_FR](../docs/ENRICHISSEMENT_TEXTES_FR.md).
