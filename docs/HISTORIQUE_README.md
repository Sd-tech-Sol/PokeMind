# PokeMind

**Assistant unifié livré (2026-10-27), AWAITING_AUDIT : UNE conversation PokeMind**, Codex par défaut, six écrans, actions projet Codex/Claude réelles et mémoire Web permanente dans le cerveau local. [Guide actuel](docs/UNIFIED_ASSISTANT_IMPLEMENTATION.md), [preuves](.orchestrator/EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md), [conception](docs/UNIFIED_POKEMIND_ASSISTANT_DESIGN.md). Import+question en un envoi, reconstruction60 hypothétique, statut Codex officiel et recherches versionnées. EXE Windows reconstruit/exécuté; preuves locales rapportées par l'exécuteur. CI limitée par budget Actions; **V1 NOT_RELEASE_READY**. Ancien mandat à deux conversations annulé; aucun mandat d'exécution actif. Les livraisons datées ci-dessous restent historiques.

**Correctif desktop :** colle un journal TCG Live dans le chat puis **Enter**
(Shift+Enter pour une ligne), ou joins/glisse un `.txt`/`.log`. Validation et
enregistrement atomique locaux, doublons, analyses et mémoire actualisées sans
envoyer le journal à l'IA. Réponses personnelles fondées sur le rapport local,
activité animée/temps écoulé, option d'actualisation au démarrage, graphiques et
galerie60 avec images sourcées en cache local. [Utilisation et confidentialité](docs/DESKTOP_GUI_CHAT_GUIDE.md).

**Application Windows + chatbot** : ouvrir `dist/PokeMind/PokeMind.exe` après
construction. [Installation, écrans et moteurs IA](docs/DESKTOP_GUI_CHAT_GUIDE.md).
Codex CLI par défaut, Claude Code et Ollama sélectionnables; données PokeMind
locales et partage cloud explicite. Livraison soumise à audit, V1 NOT_RELEASE_READY.

**Livraison desktop (2026-10-26), AWAITING_AUDIT :** six rubriques reliées aux moteurs existants, vraies sessions Codex et Claude testées, Ollama sélectionnable (service local requis). L'autorisation cloud ordinaire du propriétaire est mémorisée; le partage de statistiques reste un réglage distinct. Le coach CLI reste utilisable. [Architecture](docs/DESKTOP_GUI_CHAT_ARCHITECTURE.md). **V1 NOT_RELEASE_READY** pour les portes indépendantes restantes.

[Tes conseils de combats en une commande](docs/BATTLE_COACH.md) :
`python -m pokemind battle coach` retrouve le rapport local valide et l'affiche.
Après ajout de journaux, `python -m pokemind battle coach --update` actualise
les matchs et connaissances locales hors ligne, sans migration de SQLite.

[Revue volontaire d'une partie](docs/OWNER_SELECTED_MATCH_REVIEW.md) :
`battle review-selected`, sélection explicite, aperçu, consentements distincts
lecture/import/attestation et rapport unifié avec fiches, exports60 et Learning
Loop. Démonstration reproductible sur fixtures seulement; aucun vrai import
autorisé par cette livraison. V1 NOT_RELEASE_READY.

[Bibliothèque PUBLIC et fondation Matchups](docs/DECK_LIBRARY_MATCHUPS.md) :
`meta deck-library` recherche les compositions existantes; Observer/Analytics
testés uniquement sur matchs inventés, lecture réelle future avec sélection et opt-in.

[Deck Intelligence PUBLIC](docs/DECK_INTELLIGENCE.md) :
`meta deck-knowledge`, fiches sourcées de Dragapult et d'alternatives, plans
conditionnels et export60 pour copie manuelle; pont optionnel `--set-aliases`.
Textes manquants et légalités inconnues restent explicites, aucune collecte.

[Prévol de légalité PUBLIC hors ligne](docs/PUBLIC_DECK_LEGALITY_PREFLIGHT.md) :
`meta competitive-preflight`, bases PUBLIC explicites, date et plateforme.
Preuves par impression et structure, inconnues quantifiées; aucune collecte.

[Comparateur PUBLIC hors ligne](docs/OFFLINE_COMPETITIVE_ADVISOR.md) :
`meta competitive-inventory`, `competitive-compare` et `competitive-shortlist`;
compositions dédupliquées,différences de quantités et2–4options de plans différents.
`--db` PUBLIC et `--as-of` obligatoires;aucune collecte ni modification du cache.

Listes de tournois publiques : [échantillon Standard du 22 octobre 2026 et comparaison Dragapult](docs/COMPETITIVE_DECKLISTS_20261022.md).
Deux événements, 32 placements /28 compositions de 60 cartes rapportés localement;
consultation et export hors ligne avec `meta competitive-summary` et
`meta competitive-export`, exigeant une base PUBLIC explicite. Aucun corpus brut
versionné ni certification de la légalité Live; V1 NOT_RELEASE_READY.

Premier parcours **Windows 11 dans Codex** :
[`docs/PREMIER_USAGE_WINDOWS.md`](docs/PREMIER_USAGE_WINDOWS.md).
`python -m pokemind demo --json` exécute une répétition complète hors ligne sur
fixtures dans un espace temporaire, sans sélectionner la base personnelle.
Le [parcours utilisateur E2E](docs/PARCOURS_UTILISATEUR_E2E.md) couvre 79 appels
CLI, cinq combats fictifs, leurs liens révocables et un candidat60 distinct.
Livraison I : [`docs/LOT_I_ACCEPTANCE_MATRIX.md`](docs/LOT_I_ACCEPTANCE_MATRIX.md)
et [`docs/LOT_I_QA_REPORT.md`](docs/LOT_I_QA_REPORT.md). V1 **NOT_RELEASE_READY**.

Guide des commandes V1 : `docs/GUIDE_V1_CLI.md`. Sauvegarde et restauration :
`docs/RECUPERATION_LOCALE.md`. État de préparation :
`docs/V1_READINESS_REPORT.md` (`NOT_RELEASE_READY`, audit indépendant requis).

LOT G : `docs/LOT_G_ACCEPTANCE_MATRIX.md` et `docs/LOT_G_QA_REPORT.md`.
La restauration refuse désormais toute cible existante et publie uniquement un
clone neuf sans écrasement. L’OCR Tesseract local est optionnel, non installé ni
calibré sur ce Windows; ses tests de contrat sont simulés, sans faux succès visuel.
Profil et limites : `docs/LOT_G_LOCAL_VISION.md`. La readiness distingue toutes
les portes V1, actes propriétaire et tests; `docs/LOT_H_COMPLETION_PLAN.md`
conserve la complétion nécessaire après audit G.

PokeMind est un cerveau local, hors ligne et sourcé pour conseiller l'utilisateur
dans Pokémon TCG Live. PM-0001 couvre les quatre volumes stratégiques et leur index
SQLite FTS5. PM-0002 ajoute l'import prudent de journaux texte et les fiches de decks
observés. PM-0003 importe et versionne un export exact de 60 cartes, sans le confondre
avec la collection, puis ajoute un Skill Codex léger pour la routine après-partie.
PM-0004/PM-0004B ajoutent le catalogue TCGdex FR/EN progressif : impressions
distinctes, provenance, recherche hors ligne, couverture mesurée, synchronisation
bornée et rafraîchissement manuel reprenable des index.
PM-0005A ajoute la fondation des règles Pokémon officielles et une légalité datée,
expliquée et conservatrice. PM-0005B ajoute des instantanés manuels et bornés de la
Limitless Tournament Platform, consultables hors ligne avec statistiques descriptives.
PM-0006A compose ces preuves avec le deck et les combats locaux dans un diagnostic
strictement en lecture seule, sans taux généralisé ni recommandation d'achat.
PM-0006B compare deux versions explicitement choisies et audite la provenance des
liens combat→version, toujours hors ligne et sans modifier la base.
PM-0006C ajoute des confirmations manuelles, unitaires, datées et révocables de ces
liens, sans jamais les déduire du nom du deck, d'une carte ou d'un timestamp.
Le LOT A renforce ensuite la couverture TCGdex, les identités FR/EN, la structure
officielle des decks, la couverture Limitless et un audit intégré hors ligne. Les
données encore incomplètes restent explicitement partielles; aucun « 100 % » n'est
déduit sans dénominateur fournisseur vérifié.
Le LOT B ajoute collection/crédits déclarés et versionnés, conseils conditionnels,
leçons de combats attestées et candidats de 60 cartes exportés volontairement sans
modifier le deck joué. Guide : `docs/LOT_B_GUIDE.md`.
Le LOT C ajoute un coach visuel d’entraînement : images locales éphémères, annotation
prudente, mémoire textuelle multi-tours et conseils conditionnels. Aucun moteur de
vision fiable n’est installé par défaut; le repli honnête est l’annotation manuelle.
Guide : `docs/LOT_C_VISUAL_COACH.md`.
Le LOT D ajoute l’actualisation publique sans LLM : contrôle quotidien borné,
réconciliation mardi/vendredi en `America/Toronto`, historique/alertes offline et
préparation du planificateur Windows. Celui-ci demeure volontairement **non installé**
et impossible à activer dans le code du LOT D. Guide :
`docs/LOT_D_PUBLIC_UPDATE_GUIDE.md`.

## Prérequis et installation

- Windows 11 prioritaire; CI Linux héritée conservée pour non-régression;
- Python 3.11 ou plus récent;
- SQLite compilé avec FTS5 recommandé. Un repli local moins précis est prévu si
  FTS5 est absent.

Le paquet n'a aucune dépendance d'exécution externe et son backend d'installation
est inclus dans `scripts/`; l'installation ne télécharge donc rien :

```powershell
python -m pip install --no-index --no-build-isolation -e .
```

Pour contribuer, pytest est la seule dépendance directe de test et sa version est
épinglée dans `pyproject.toml`. PM-0001 a utilisé la version 9.1.1 déjà présente;
aucun paquet n'a été téléchargé.

Sans installation, les mêmes commandes fonctionnent depuis la racine ainsi :

```powershell
$env:PYTHONPATH = "src"
python -m pokemind --help
```

## Utilisation

```powershell
python -m pokemind import-seed
python -m pokemind search "gestion des récompenses"
python -m pokemind search "ordre des actions" --limit 3 --json
python -m pokemind status
python -m pokemind status --json
python -m pokemind cards sync --dry-run --json
python -m pokemind cards sync --phase balanced --lang en,fr --max-requests 12 --json
python -m pokemind cards sync --phase index --refresh-index --max-requests 12 --json
python -m pokemind cards sync --phase details --recheck-absent --max-requests 4 --json
python -m pokemind cards search "Vipélierre" --lang fr --json
python -m pokemind cards show 2011bw-1 --lang fr --json
python -m pokemind cards reprints 2011bw-1 --as-of 2026-10-13 --json
python -m pokemind cards coverage --json
python -m pokemind cards resolve-deck principal --json
python -m pokemind rules load-official --json
python -m pokemind rules sources --json
python -m pokemind rules status --json
python -m pokemind rules check-card <tcgdex-id> --format standard --platform live --as-of 2026-10-11 --json
python -m pokemind rules check-deck principal --format standard --platform live --as-of 2026-10-11 --json
python -m pokemind meta sync --dry-run --json
python -m pokemind meta sync --mode discover --max-requests 8 --max-tournaments 2 --format standard --platform PTCGL --online true --json
python -m pokemind meta sync --mode refresh --max-requests 8 --max-tournaments 2 --format standard --platform PTCGL --online true --json
python -m pokemind meta status --json
python -m pokemind meta coverage --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta tournaments --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta archetypes --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta matchups --archetype ID-PUBLIE --min-sample 5 --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind analyze deck principal --as-of 2026-10-12 --format standard --platform live --json
python -m pokemind knowledge status --json
python -m pokemind knowledge audit --json
python -m pokemind knowledge update --mode daily --dry-run --json
python -m pokemind knowledge update --mode deep --deep-time 19:30 --dry-run --json
python -m pokemind knowledge update status --deep-time 19:30 --json
python -m pokemind knowledge scheduler --action install --daily-time 08:15 --deep-time 19:30 --dry-run --json
python -m pokemind capability status --json
python -m pokemind collection status --json
python -m pokemind collection coverage --json
python -m pokemind collection missing --deck principal --json
python -m pokemind credits status --json
python -m pokemind recommend deck principal --as-of 2026-10-13 --format standard --platform live --collection --json
python -m pokemind battle lessons --deck principal --as-of 2026-10-13 --json
python -m pokemind log import data\local\battle_logs\partie.txt --deck principal --json
python -m pokemind log import --clipboard --deck principal --json
Get-Content data\local\battle_logs\partie.txt | python -m pokemind log import - --deck principal --json
python -m pokemind log import data\local\battle_logs\partie.txt --deck principal --reparse --json
python -m pokemind profile summary --deck principal --json
python -m pokemind profile review --deck principal --json
python -m pokemind deck import --clipboard --deck principal --json
python -m pokemind deck import data\local\decks\principal.txt --deck principal --json
Get-Content data\local\decks\principal.txt | python -m pokemind deck import - --deck principal --json
python -m pokemind deck show principal --json
python -m pokemind deck compare principal --from-version 1 --to-version 2 --json
python -m pokemind deck compare principal --from-version 1 --to-version 2 --show-changes
python -m pokemind deck version-evidence principal --as-of 2026-10-12 --json
python -m pokemind deck link-candidates --deck principal --json
python -m pokemind deck link-battle --deck principal --battle-id ID --version 1 --dry-run --json
python -m pokemind deck link-battle --deck principal --battle-id ID --version 1 --apply --confirm-owner --json
python -m pokemind deck unlink-battle --deck principal --battle-id ID --dry-run --json
python -m pokemind deck unlink-battle --deck principal --battle-id ID --apply --confirm-owner --json
python -m pokemind deck export principal --json
python -m pokemind deck prepare --proposal data\local\decks\proposals\candidat.json --json
python -m pokemind deck copy data\local\decks\import_ready\principal_v1.txt --json
python -m pokemind deck candidate-create --changes data\local\changes.json --dry-run --json
python -m pokemind deck candidate-show --candidate ID --json
python -m pokemind deck candidate-export --candidate ID --dry-run --json
python -m pokemind match start --as-of 2026-10-13 --format standard --platform live --dry-run --json
python -m pokemind match observe --image data\local\screenshots\tour-1.png --turn 1 --mode training --dry-run --json
python -m pokemind match observe --annotation data\local\annotations\tour-1.json --session ID --turn 1 --apply --confirm-owner --json
python -m pokemind match advise --session ID --turn 1 --format standard --platform live --as-of 2026-10-13 --json
python -m pokemind match show --session ID --json
python -m pokemind match close --session ID --apply --confirm-owner --json
```

### Coach visuel d’entraînement

`match observe` ne capture jamais l’écran : il lit uniquement le fichier PNG, JPEG
ou WebP choisi sous `data/local/`. Il vérifie chemin, signature, format, taille,
dimensions et orientation, puis libère les octets sans les copier dans SQLite. Le
fichier d’origine reste au propriétaire et n’est jamais supprimé automatiquement.

Sur l’environnement livré, aucune vision/OCR locale fiable n’est installée. Une
image seule retourne donc `NEEDS_MANUAL_ANNOTATION`; elle n’est pas présentée comme
interprétée. L’annotation JSON peut ensuite conserver les seuls faits confirmés. La
mémoire exige `--apply --confirm-owner`, reste textuelle et isole chaque séance. Le
coach garde la main adverse, la pioche et le contenu des Récompenses à `UNKNOWN`,
ne produit aucun taux de victoire et n’envoie aucune action au client du jeu.

`log import` accepte UTF-8, UTF-16 et Windows-1252. Le presse-papiers est lu une
seule fois sur demande explicite sous Windows; le repli fichier ou stdin (`-`)
n'exige aucune dépendance. `--deck` lie les parties à un identifiant local; sans
cet argument, chaque journal reçoit sa propre fiche `observed-<empreinte>` afin de
ne pas fusionner arbitrairement des decks.

La base conserve l'empreinte SHA-256, les événements reconnus, de courtes preuves
textuelles et les cartes observées. Elle ne conserve ni journal brut ni image.
Deux imports du même texte comptent une seule fois. Une carte vue est une
observation, jamais une liste de 60 cartes ni une preuve de collection. Avant cinq
parties valides, le bilan indique explicitement que les données sont insuffisantes;
10 parties ou plus restent préférables.

Après une mise à jour du parseur, `--reparse` remplace transactionnellement les
événements du journal ayant la même empreinte, sans créer une seconde partie. Le
fichier ou le texte d'origine doit encore être disponible puisque le brut n'est pas
archivé. Le deck déjà associé est conservé : fournir un autre `--deck` fait échouer
la commande sans modifier les données. Sans `--reparse`, le comportement demeure
un doublon ignoré et idempotent.

L'identité du joueur doit venir d'un marqueur explicite ou d'une main initiale
visiblement détaillée; le nombre de pioches ne suffit jamais. Un résultat W/L exige
un gagnant correspondant à l'un de deux participants corroborés. Sinon l'issue reste
`inconnue`. Une action « a utilisé X » est conservée comme action, mais `X` n'est pas
pris pour une carte sans contexte qui identifie le Pokémon.

### Import unique du deck exact

Après avoir choisi **Exporter** dans Pokémon TCG Live, ne copiez aucune autre commande
ni aucun autre texte. Dans Codex, tapez simplement : « J'ai copié l'export de mon deck;
importe-le comme `principal` avec PokeMind. » Codex peut alors exécuter la commande
`deck import --clipboard` sans écrire dans le presse-papiers. Le repli fichier ou
stdin accepte UTF-8, UTF-16 et Windows-1252.

L'import exige les trois sections Pokémon, Trainer/Dresseur et Energy/Énergie, vérifie
leurs totaux et refuse toute liste différente de 60 cartes. Il accepte aussi la forme
historique `##Pokémon - N`, `##Trainer Cards - N`, `##Energy - N`. Chaque version
immuable conserve seulement les lignes normalisées, la provenance, les dates et les
empreintes; jamais le texte brut. Réimporter la même liste, même réordonnée, demeure
idempotent. Une liste modifiée crée la version suivante.

`deck show principal` distingue « export 60 cartes vérifié » de « observé
partiellement ». L'import n'associe jamais rétroactivement les parties existantes à
la nouvelle version et ne prouve ni possession de toute la collection, ni légalité
Standard, ni disponibilité dans Live.

### Préparer un deck à coller dans TCG Live

`deck export principal` sérialise la dernière version exacte déjà importée. La
commande `deck prepare --proposal <fichier.json>` accepte plutôt un candidat local
conforme au schéma documenté dans `docs/PM-0003E_EXPORT_AUDIT.md`. Les deux chemins
valident 60 cartes et produisent un `.txt` sans commentaire ainsi qu'un rapport
`.json` privé séparé. Les fichiers avec toutes les identités `set_code` +
`collector_number` vérifiées (étiquette `printing_verified` pour une proposition)
vont sous `data/local/decks/import_ready/`; les autres restent sous
`data/local/decks/drafts/` et ne sont pas présentés comme prêts.

Le presse-papiers n'est modifié qu'avec `--copy` ou `deck copy <chemin>`. `deck
copy` refuse les fichiers hors du répertoire privé `import_ready`; le repli est
d'ouvrir le `.txt`, puis Ctrl+A et Ctrl+C. Le format n'a pas encore été validé par
un aller-retour dans le client réel (`OUTPUT_FORMAT_NOT_FIELD_VALIDATED`). TCG Live
demeure l'autorité temporaire pour la légalité, la disponibilité, les cartes
possédées et toute fabrication; PokeMind ne déclenche aucune transaction.

### Routine après chaque partie dans Codex

Le Skill de projet `combat` est découvert depuis `.agents/skills/combat/SKILL.md`.
Après avoir copié le journal, demandez : `$combat importe le dernier combat et
conseille-moi`. La lecture du presse-papiers reste explicite. La réponse indique
l'issue, le doublon, la progression `n/5`, au plus deux constats corroborés et les
incertitudes. Repli : exécuter
`python -m pokemind log import --clipboard --deck principal --json`, puis demander
« Résume et révise le profil principal avec PokeMind ».

`import-seed` accepte exclusivement les quatre fichiers `.md` nommés dans
`source_material/markdown/`. Chaque section conserve le document, la hiérarchie
des titres, le chemin relatif, les lignes et caractères, la date du document et
un SHA-256. Un second import ne duplique ni documents ni sections.

La base reconstruite est `data/local/pokemind.sqlite3`. Elle est privée et ignorée
par Git, comme les collections, journaux, captures et identifiants futurs. Les PDF
sont conservés comme pièces d'origine; ils ne sont pas parsés parce que les quatre
Markdown offrent déjà une structure de qualité. Aucun numéro de page n'est donc
inventé.

### Catalogue TCGdex progressif

`cards sync --dry-run` n'utilise pas le réseau et n'écrit rien. `--phase
index|details|balanced` sépare la découverte des index des détails. Une vraie
synchronisation exige un budget explicite; chaque tentative HTTP, y compris un retry,
compte dans `--max-requests`. Les réponses sont limitées à 8 Mio, avec timeout,
intervalle respectueux, backoff et prise en charge de `Retry-After`.

Le schéma actuel conserve une impression par identifiant TCGdex et une traduction reliée
par langue. Deux impressions au même nom restent distinctes. `present`, `absent`,
`not_fetched` et `network_error` sont des états séparés. Les recherches et fiches
sont entièrement hors ligne après synchronisation et citent URL, date UTC et SHA-256.
Le cache SQLite et sa sauvegarde de migration restent sous `data/local/`, ignoré par
Git; aucune image n'est téléchargée.

`--refresh-index` est une action manuelle explicite, jamais planifiée en arrière-plan.
Elle possède ses propres curseurs et reprend un scan interrompu. Une page abrégée doit
être suivie d'une page vide avant de marquer le scope terminé; un tri stable et une
sonde de la première page réduisent les omissions si l'index change pendant le scan,
sans garantir un instantané atomique du fournisseur. Un bref modifié marque le détail
antérieur comme possiblement périmé sans l'effacer. `--recheck-absent` revalide
explicitement un 404 antérieur. `--prioritize-deck ID` ne transmet aucune liste privée :
seuls les IDs TCGdex déjà résolus localement influencent l'ordre des détails.

`cards resolve-deck` est un diagnostic strictement en lecture seule. Il exige la
concordance du code `tcgOnline` fourni par TCGdex, du numéro local et du nom; sinon la
ligne reste `unresolved` ou `ambiguous`. Le catalogue TCGdex ne prouve jamais la
présence dans Live, la légalité, la possession, le coût ou la puissance compétitive.
Le catalogue local est volontairement progressif : `cards coverage` sépare la fin de
la découverte initiale, la complétude des détails découverts et l'état du dernier
rafraîchissement. Une couverture locale complète ne prouve jamais le catalogue mondial.

Le LOT A ajoute `--lang all`, une comparaison Unicode NFC sans casse, une fiche avec
identité d'impression stable et alias FR/EN sourcés, puis `cards reprints`. Cette
dernière commande ne retourne que des équivalences attestées par une source Pokémon
officielle vérifiée; l'égalité d'un nom ne suffit jamais. La priorité de détails est
deck local résolu → contexte Standard prouvé → arrière-catalogue. Seuls des IDs
TCGdex publics quittent la machine. `cards coverage` expose maintenant les scans par
langue, les totaux visibles seulement après une fin confirmée, les ratios sur les
impressions découvertes et le travail de détails exactement comptable.

### Règles officielles et légalité datée

`rules load-official` charge explicitement le petit registre public versionné de
`knowledge/curated/official_rules_2026.json`. Cette commande ne contacte pas le réseau.
La migration additive vers le schéma 9 crée d'abord une sauvegarde cohérente avec
`sqlite3.backup()` lorsque la base existe déjà. Les sources conservent URL canonique,
langue, publication, consultation, empreinte, état de validation et intervalle d'effet.

`rules check-card` exige un ID d'impression TCGdex local, le format, la plateforme et
une date. `rules check-deck` ne lit que la dernière version exacte et ne la modifie pas.
Les résultats `legal`, `not_legal` et `unknown` comprennent des codes de raison, les
sources utilisées et les données manquantes. Une marque H/I/J seule ne donne pas
`legal` si la couverture des restrictions n'est pas prouvée; une marque ancienne ne
donne pas `not_legal` sans vérification des réimpressions fonctionnelles. Une carte
réglementairement légale ne prouve ni support de cette impression dans Live, ni
possession ou fabrication. La couverture et les réserves sont détaillées dans
`docs/REGLES_LEGALITE.md` et `docs/PM-0005A_SOURCE_AUDIT.md`.

Le contrôle de deck couvre maintenant le total 60, la somme des quantités, la limite
par nom canonique, l'exception Énergie de base et la présence d'au moins un Pokémon de
base à partir d'une règle officielle datée. Comme le registre des exceptions spéciales
n'est pas exhaustif, un deck structurellement plausible peut rester `unknown`; les
cas 59/61 et l'absence démontrée de Pokémon de base sont `not_legal`.

### Métagame Limitless descriptif

`meta sync --dry-run` n'utilise ni réseau ni écriture. Le mode par défaut `discover`
isole les exclusions par jeu/format/plateforme/online. Il réanalyse la tête, relit une
page de chevauchement et reprend un checkpoint profond persistant; une page interrompue
ou une frontière vide/partielle est revisitée. `--max-tournaments` borne les imports
réussis, pas l'examen des candidats exclus. `--mode refresh` revalide explicitement
les snapshots et exclusions scoppées les plus anciens, notamment après correction du
fournisseur. La pagination n'est pas atomique : ces mécanismes réduisent les omissions
et exposent l'horizon observé dans la sortie JSON, sans prétendre fournir un instantané
global ou exhaustif.

Une synchronisation réelle ne fait que des GET publics allowlistés sur
`play.limitlesstcg.com/api`, avec budget, taille maximale, timeout et retries comptés.
La même allowlist contrôle URL initiale, redirections et URL finale. L'endpoint
protégé `/games/{id}/decks` reste interdit, même par redirection. Chaque GET de
redirection est débité avant transmission; budget ou quota fournisseur restant à
zéro arrête donc l'invocation avant le GET suivant. Aucun service ni planificateur
n'est installé.

Le schéma 7 conserve les filtres PTCG/format/plateforme/online/date, la provenance et
des références HMAC différentes par tournoi. Il ignore noms, pays, pseudos et
decklists. Les archétypes viennent uniquement du champ public `standing.deck.id`;
absent signifie `unknown`. Les matchups excluent les résultats ambigus et séparent
phase et BO. Sous `--min-sample`, aucun pourcentage n'est affiché. Ces résultats ne
représentent ni tous les tournois, ni la légalité, ni un taux attendu pour le joueur.
Un refresh devenu privé ou incompatible marque l'ancien snapshot `partial`, l'exclut
des agrégats actuels et conserve son historique local. Le champ `excluded` des
matchups couvre tous les matchs des tournois filtrés, pas seulement l'archétype ciblé.
Voir `docs/METAGAME_LIMITLESS.md`, `docs/PM-0005B_SOURCE_AUDIT.md` et
`docs/PM-0005B-R1_AUDIT.md`, puis `docs/PM-0005B-R2_AUDIT.md`.

`meta coverage` ne calcule aucun winrate. Il expose période, fraîcheur, snapshots
complets/partiels, statuts fournisseur non interprétés, placements classifiés,
matchs admissibles/classifiables, phases, BO et exclusions pour le contexte public
demandé. Trainer Hill demeure bloqué faute d'API publique et de conditions
d'automatisation vérifiées; aucun scraping de repli n'est effectué.

### Audit intégré et questions dans Codex

`knowledge status` et `knowledge audit` sont entièrement hors ligne et ouvrent la
base en lecture seule. Ils regroupent les métriques sans mélanger catalogue, règles,
support Live, possession et métagame, puis proposent les prochaines actions avec un
budget exact seulement lorsqu'il est démontrable. Le second vérifie aussi intégrité,
clés étrangères, FTS5 et état A1–A5. Le skill `knowledge` route les questions usuelles
vers les commandes locales et exige source/date/langue/contexte. Voir
`docs/AUDIT_CONNAISSANCES.md` et `docs/LOT_A_ACCEPTANCE_MATRIX.md`.

### Actualisation publique locale

`knowledge update --dry-run` ne fait ni réseau ni écriture. Une exécution publique
réelle exige `--apply --confirm-owner`, respecte les budgets TCGdex/Pokémon officiel/
Limitless et ne transmet aucune donnée personnelle. Les changements de pages
officielles restent `non_verified/conflict` jusqu’à validation de leur contenu : un
HTTP 200, ETag ou hash différent ne modifie jamais seul les règles actives.

`knowledge update status` relit hors ligne le dernier cycle, les compteurs et alertes.
La cadence profonde utilise `zoneinfo` Toronto avec DST, une heure explicitement
configurée et un rattrapage unique après arrêt. Les logs anonymisés et verrous restent
sous `data/local/`. La commande `knowledge scheduler ... --dry-run` rend les deux
manifests Windows sans contacter le planificateur; toute tentative réelle refuse avec
`SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D`. Détails et limites :
`docs/LOT_D_PUBLIC_UPDATE_GUIDE.md` et `docs/LOT_D_ACCEPTANCE_MATRIX.md`.

### Diagnostic personnel en lecture seule

`analyze deck` sélectionne toujours la dernière version enregistrée du deck demandé;
une version récente non confirmée n'est jamais remplacée silencieusement par une
ancienne version exacte. La commande rapproche hors ligne les quantités du deck, la
résolution TCGdex, le verdict conservateur de `rules check-deck`, les combats associés
et le cache Limitless dans le contexte format/plateforme/date demandé.

Les combats restent attribués à la version choisie seulement lorsqu'un lien local
explicite le prouve. Le rapport donne `facts`, `evidence`, `unknowns`, `next_evidence`
et `warnings`, avec `read_only: true` et `network_used: false`; il ne montre ni liste
de cartes, journal, pseudo, chemin Windows, empreinte privée ou référence HMAC. Même
avec cinq combats, aucun taux attendu, matchup personnel, meilleur deck, achat ou coût
en crédits n'est inventé. Contrat détaillé : `docs/PM-0006A_ANALYSE.md`.

### Comparer les versions et auditer leurs preuves

`deck compare` exige deux numéros explicites appartenant au même deck. Chaque version
doit être confirmée, cohérente et totaliser 60 cartes. La clé conservatrice est
`card_type + set_code + collector_number + card_name`, normalisée de façon
déterministe; deux impressions du même nom restent distinctes et une ligne sans code
de set ou numéro demeure `identity_uncertain`. Un simple réordonnancement produit
zéro changement et `delta_total` reste zéro entre deux listes de 60 cartes.

Par défaut, la sortie ne contient que les agrégats. `--show-changes` est l'option
volontaire qui révèle localement noms, codes et quantités avec un avertissement privé;
ces détails ne doivent pas être publiés. S'il n'existe qu'une version, la commande
retourne `INSUFFICIENT_DECK_VERSIONS` au lieu d'en inventer une. La comparaison ne
déduit jamais légalité, possession, équivalence fonctionnelle ou amélioration.

`deck version-evidence` distingue le `deck_id` déclaré à l'import d'un lien explicite
dans `battle_deck_versions`. Elle compte séparément liens cohérents, absences de lien,
conflits de deck/version et doutes temporels, puis produit des références locales
opaques à confirmer. `imported_at` est seulement la date d'import du journal, pas une
preuve de date réelle de partie. Les issues ne sont attribuées à une version que si
le lien stocké est cohérent; aucun taux prédictif ni comparaison de rendement n'est
produit. Contrat complet : `docs/PM-0006B_VERSION_EVIDENCE.md`.

### Confirmer ou révoquer un lien combat-version

Le schéma 8 conserve une attestation distincte des dates de création de la version.
`deck link-candidates` liste uniquement des clés SQLite locales stables, sans journal,
pseudo, empreinte ni carte. `deck link-battle` est une prévisualisation sans écriture
par défaut; `--apply` exige toujours `--confirm-owner` et cible exactement un combat
et une version 60/60. Il n'existe aucune option globale. `--battle-date YYYY-MM-DD`
permet de déclarer volontairement la date réelle; sans elle, cette date reste inconnue.

Une confirmation écrit `confirmed_at` en UTC avec provenance `owner_asserted`; ce
n'est pas une vérification indépendante. Elle n'est jamais visible dans un rapport
`--as-of` antérieur. `deck unlink-battle` révoque seulement une attestation créée par
ce mécanisme, conserve sa ligne d'audit et retire son lien actif transactionnellement.
Un lien historique sans attestation n'est ni effacé ni transformé en déclaration du
propriétaire. Détails et limites : `docs/PM-0006C_MANUAL_ATTESTATIONS.md`.

## Qualité et sécurité

```powershell
python -m pytest
```

L'import des volumes, les consultations et les recherches, y compris toutes les
commandes `rules`, n'utilisent pas le réseau; seules les commandes explicites
`cards sync`, `meta sync`, `knowledge update --apply` et le probe public distinct y
accèdent. Les sources Markdown, API,
journaux et images sont toujours traités comme des données non fiables : aucune
commande qu'ils contiennent n'est exécutée. Les conseils issus des volumes restent
datés du 9 octobre 2026 et doivent être revérifiés auprès des sources officielles
pour les règles, rotations, errata et légalité courante.

SQLite FTS5 et la bibliothèque standard suffisent pour ce corpus. Un moteur
vectoriel, LangChain, un service cloud ou un LLM local ajouteraient des coûts, des
permissions et de l'opacité sans besoin démontré. L'audit TCGdex et ses limites sont
dans `docs/PM-0004_AUDIT.md`; l'audit Limitless est dans
`docs/PM-0005B_SOURCE_AUDIT.md`, avec le correctif d'intégrité dans
`docs/PM-0005B-R1_AUDIT.md` et la reprise durable dans
`docs/PM-0005B-R2_AUDIT.md`.

## Portée

PokeMind fournit conseil et analyse. Il n'automatise pas le client de jeu, ne lit
pas les informations cachées et ne doit pas être utilisé là où l'assistance est
interdite. L'état détaillé et la reprise se trouvent dans `.orchestrator/`.
