# Mode du message et contexte allégé — 2026-11-02

À gauche d'**Envoyer**, la liste **Coach / Recherche web / Développement** choisit ce que fait le message; rien
n'est plus déduit des mots de la phrase (audit A-8). **Coach** répond avec la mémoire locale et le catalogue, sans
Internet. **Recherche web** fait une collecte publique bornée avant la réponse, pour ce message seulement, puis la
liste revient à Coach (l'idée de question « Cherche les changements récents de la méta… » la sélectionne).
**Développement** confie le message à Codex ou Claude sur le code de PokeMind (absent dans une copie installée).
Un journal collé reste toujours traité par le coach isolé.

Le coach reçoit moins de données collées (audit A-7) : les familles nommées dans la question et les 15 qui te
battent le plus (les autres via l'outil `context`), et, dans une même session Codex ou Claude, seulement ce qui a
changé depuis le message précédent. Après un échec, un arrêt, une nouvelle discussion ou un changement de moteur,
tout est renvoyé.

---

# Accueil, cartes, chat et statistiques visuelles — 2026-10-27

L'accueil rassemble les favoris de Deck Lab, les parties à reprendre et un point de travail tiré du rapport conservé. L'étoile de Deck Lab mémorise une liste exacte comme référence favorite; elle ne l'atteste pas comme deck joué ou légal. Les parties sont présentées dans l'ordre du rapport lorsque leur date n'est pas attestée. Le menu peut se replier en conservant ses icônes, ses info-bulles et la navigation clavier.

**Tes statistiques, en images** propose quatre vues : bilan du corpus, résultats empilés par famille adverse, derniers tours observés et occurrences d'événements consignés. Les vues détaillées se filtrent par résultat; cliquer une famille ouvre ses combats. Le bilan reste celui du corpus complet. Les effectifs globaux et le nombre de parties détaillées disponibles restent séparés. Les tours inconnus restent visibles; un dernier tour observé n'est pas une durée complète et une prise de Récompenses peut porter sur plusieurs cartes. Aucun taux de victoire global ou effet causal n'est déduit.

Les illustrations déjà autorisées ont un survol avec reflet/relief léger et un zoom animé. Sans image disponible ou permise, le texte local reste affiché. **Réduire les animations** désactive aussi ces nouveaux effets.

Le coach conserve une seule conversation, présentée en bulles. **Sources regroupées** ouvre les liens cités dans les réponses, sans collecte ni aperçu réseau; jusqu'à 50 sources sont regroupées, les messages complets restant conservés. Les fiches de combat présentent une frise des seuls événements disponibles, avec inconnues explicites. Les fonctions d'import, sources et permissions restent les mêmes.

---

# Animations Pokédex — 2026-10-27

Les pages apparaissent avec un fondu et un léger glissement. Les boutons et panneaux s'illuminent au survol, un clic produit une onde discrète et la Poké Ball du tableau de bord réagit au pointeur. Les graphiques se dessinent progressivement; les nombres affichés restent les vraies valeurs du rapport. Les effets s'arrêtent au repos et lorsque leur page est cachée.

Dans **Réglages**, cocher **Réduire les animations et afficher les pages instantanément** désactive ces effets et conserve ce choix pour les prochaines ouvertures. Les réglages défilent verticalement dans les petites fenêtres; les libellés des cases à cocher passent sur plusieurs lignes.

---

# Habillage Pokédex — 2026-10-27

Navigation anthracite, sélection rouge, accents jaunes, bannière d'entraînement et Poké Ball dessinée localement. Les thèmes clair et sombre restent sélectionnables dans Réglages; graphiques et catégories de cartes suivent le thème. Le tableau de bord défile dans les petites fenêtres. Aucun téléchargement d'illustration ou de police n'est nécessaire pour cet habillage.

---

# Mise à jour courante — assistant unifié livré / AWAITING_AUDIT

2026-10-27 Québec. Après lancement explicite, **une conversation** relie Codex App Server par défaut, actions projet Codex/Claude, import+question, reconstruction hypothétique60 et mémoire Web permanente dans le cerveau existant. [Utilisation et contrats](UNIFIED_ASSISTANT_IMPLEMENTATION.md), [preuves](../.orchestrator/EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md), [état](../.orchestrator/STATE.json).

Les mentions datées de conception non lancée, terminal séparé ou chat exclusivement en lecture seule ci-dessous sont historiques et supplantées par cette livraison. Le coach conserve ses permissions propres; le développement est sélectionné par demande utilisateur explicite dans le même fil. Cloud ordinaire autorisé et mémorisé, aucun brut de journal envoyé automatiquement. Aucune migration SQLite personnelle ni nouveau backup. **V1 NOT_RELEASE_READY; STOP audit indépendant.** Réception Windows rapportée par l'exécuteur, CI au SHA final limitée par le budget Actions, sans succès présumé.

---

# Cible actuelle — UNE conversation, conception en revue

2026-10-26. L'application existante ci-dessous contient déjà le chat en lecture seule, l'import local et les six écrans. La cible corrigée étend **ce même fil** avec outils Codex/Claude, /status officiel, reconstruction probable et recherche mémorisée; aucun chat/terminal Codex Direct séparé. [Cahier](UNIFIED_POKEMIND_ASSISTANT_DESIGN.md), [inventaire/CI](../.orchestrator/VERIFICATION_PM_V1_UNIFIED_ASSISTANT_REPRISE.md), [mandat majeur proposé](../.orchestrator/MANDATES/PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md).

**DESIGN_READY_OWNER_REVIEW, execute_now=false : extensions non lancées.** Le guide des capacités existantes suit; ne pas confondre celles-ci avec la cible complète. L'ancien mandat ConPTY à deux conversations est annulé. V1 NOT_RELEASE_READY.

---

# Ouvrir PokeMind Desktop sur Windows

## Coller un combat et recevoir ses conseils

Dans **Pose ta question à PokeMind**, colle directement le journal TCG Live,
puis appuie sur **Enter**. **Shift+Enter** ajoute une ligne. Tu peux aussi joindre
ou glisser un fichier `.txt` ou `.log` : seul le fichier choisi est lu, sa source
reste intacte et la copie acceptée est conservée dans le projet PokeMind.

PokeMind reconnaît et valide le journal **localement avant tout fournisseur IA**.
Il vérifie joueur, deux participants, tours et victoire/défaite finale. Un fragment,
un collage ambigu ou un résultat contradictoire reste local et n'ajoute aucune
partie. La limite du parseur est **2 Mo par journal**, distincte des questions
ordinaires. Jusqu'à20 pièces jointes sont traitées successivement.

Le chat affiche les étapes réelles : journal reconnu, enregistrement, analyse,
partie enregistrée/doublon/refus, résultat et adversaire fiables, nouvelles parties
uniques et statistiques. **Consulter l'analyse de la partie** ouvre sa chronologie.
Les fichiers sont publiés atomiquement sous un nom unique; aucun journal existant
n'est remplacé. Les doublons historiques sont recherchés dans le dossier, le
rapport canonique et les empreintes d'import SQLite disponibles. La comparaison
du texte ignore Unicode équivalent, fins de ligne, lignes vides et indentation;
elle conserve le contenu du jeu et ne suppose pas deux parties identiques à partir
d'une simple ressemblance d'archétype.

L'actualisation appelle le moteur `battle_coach` et le Learning Loop existants.
Une empreinte de fraîcheur locale lie fichiers, date/moteur et snapshot validé;
si rien n'a changé, le rapport est relu sans retraitement complet. Cet index
technique ne stocke aucune statistique concurrente. Les journaux et les notifications
d'import sont exclus des messages suivants vers Codex/Claude/Ollama. Un ancien
historique contenant un journal est isolé dans un nouveau fil fournisseur, sans
supprimer l'historique local; le dialogue normal reprend ensuite sur le fil sûr.

## Réponses fondées sur tes données et activité

Les questions sur tes combats/statistiques/decks consultent d'abord le rapport
local validé et sa mémoire : chiffres du corpus, W/L/n, date, observations,
hypothèses et liens internes. La méta publique complète ces connaissances.
Les totaux personnels restent présents même quand le contexte doit être réduit.

Tes préférences cloud existantes sont conservées :

| Choix mémorisé | Question personnelle |
|---|---|
| Cloud autorisé + statistiques anonymisées | Codex/Claude reçoit les agrégats bornés du rapport local. |
| Connaissances publiques seulement, ou cloud non autorisé | PokeMind répond localement avec les chiffres réels, sans transmettre les statistiques. |
| Ollama sélectionné et disponible | Consultation locale et contexte envoyés au serveur loopback choisi par l'application. |

L'indicateur animé affiche le temps réellement écoulé et l'étape : consultation
locale, connexion/attente, génération, terminé/interrompu/erreur. Aucun pourcentage
n'est estimé. Le streaming et **Arrêter** restent disponibles. L'analyse d'un corpus
volumineux peut prendre du temps; la navigation de l'application reste utilisable.

## Démarrage, graphiques et cartes

Dans **Réglages**, active **Actualiser automatiquement mes combats au démarrage**
pour vérifier les fichiers en arrière-plan et afficher le nombre de nouvelles
parties uniques. L'option est mémorisée, désactivée initialement. L'option de
surveillance pendant l'ouverture vérifie les changements toutes les5 secondes,
puis attend au moins10 secondes de stabilité avant l'analyse; aucun service,
scheduler ou surveillance de GitHub n'est installé.

La vue d'ensemble sépare **corpus enregistré**, répartition descriptive et
priorités pédagogiques par défaites. **Le taux de victoire global est inconnu**
tant que la représentativité n'est pas établie, même si des victoires sont ajoutées.

**Deck Lab / Galerie** regroupe Pokémon, Dresseurs et Énergies avec quantités,
60/60, miniatures et agrandissement au clic. La liste texte et les versions restent
disponibles. La recherche de cartes conserve son sélecteur FR/EN; les illustrations
de galerie privilégient FR et utilisent EN si nécessaire. Une impression non
résolue ou une image absente/non permise garde une tuile nommée propre.

Les images proviennent des URLs publiées par l'API TCGdex, avec hôtes HTTPS limités,
taille/dimensions/budget bornés, provenance/date/empreinte et cache sous
`data/local/card-images`. Les paramètres peuvent désactiver leur affichage et les
nouvelles requêtes. Les illustrations restent soumises aux droits Pokémon,
Nintendo, Creatures et GAME FREAK; la licence MIT des données/code n'est pas
présumée couvrir les illustrations. Usage personnel local; aucune image du cache
dans Git ni dans le portable distribué. [Documentation des images](https://tcgdex.dev/assets),
[images manquantes et API](https://tcgdex.dev/faq). Un refus source ferme les
nouvelles tentatives automatiques de la session; le cache reste consultable.

QA Windows explicite : `scripts/qa_desktop_ingestion.py --real-windows --owner-codex`.
Les nouveaux imports/refus/gros collages/réouverture utilisent le vrai code et le
vrai parseur dans un corpus inventé isolé. Le rapport propriétaire, une réponse
Codex fondée sur ses agrégats, un doublon réel, les images et la galerie sont
exercés sur le PC. Aucune fausse partie ajoutée au corpus propriétaire. Captures,
réponses et preuves privées restent sous `data/local/desktop-dev`; GitHub ne
reçoit que le résultat technique assaini. Les préférences cloud de QA sont restaurées.

## Installation et écrans

Après construction, double-cliquer **`dist/PokeMind/PokeMind.exe`**. Garder
l'ensemble du dossier `PokeMind`, ses DLL et `_internal` ensemble, sous `dist`
dans le projet. Aucune console ni fenêtre ChatGPT n'est nécessaire. Le programme
retrouve le dossier du projet; s'il est déplacé, il propose de choisir ce dossier.
Les données personnelles restent dans le `data/local` du projet sélectionné.

Pour installer/reconstruire depuis les sources :

```powershell
./scripts/Install-PokeMindDesktop.ps1
./scripts/Build-PokeMindDesktop.ps1
```

Le build refuse une distribution déjà présente. Pour préparer une mise à jour,
utiliser `-StagingRoot` avec un chemin neuf sous `build/exe-upgrade-<GUID32>`
(GUID en minuscules, sans tirets). Cette option compile le vrai programme et ses
licences séparément; elle ne déploie rien. Le remplacement de l'installation et
la conservation des anciens binaires exigent le mandat de mise à jour autorisé.
`-StagingRoot` et `-SyntheticQaRoot` sont mutuellement exclusifs.

L'installation utilise uniquement `.venv-desktop` dans le projet. Python3.11+
et l'accès normal à PyPI sont nécessaires à l'installation, pas à la lecture
des données conservées. Les dépendances sont épinglées; les avis des composants
sont fournis avec le portable. Aucun fournisseur IA n'est installé par ces scripts.
Pour développer : `.venv-desktop/Scripts/python.exe -m pokemind desktop`.
`scripts/Start-PokeMindDesktop.ps1` utilise `pythonw`, sans console.

## Les six rubriques

- **Vue d'ensemble** : derniers compteurs réels, date et version du rapport,
  priorités par famille et avertissement de sélection des défaites.
- **Combats** : filtrer/trier les familles, sélectionner une partie et parcourir
  sa chronologie visible. « Discuter de ce matchup » prépare une question dans
  le chat; il ne l'envoie pas sans ton action.
- **Deck Lab** : versions personnelles exactes et modèles PUBLIC déjà conservés,
  comparaison des quantités, copie ou export d'une liste vérifiée60. L'export
  refuse de remplacer un fichier existant. Légalité, possession, crédits et
  version réellement jouée demeurent distincts.
- **Cartes & méta** : recherche FR/EN, textes, provenance et légalité datée de
  chaque impression; consultation des tournois et familles publiées conservés.
- **Apprentissage** : observations et statistiques du Learning Loop existant,
  hypothèses révisables, plans de test et limites causales.
- **Réglages** : thème sombre/clair, état des caches et partage cloud.

« Actualiser les combats locaux » exécute le service `battle_coach` existant
sur un worker. Les dossiers connus et la déduplication restent gérés par ce
moteur; aucun second cerveau n'est créé. La fermeture attend la fin de son
étape sûre. Le bouton d'arrêt de consultation/analyse demande un arrêt entre
fichiers ou transactions; les données déjà validées restent conservées et une
reprise utilise la déduplication existante. Le bouton Arrêter du chat interrompt le tour IA et garde la réponse
partielle. Les recherches et lectures lourdes fonctionnent sur workers.

## Chat : Codex, Claude Code et Ollama

Codex est sélectionné au premier lancement. L'application lance **le CLI déjà
installé** avec `codex app-server --stdio`. Elle réutilise son authentification;
elle ne lit pas les fichiers de jetons et ne suppose aucune nouvelle clé API.
Le fil de discussion est associé à l'historique PokeMind, et repris par
`thread/resume`. Les messages arrivent en streaming. Nouvelle discussion,
Arrêter, Copier la réponse et Reprendre une discussion sont dans le panneau.

Claude Code utilise son CLI officiel `-p --output-format stream-json`, avec
reprise de session. Si le CLI est absent, l'état l'indique; en cas d'auth absente,
ouvrir et connecter le CLI habituel. L'application ne connecte aucun compte
à ta place. Aucun basculement automatique de fournisseur.

Ollama consulte uniquement `127.0.0.1:11434`, liste les modèles déjà installés et
diffuse `/api/chat`. Choisir explicitement un modèle disponible. Aucun modèle
n'est téléchargé automatiquement; RAM/VRAM et vitesse dépendent du modèle et
du PC. En l'absence du serveur local, les données et les autres moteurs restent
utilisables. Les tests CI utilisent un serveur HTTP local inventé.

Les questions au chatbot utilisent les services en lecture seule : consultation bornée des services
PokeMind, sources, date, W/L/n si le partage choisi le permet. Il n'expose pas
un terminal ou le shell de développement. Les commandes de terminal personnelles
restent utilisables séparément. Les outils système, plugins et hooks sont
désactivés dans le processus Codex géré, les demandes d'actions externes sont
refusées; Claude est lancé sans outils et sans personnalisations. Les écritures
d'import passent uniquement par le pipeline local fixé décrit ci-dessus; l'IA ne
reçoit pas ce journal. Aucune migration, sauvegarde, suppression ou modification du jeu.

## Partage et historique

Codex et Claude sont des **services cloud**. Dans Réglages, autoriser une fois
l'envoi des questions et choisir le contexte : connaissances publiques seules,
ou ajout de statistiques de combats anonymisées et bornées. Cette préférence
est mémorisée; il n'y a pas de confirmation par fichier. Les journaux bruts,
images, pseudos, chemins et empreintes personnelles ne font pas partie du contexte
automatique. Le texte que tu saisis est un message destiné au moteur choisi.
Ollama effectue les échanges seulement avec le serveur local.

Les statistiques partagées concernent un échantillon de journaux choisi,
avec surreprésentation volontaire des défaites pour apprendre. Elles ne mesurent
pas le taux de victoire global ni la force générale d'un matchup. Les événements
et noms d'attaques ne prouvent pas la cause d'une défaite ou un deck adverse60.

Préférences, historiques et identifiants des fils restent exclusivement sous
`data/local/chat`, ignoré par Git. Ils sont séparés de la mémoire factuelle du
cerveau. Un changement de portée de partage démarre un nouveau fil fournisseur
au prochain message; il n'efface pas les données déjà transmises auparavant.

Si la DB personnelle est encore en schéma7, le rapport dérivé conserve le
coaching. Aucun passage7→13 ou nouvelle DB n'est exécuté par l'ouverture.
Les caches PUBLIC absents donnent des états vides ou indisponibles explicites.

## Vérification et limites

`scripts/qa_desktop_runtime.py --real-windows-codex` est une QA explicite de la
vraie fenêtre et du CLI connecté. Elle pose seulement des questions publiques,
vérifie deux tours, streaming, reprise et arrêt, consulte les données localement
et conserve ses captures/preuves sous `data/local/desktop-dev`. Elle n'est pas
exécutée sur CI. Les tests Qt de CI sont inventés/offscreen.

Le portable Windows a été compilé et ouvert localement selon Codex. Ce constat
terrain n'est pas certifié par GitHub. Le binaire local n'est pas signé ni
publié comme release GitHub; le code et les preuves assainies sont soumis à
l'audit indépendant. **V1 NOT_RELEASE_READY** pour les portes restantes.
