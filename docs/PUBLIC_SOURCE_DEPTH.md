# Profondeur des preuves PUBLIC — prototype sur données inventées

2026-10-27. `PM-V1-PUBLIC-SOURCE-DEPTH-001`. Aucun renseignement ci-dessous ne certifie une règle Pokémon actuelle. **V1 NOT_RELEASE_READY; sources réelles à qualifier séparément.**

## Matrice question / preuve / réponse

| Question | Champs nécessaires | Source licite à qualifier | Statut de provenance | Réponse prudente |
|---|---|---|---|---|
| Que dit cette annonce de rotation? | URL, hash du corps, version de projection, publication, plateforme, format, marques citées, date d'effet | Texte officiel admis et droits explicites pour les seuls champs dérivés | `extracted_unverified`; consultation distincte de publication et effet | Rapporter les champs extraits comme annonce non certifiée, date future indiquée; application courante `unknown` |
| Quel changement de règle et quel effet sur mon deck? | Texte explicite avant/après, date, portée, exceptions et version de deck autorisée | Annonce officielle et registre normatif existant vérifié | Absence de texte, contradiction ou droits inconnus = `unknown` | Le prototype reconnaît seulement une phrase de rotation bornée; aucun changement général ni effet sur un deck personnel inféré |
| Une ancienne impression équivaut-elle à une réimpression? | Identités des deux impressions, texte effectif/errata, preuve officielle d'équivalence et dates | Registre `rules.py` existant et catalogue sourcé | La rotation seule ne prouve pas l'équivalence | `réimpression : unknown`; aucun nouvel import normatif ou verdict de légalité |
| Standard et TCG Live? | Format, plateforme, date, restrictions complètes, sortie de l'impression, équivalence, support Live distinct | Registre officiel et données de support Live explicitement vérifiées | Une page, un répertoire ou une marque seule sont insuffisants | Application, disponibilité Live et restrictions restent inconnues; aucune carte déclarée légale |
| Les familles ont-elles changé dans l'échantillon? | Deux fenêtres disjointes, dates de tournois et de consultation, format/plateforme, placements classifiés et dénominateurs, pairings admissibles, provenance | Tables PUBLIC `meta_tournaments`, `meta_placements`, `meta_matches`, instantanés complets existants | Classification par identifiant publié, non validée indépendamment | Variation descriptive des parts des placements classifiés si seuils atteints; autrement aucune tendance calculée |
| Pourquoi ce changement? Est-ce meilleur? | Comparabilité, classification stable, facteurs confondants, protocole et échantillon approprié | Les fréquences observées seules ne fournissent pas cette preuve | Causalité, représentativité mondiale et amélioration `unknown` | Hypothèse de conseil à tester, pas de winrate ni d'amélioration causale |

## Réutilisation et limites de conception

Le transport de `batch_public_research.py` conserve allowlist HTTPS exacte, robots avant page, arrêt sur protection/refus, absence de redirection, réservations GET durables, limites de taille et de budget. Les pages HTML demeurent éphémères. Les champs dérivés et leur provenance sont insérés dans les mêmes `research.json`, Learning Loop et index versionnés; aucun schéma, historique, cerveau ou chat supplémentaire. Les anciens instantanés restent lisibles; leur contenu n'est pas réécrit.

`public_source_fields.py` ne fait aucun réseau. La grammaire expérimentale reconnaît uniquement une phrase complète dans un paragraphe d'article : `In the Standard format for TCG Live, regulation marks Q, R are allowed starting 2031-05-01.` Ces marques/dates sont inventées. Le titre, scripts, navigation, éléments cachés et prose libre ne font pas autorité. Pas de généralisation à la formulation des vrais sites sans future qualification. Bornes : corps 2 Mio, 64 paragraphes de 500 caractères, 8 assertions distinctes. Rien ne stocke la phrase ou le corps HTML.

Les droits sont un paramètre explicite séparé du contenu de la page. **Seule la licence de fixture `synthetic_author_owned` est admise dans ce prototype**; aucun droit d'un vrai site n'est installé. L'UI ordinaire ne fournit pas cette politique. Politique absente/invalide = `RETENTION_NOT_AUTHORIZED`, zéro assertion. Une future collecte ne peut donc pas activer l'extraction réelle simplement en renouvelant le cache. Une politique synthétique déclarée par un appelant n'est pas une certification juridique; elle ne doit jamais être appliquée à un document réel.

Les champs extraits restent `unverified` et ne sont pas chargés dans les assertions `verified` du registre officiel. Les dates sont requalifiées au moment de la réponse : publication absente/invalide ou future, effet absent/invalide/futur, contradictions intra/inter-sources. Conflit conservateur pour toute divergence de marques/date au sein d'une plateforme; le prototype ne résout pas une succession d'annonces. Une consultation de cache périmé peut rapporter les champs historiques, jamais affirmer leur applicabilité courante. Publication, consultation et effet sont présentés séparément; hash du corps et version de projection restent dans l'instantané.

`meta_window_comparison` réutilise les filtres de contexte et instantanés complets du moteur méta. Sont exclus : événements/consultations futures, autre format/plateforme, tournois privés, incomplets, règles spéciales, bannissements personnalisés, source/hash non qualifiés. Les fenêtres sont disjointes et bornées par `as_of`; les lectures sont sans écriture. La projection du cache de pairings marqué existant est recalculée pour le reçu, sans collecte ni nouvelle mémoire factuelle. Le chat conserve son reçu d'écritures; les agrégats lus ne deviennent pas des faits ajoutés fictifs.

Seuils par fenêtre : 2 tournois, 10 placements classifiés, couverture de classification >=80 %, 5 matchs admissibles classifiables. Ces seuils sont une politique minimale d'affichage, **aucun test de significativité**. Parts = placements classifiés de la famille / tous les placements classifiés; un placement n'est pas un joueur unique. Les parties individuelles ne sont pas connues par ces pairings. L'ID d'archétype du fournisseur est la définition utilisée; dérive possible, top cuts, abandons, absences et sélection de tournois restent des biais. Deux parts différentes ne démontrent ni cause ni rendement personnel. Le reçu ignore les synthèses et proportions libres et recalcule les parts depuis les effectifs typés.

## Proposition de collecte future — execute_now=false

**Préparation seulement, pas une autorisation. Aucun GET réel fait par ce mandat.**

| Site / opération future proposée | Plafond proposé, inclus dans l'enveloppe | Conditions avant exécution |
|---|---|---|
| `www.pokemon.com` : robots + les deux URL officielles déjà admises | 3 GET maximum, 2 Mio par réponse | Consentement propriétaire distinct; vérifier manuellement URL courante et droits/conditions; si redirection ou site déplacé, STOP et nouveau mandat, aucune extension silencieuse |
| API publique `play.limitlesstcg.com` : jeux, une page de découverte et détails/classements/pairings d'au plus 4 événements | 14 GET maximum, 2 Mio par réponse | Consentement distinct; licence/rétention et contexte à qualifier; une enveloppe 4 événements ne garantit pas deux fenêtres suffisantes; pas de poursuite automatique |
| Total proposé | **17 GET / 24 Mio cumulatifs**, un seul essai, sans reprise réseau automatique | Réservation durable; cadence >=1 s/hôte; timeout <=25 s; aucun compte, jeton privé, Trainer Hill, contournement, page brute HTML, image ni donnée personnelle |

Les deux enveloppes peuvent être refusées ou autorisées séparément. Cette proposition n'est pas câblée comme nouvelle valeur par défaut ni exécutée. Toute nouvelle allowlist, droits, extraction réelle ou modification du budget existant exige un mandat ultérieur, audit et ordre manuel explicite. Si le contenu réel ne correspond pas à la grammaire validée, garder `unknown`, sans élargissement automatique.
