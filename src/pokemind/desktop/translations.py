"""Reviewed English equivalents for app-authored French UI text only."""
import re

_PAIRS = r'''
TON COMPAGNON TCG|||YOUR TCG COMPANION
TON COACH POKEMIND|||YOUR POKEMIND COACH
TON AVENTURE, EN MÉMOIRE|||YOUR JOURNEY, REMEMBERED
Mémoire locale · conseils sourcés\nV1 · audit requis|||Local memory · sourced advice\nV1 · audit required
Replier le menu|||Collapse menu
Replier ou déplier la navigation|||Collapse or expand navigation
Navigation principale|||Main navigation
Déplier la navigation|||Expand navigation
Replier la navigation|||Collapse navigation
Vue d’ensemble|||Overview
Combats & adversaires|||Battles & opponents
Combats|||Battles
Cartes & méta|||Cards & meta
Cartes / méta|||Cards / meta
Apprentissage|||Learning
Réglages|||Settings
Langue de l’application|||Application language
Le choix s’applique immédiatement et sera conservé au prochain lancement.|||Your choice applies immediately and is saved for the next launch.
Impression|||Printing
Langue|||Language
Nom|||Name
Lexique|||Card reference
Effet|||Effect
aucune image|||no image
Extraction :|||Extraction:
application courante : unknown.|||current applicability: unknown.
en personne|||in person
Champs extraits (extracted_unverified) : rotation Standard, plateforme|||Extracted fields (extracted_unverified): Standard rotation, platform
marques rapportées :|||reported marks:
publication :|||publication:
date d’effet annoncée :|||announced effective date:
Équivalence de réimpression : unknown; disponibilité dans Live : unknown; restrictions et texte effectif non certifiés.|||Reprint equivalence: unknown; Live availability: unknown; restrictions and effective text are not certified.
 à ||| to\u0020
Ton tableau de bord|||Your dashboard
Une partie à la fois. Un peu plus loin à chaque combat.|||One game at a time. A little further with every battle.
CENTRE D’ENTRAÎNEMENT|||TRAINING CENTER
À toi de jouer.|||Your turn to grow.
Ton équipe. Tes combats. Ta progression.|||Your team. Your battles. Your progress.
Parties analysées|||Games analyzed
Victoires enregistrées|||Recorded wins
Défaites à travailler|||Losses to learn from
Tes decks favoris|||Your favorite decks
Parties à reprendre|||Games to revisit
Ton prochain point à travailler apparaîtra ici avec le rapport.|||Your next focus will appear here with the report.
À travailler :|||Focus on:
Prochain objectif : conserver des observations et comparer un changement à la fois.|||Next goal: save observations and compare one change at a time.
Marque un deck d’une étoile dans Deck Lab pour le retrouver ici.|||Star a deck in Deck Lab to find it here.
Favoris conservés; leurs références ne sont pas disponibles dans le rapport chargé.|||Favorites saved; their references are unavailable in the loaded report.
Les parties détaillées apparaîtront ici avec le rapport.|||Detailed games will appear here with the report.
version jouée et légalité à vérifier|||played version and legality need checking
Limite de 100 favoris atteinte.|||The limit of 100 favorites has been reached.
Favori|||Favorite
Priorités de travail|||Learning priorities
Choisis une famille pour retrouver les parties et distinguer les observations des hypothèses.|||Choose a family to find its games and separate observations from hypotheses.
CORPUS ENREGISTRÉ · Statistiques des parties conservées. Les défaites guident l’apprentissage; le taux de victoire global reste inconnu tant que la représentativité n’est pas établie.|||RECORDED CORPUS · Statistics for saved games. Losses guide learning; the overall win rate remains unknown until representativeness is established.
Actualiser les combats locaux|||Refresh local battles
Arrêter la consultation / analyse|||Stop lookup / analysis
Classement descriptif des défaites enregistrées · familles hypothétiques · n toujours visible.|||Descriptive ranking of recorded losses · hypothetical families · sample size always visible.
Filtrer les familles adverses…|||Filter opponent families…
Famille / signature|||Family / signature
Choisis une famille et une partie pour voir sa fiche.|||Choose a family and a game to see its details.
Discuter de ce matchup avec PokeMind|||Discuss this matchup with PokeMind
Dans mes combats, quelles situations travailler contre|||In my battles, which situations should I work on against
? Cite n, les sources et ce qui reste inconnu.|||? Include sample size, sources, and what remains unknown.
Aucune partie sélectionnée.|||No game selected.
Versions exactes et modèles PUBLIC · collection, crédits et légalité distincts.|||Exact versions and PUBLIC references · collection, credits, and legality are separate.
Ajouter ou retirer ce deck des favoris|||Add or remove this deck from favorites
Chargement des références…|||Loading references…
Galerie · 60/60|||Gallery · 60/60
Liste texte|||Text list
Copier les 60 cartes|||Copy all 60 cards
Exporter en fichier texte…|||Export to text file…
Comparer à cette référence|||Compare with this reference
Une différence de cartes ne prouve pas une amélioration.|||A difference in cards does not prove an improvement.
Aucune référence exacte de 60 cartes disponible localement.|||No exact 60-card reference is available locally.
possession / crédits inconnus.|||ownership / credits unknown.
Liste de 60 cartes copiée; légalité à vérifier.|||60-card list copied; legality needs checking.
Exporter les 60 cartes|||Export all 60 cards
Texte (*.txt)|||Text (*.txt)
Export refusé : fichier existant ou destination indisponible.|||Export refused: the file exists or the destination is unavailable.
copies communes.|||copies in common.
Équivalences de réimpression et efficacité non établies.|||Reprint equivalence and effectiveness are not established.
Référence personnelle · candidat non joué|||Personal reference · unplayed candidate
Candidat enregistré · non joué|||Saved candidate · not played
Référence personnelle; version jouée non attestée|||Personal reference; played version not attested
Référence PUBLIC|||PUBLIC reference
Variante PUBLIC|||PUBLIC variant
Deck enregistré · version|||Registered deck · version
Standard / Live inconnus|||Standard / Live unknown
Légalité datée à vérifier pour chaque impression|||Dated legality must be checked for each printing
Bibliothèque FR/EN et tournois conservés · fonctionnement hors ligne.|||FR/EN library and saved tournaments · available offline.
Nom de carte, talent, attaque…|||Card name, Ability, attack…
Français (Québec)|||Français (Québec)
Français|||French
Rechercher|||Search
Consulter les tournois et compositions conservés|||View saved tournaments and compositions
Méta datée|||Dated meta
Carte sélectionnée|||Selected card
Choisir une impression|||Choose a printing
Impression inconnue|||Unknown printing
Image indisponible|||Image unavailable
Image absente ou non autorisée; texte local conservé.|||Image missing or not authorized; local text retained.
TCGdex · illustration Pokémon · cache local|||TCGdex · Pokémon artwork · local cache
Usage personnel local, aucune redistribution.|||Local personal use, no redistribution.
Énergies|||Energy
ÉNERGIE|||ENERGY
DRESSEUR|||TRAINER
Dresseurs|||Trainers
cartes|||cards
Agrandir|||Enlarge
Fermer|||Close
Impression, réimpression, disponibilité Live et possession sont distinctes.|||Printing, reprints, Live availability, and ownership are separate.
Compléments français publiés et attribués|||Published and attributed French supplements
Texte officiel français et impression française non prouvés par ces compléments.|||These supplements do not establish official French text or a French printing.
Standard présentiel :|||In-person Standard:
 · PV ||| · HP\u0020
 · Live : ||| · Live:\u0020
Fraîcheur du cache :|||Cache freshness:
 · au ||| · as of\u0020
Consultée :|||Accessed:
à revalider|||needs revalidation
selon la date de consultation ci-dessus|||according to the access date above
Conditions sur la page source|||Terms on the source page
Échantillon de tournois conservé|||Saved tournament sample
placements|||placements
compositions distinctes. Popularité et placements ne prouvent pas un matchup.|||distinct compositions. Popularity and placements do not prove a matchup advantage.
Familles publiées|||Published families
Observations, statistiques et hypothèses|||Observations, statistics, and hypotheses
Les observations sont conservées. Les hypothèses se révisent. Aucun réentraînement de modèle.|||Observations are saved. Hypotheses can be revised. No model retraining.
Journal Learning Loop absent ou indisponible; rapport conservé consultable.|||Learning Loop journal missing or unavailable; the saved report can be viewed.
Événements observés :|||Observed events:
parties; faits préservés.|||games; facts preserved.
Bilan descriptif du corpus sélectionné; aucune causalité.|||Descriptive summary of the selected corpus; no causal inference.
Base à tester :|||Reference to test:
référence60 dans Deck Lab|||60-card reference in Deck Lab
Avantage de matchup inconnu.|||Matchup advantage unknown.
Un changement à la fois; aucune amélioration causale démontrée.|||One change at a time; no causal improvement demonstrated.
Plan de test ou classification révisable. Version jouée et effet causal inconnus.|||Revisable test plan or classification. Played version and causal effect unknown.
Révision datée|||Revision dated
préservée dans l’historique.|||preserved in history.
Préférences locales · tes connexions CLI existantes · aucun compte à recréer ici.|||Local preferences · your existing CLI connections · no new account needed here.
Thème sombre|||Dark theme
Thème clair|||Light theme
Réduire les animations et afficher les pages instantanément|||Reduce motion and show pages instantly
Codex et Claude utilisent leurs services cloud : tes messages et le contexte choisi peuvent leur être envoyés. Ollama utilise uniquement le serveur local. Les journaux bruts, identités et chemins sont exclus du contexte automatique.|||Codex and Claude use cloud services: your messages and selected context may be sent to them. Ollama uses only the local server. Raw logs, identities, and paths are excluded from automatic context.
J’autorise l’envoi de mes questions à Codex / Claude (cloud)|||I allow my questions to be sent to Codex / Claude (cloud)
Connaissances publiques seulement|||Public knowledge only
connaissances publiques seulement|||public knowledge only
Ajouter statistiques, listes et événements sélectionnés anonymisés et bornés|||Include bounded, anonymized selected statistics, lists, and events
Standard · shell avec accès aux données privées|||Standard · shell can access private data
Accès complet · équivalent --yolo|||Full access · equivalent to --yolo
Projet relatif à PokeMind : .|||Project relative to PokeMind: .
Case cochée, chaque question tapée part au moteur dans le dossier choisi; sinon, les outils de développement répondent seulement à une demande explicite. Les outils de fichiers refusent data/. Les commandes Codex utilisent sa sandbox workspace-write (écritures dans le projet, lectures selon le CLI). En standard comme en accès complet, un shell peut lire et modifier data/local et renvoyer son contenu au fournisseur et à son historique cloud. Claude ne fournit pas de sandbox native Windows. Choisir un sous-dossier sans données privées ne bloque pas les chemins absolus ni les alias. Une isolation externe vérifiée est nécessaire pour garantir cette frontière; elle reste non résolue dans cette version. Le flux Pokémon continue d’exclure les journaux bruts du contexte automatique.|||When checked, every typed question goes to the engine in the chosen folder; otherwise development tools answer only an explicit request. File tools refuse data/. Codex commands use its workspace-write sandbox (project writes, reads according to the CLI). In both standard and full-access mode, a shell can read and modify data/local and send its contents to the provider and cloud history. Claude has no native Windows sandbox. Choosing a subfolder without private data does not block absolute paths or aliases. Verified external isolation is needed to guarantee this boundary; it remains unresolved in this version. The Pokémon workflow continues to exclude raw logs from automatic context.
Révoquer les consentements de développement|||Revoke development consent
Actualiser automatiquement mes combats au démarrage|||Automatically refresh my battles at startup
Surveiller les nouveaux journaux pendant que PokeMind est ouvert (temporisation 10 s)|||Watch for new logs while PokeMind is open (10-second delay)
Afficher les illustrations publiques TCGdex et conserver leur cache local|||Show public TCGdex artwork and keep a local cache
État des caches en cours de lecture…|||Reading cache status…
Dossiers gérés : data/local/battle_logs · battle-intelligence · chat\nSi SQLite legacy7 : conseils disponibles, import bloqué, aucune migration automatique.|||Managed folders: data/local/battle_logs · battle-intelligence · chat\nFor legacy7 SQLite: advice available, import blocked, no automatic migration.
Vérifier le moteur sélectionné|||Check selected engine
\n[Fichiers modifiés · |||\n[Files changed ·
\n[Outil · |||\n[Tool ·
Copier le diagnostic (journal local masqué)|||Copy diagnostics (masked local log)
Diagnostic copié · journal local : |||Diagnostics copied · local log:
Assistant PokeMind|||PokeMind assistant
Moteur de discussion|||Conversation engine
Codex · session CLI|||Codex · CLI session
Claude Code · session CLI|||Claude Code · CLI session
Ollama · local|||Ollama · local
Modèle Ollama installé|||Installed Ollama model
Connexion au premier message · outils selon ta demande|||Connects on first message · tools according to your request
Contexte cloud : connaissances publiques; statistiques sur opt-in dans Réglages.|||Cloud context: public knowledge; statistics require opt-in in Settings.
Contexte cloud :|||Cloud context:
statistiques anonymisées et connaissances publiques|||anonymized statistics and public knowledge
Historique des discussions|||Conversation history
Historique|||History
Sources regroupées|||Grouped sources
Sources de la discussion|||Conversation sources
50 premières sources citées|||First 50 cited sources
Idées de questions|||Question ideas
Pose ta question ou colle ton journal TCG Live…\nEnter : envoyer · Shift+Enter : nouvelle ligne|||Ask a question or paste your TCG Live log…\nEnter: send · Shift+Enter: new line
Message à PokeMind|||Message to PokeMind
Joindre un journal|||Attach a log
Joindre…|||Attach…
Joindre des journaux .txt / .log choisis sur ton ordinateur|||Attach .txt / .log files you choose on your computer
Consulter l’analyse de la partie|||View game analysis
Envoyer|||Send
Arrêter|||Stop
Nouveau|||New
Nouvelle discussion|||New conversation
Copier la dernière réponse|||Copy the last answer
Copier|||Copy
Supprimer|||Delete
Supprimer cette discussion|||Delete this conversation
Supprimer la discussion?|||Delete the conversation?
Effacer définitivement cette discussion de PokeMind?|||Permanently erase this conversation from PokeMind?
Les copies gardées par Codex ou Claude dans leurs propres dossiers ne sont pas touchées.|||Copies kept by Codex or Claude in their own folders are not affected.
Suppression impossible; discussion conservée.|||Could not delete; conversation kept.
Discussion supprimée.|||Conversation deleted.
Discussion supprimée; index des discussions non enregistré.|||Conversation deleted; conversation index not saved.
PokeMind · questions, sources et hypothèses.|||PokeMind · questions, sources, and hypotheses.
Choisis une discussion ou pose une question.|||Choose a conversation or ask a question.
TOI|||YOU
Journal TCG Live fourni pour traitement local.|||TCG Live log provided for local processing.
Joindre des journaux TCG Live|||Attach TCG Live logs
Journaux texte (*.txt *.log)|||Text logs (*.txt *.log)
Joindre de 1 à 20 fichiers .txt ou .log choisis sur ton ordinateur.|||Attach 1 to 20 .txt or .log files you choose on your computer.
Un traitement est en cours; le collage reste dans la zone de saisie.|||Processing is in progress; pasted text stays in the input area.
Discussion pleine; ouvre une nouvelle discussion pour importer.|||Conversation full; open a new conversation to import.
Importations de combats locales|||Local battle imports
Validation du journal local|||Validating the local log
Partie enregistrée|||Game saved
Doublon détecté; aucun journal remplacé|||Duplicate detected; no log replaced
Doublon détecté|||Duplicate detected
Importation refusée|||Import refused
Journal enregistré; analyse à reprendre|||Log saved; analysis to be resumed
Traitement local terminé · aucun journal envoyé au cloud|||Local processing complete · no log sent to the cloud
Traitement interrompu à une frontière sûre; fichiers déjà enregistrés conservés.|||Processing stopped at a safe boundary; saved files retained.
Importation refusée : service local indisponible. Aucun envoi cloud.|||Import refused: local service unavailable. Nothing sent to the cloud.
Journal reconnu comme candidat|||Log recognized as a candidate
Journal refusé : fichier inaccessible, modifié, redirigé ou import déjà occupé. Aucun envoi cloud.|||Log refused: file inaccessible, modified, redirected, or import busy. Nothing sent to the cloud.
Journal trop volumineux : maximum 2 Mo par fichier.|||Log too large: maximum 2 MB per file.
Le fichier est encore en cours d’écriture; réessaie une fois terminé.|||The file is still being written; try again when finished.
Résultat reconnu :|||Recognized result:
Statistiques actualisées : n=|||Statistics updated: n=
Nouvelles parties uniques dans le corpus :|||New unique games in the corpus:
défaites. Taux global inconnu.|||losses. Overall rate unknown.
validation locale en cours. Aucun envoi au moteur IA.|||local validation in progress. Nothing sent to the AI engine.
Analyse locale en cours; ton message partira tout seul dès qu’elle sera finie.|||Local analysis in progress; your message will be sent as soon as it ends.
Outils PokeMind · consultation|||PokeMind tools · lookup
Quel deck m’a affronté dans cette partie? Identifie l’archétype adverse, reconstruis sa liste de 60 cartes (cartes vues d’abord, le reste d’après les listes publiques), donne-lui un nom et enregistre-le dans mes decks.|||Which deck did I face in this game? Identify the opponent's archetype, rebuild its 60-card list (seen cards first, the rest from public lists), give it a name and save it in my decks.
Le coach identifie maintenant le deck adverse et l’ajoute à Mes decks…|||The coach is now identifying the opponent's deck and adding it to My decks…
Pour que le coach trouve le deck adverse, coche l’envoi cloud et « Ajouter statistiques… » dans Réglages.|||For the coach to find the opponent's deck, tick cloud sending and “Add statistics…” in Settings.
Deck ajouté à Mes decks :|||Deck added to My decks:
Codex et Claude Code tels quels, comme dans une fenêtre PowerShell, dans le dossier du projet. Plusieurs onglets possibles.|||Codex and Claude Code as they are, like in a PowerShell window, in the project folder. Several tabs allowed.
Accès complet : Codex (yolo) et Claude (toutes permissions) lisent et modifient tous les fichiers du projet, y compris data/local, sans demander d’approbation. Ctrl+V colle · Ctrl+C copie la sélection (sinon interrompt) · clic droit copie ou colle · Maj+Pg↑ remonte.|||Full access: Codex (yolo) and Claude (all permissions) read and modify every project file, including data/local, without asking for approval. Ctrl+V pastes · Ctrl+C copies the selection (otherwise interrupts) · right-click copies or pastes · Shift+PgUp scrolls back.
Codex · yolo|||Codex · yolo
Claude Code · toutes permissions|||Claude Code · all permissions
Terminal indisponible : pywinpty et pyte sont requis (Windows).|||Terminal unavailable: pywinpty and pyte are required (Windows).
Terminal non démarré :|||Terminal not started:
Terminal ouvert :|||Terminal opened:
Fermer le terminal|||Close the terminal
Arrêter cette session? Le travail en cours dans cet onglet sera interrompu.|||Stop this session? Work in progress in this tab will be interrupted.
Quitter PokeMind|||Quit PokeMind
Des sessions de terminal sont ouvertes (Codex, Claude ou PowerShell). Les arrêter et quitter?|||Terminal sessions are open (Codex, Claude or PowerShell). Stop them and quit?
Mon deck · référence personnelle enregistrée par le coach|||My deck · personal reference saved by the coach
Texte trop volumineux : maximum 2 Mo pour un journal local. Aucun envoi cloud.|||Text too large: maximum 2 MB for a local log. Nothing sent to the cloud.
Message trop long ou discussion pleine; aucun contenu envoyé. Ouvre une nouvelle discussion.|||Message too long or conversation full; nothing sent. Open a new conversation.
Choisis une fois le partage cloud dans Réglages; ton message reste ici.|||Choose cloud sharing once in Settings; your message stays here.
Consultation des connaissances locales|||Looking up local knowledge
Connexion ou attente du moteur IA|||Connecting to or waiting for the AI engine
Commande officielle du moteur|||Official engine command
Génération de la réponse|||Generating answer
Réponse interrompue à ta demande.|||Answer interrupted at your request.
Tour interrompu; le résultat local ci-dessus est conservé.|||Turn interrupted; the local result above is retained.
Réponse du fournisseur indisponible; le reçu local est conservé.|||Provider answer unavailable; the local receipt is retained.
Discussion conservée|||Conversation saved
Interrompu · aucune nouvelle requête envoyée après l’arrêt|||Interrupted · no new request sent after stopping
Réponse indisponible :|||Answer unavailable:
réessayer ou choisir un autre moteur.|||try again or choose another engine.
Commande non disponible :|||Command unavailable:
Aucune session active à reprendre. Choisis une discussion dans l’historique.|||No active session to resume. Choose a conversation from history.
Session fournisseur reprise par son interface officielle.|||Provider session resumed through its official interface.
Statut réel Codex · les champs absents sont indisponibles.|||Actual Codex status · missing fields are unavailable.
Demande de compactage acceptée par thread/compact/start. L’achèvement reste à confirmer par le moteur.|||Compaction request accepted by thread/compact/start. Completion still needs engine confirmation.
Commande non exposée par cet adaptateur; aucune valeur simulée.|||Command not exposed by this adapter; no simulated value.
Exécution des outils du moteur|||Running engine tools
Outil réel|||Real tool
Code de sortie :|||Exit code:
Commande réelle :|||Actual command:
Arrêt local demandé|||Local stop requested
Arrêt du tour demandé…|||Turn stop requested…
Arrêt demandé; l’étape locale en cours atteint sa frontière sûre…|||Stop requested; the current local step is reaching a safe boundary…
Le tour se termine; fermeture ensuite.|||The turn is finishing; the window will then close.
Opération locale en cours; fermeture après son étape sûre.|||Local operation in progress; closing after its safe step.
Fermeture après la consultation locale en cours…|||Closing after the current local lookup…
Chargement des connaissances locales…|||Loading local knowledge…
Chargement du rapport conservé…|||Loading saved report…
Analyse des journaux locaux…|||Analyzing local logs…
Lecture du rapport conservé…|||Reading saved report…
fichiers traités · analyse locale en cours|||files processed · local analysis in progress
Analyse conservée au|||Analysis saved as of
mémoire locale|||local memory
Aucun rapport conservé. Ajoute tes journaux dans data/local/battle_logs, puis utilise Actualiser.|||No saved report. Add your logs to data/local/battle_logs, then use Refresh.
Tes données apparaîtront ici après la première analyse locale. Aucun résultat inventé.|||Your data will appear here after the first local analysis. No invented results.
Aucun rapport disponible|||No report available
Rapport local prêt · aucun taux de victoire global inféré|||Local report ready · no overall win rate inferred
Combats actualisés automatiquement|||Battles refreshed automatically
nouvelles parties uniques.|||new unique games.
Service indisponible|||Service unavailable
Opération arrêtée à une frontière sûre; données déjà validées conservées.|||Operation stopped at a safe boundary; validated data retained.
Actualisation automatique indisponible · rapport précédent conservé.|||Automatic refresh unavailable · previous report retained.
Recherche locale…|||Searching locally…
Vérification du moteur…|||Checking engine…
Moteur indisponible|||Engine unavailable
Préférences non enregistrées · accès local indisponible; fichiers précédents conservés.|||Preferences not saved · local access unavailable; previous files retained.
Historique indisponible; aucune discussion remplacée.|||History unavailable; no conversation replaced.
Historique non enregistré · accès local indisponible; réponse gardée dans cette fenêtre.|||History not saved · local access unavailable; answer kept in this window.
Réponse sauvegardée; index des discussions non enregistré.|||Answer saved; conversation index not saved.
ACCÈS COMPLET · --yolo volontaire · données privées accessibles|||FULL ACCESS · voluntary --yolo · private data accessible
STANDARD · shell : données privées accessibles|||STANDARD · shell: private data accessible
Activer l’accès complet?|||Enable full access?
Ce choix autorise les vrais outils Codex/Claude sans confirmations courantes. Les droits du compte Windows s’appliquent; un shell libre peut lire ou modifier des fichiers privés. Le mode s’applique aux demandes de développement, jamais aux instructions contenues dans un journal.|||This enables real Codex/Claude tools without routine confirmations. Windows account permissions apply; an unrestricted shell can read or modify private files. The mode applies to development requests, never to instructions inside a log.
Outils de développement indisponibles pour ce fournisseur.|||Development tools unavailable for this provider.
Répertoire de développement refusé; aucun contenu envoyé.|||Development directory refused; no content sent.
Développement : confidentialité non isolée|||Development: privacy is not isolated
Les shells Codex et Claude peuvent lire et modifier des fichiers privés, y compris data/local, en mode standard comme en accès complet. Leur contenu peut être transmis au fournisseur et conservé dans son historique cloud. Les filtres de fichiers et le choix du projet n’isolent pas les commandes shell; aucune garantie d’exclusion des données privées.\n\nAutoriser les demandes de développement dans cette portée malgré cette limite?\nFournisseur :|||Codex and Claude shells can read and modify private files, including data/local, in both standard and full-access mode. Their contents may be sent to the provider and kept in its cloud history. File filters and project selection do not isolate shell commands; there is no guarantee that private data is excluded.\n\nAllow development requests in this scope despite this limitation?\nProvider:
Le choix sera mémorisé pour cette portée. Le consentement cloud du coach demeure distinct.|||This choice will be saved for this scope. Coach cloud consent remains separate.
Développement arrêté : confidentialité non isolée; message conservé.|||Development stopped: privacy is not isolated; message retained.
Consentement non enregistré; développement arrêté et message conservé.|||Consent not saved; development stopped and message retained.
Consentements de développement révoqués; nouveau choix requis à la prochaine demande.|||Development consent revoked; a new choice is required for the next request.
Demande réelle du moteur|||Actual engine request
Modification de fichiers|||File changes
Exécution de commande|||Command execution
Autorisation requise par le moteur|||Authorization required by the engine
 · projet : ||| · project:\u0020
 · mode : ||| · mode:\u0020
Oui|||Yes
Non|||No
Annuler|||Cancel
Prêt|||Ready
prêt|||ready
Terminé|||Done
arrêt demandé|||stop requested
Refus ou analyse en attente|||Refused or analysis pending
Activité du coach et temps écoulé|||Coach activity and elapsed time
Répartition du corpus enregistré et priorités par défaites; taux global inconnu|||Recorded corpus distribution and loss priorities; overall rate unknown
Corpus enregistré · taux global inconnu|||Recorded corpus · overall rate unknown
Défaites par famille|||Losses by family
Victoires|||Wins
victoires|||wins
Victoire|||Win
victoire|||win
Défaites|||Losses
défaites|||losses
Défaite|||Loss
défaite|||loss
Inconnues|||Unknown
Inconnue|||Unknown
inconnu|||unknown
issues inconnues|||unknown outcomes
Issues inconnues|||Unknown outcomes
Issue inconnue|||Unknown outcome
issue inconnue|||unknown outcome
Hypothèse de famille|||Hypothetical family
Famille hypothétique|||Hypothetical family
famille hypothétique|||hypothetical family
défaites enregistrées|||recorded losses
parties uniques enregistrées :|||unique games recorded:
parties uniques|||unique games
parties|||games
partie|||game
Observé dans|||Observed in
défaites et|||losses and
causalité inconnue.|||causality unknown.
causalité non prouvée.|||causality not proven.
Tes statistiques, en images|||Your statistics, visualized
Résultats du corpus enregistré; représentativité non établie.|||Recorded corpus results; representativeness not established.
Jusqu’à 8 familles affichées. Classification hypothétique; cliquer une barre pour ouvrir les combats.|||Up to 8 families shown. Hypothetical classification; click a bar to open battles.
Dernier tour visible dans chaque trace, pas la durée complète. Les tours inconnus restent séparés.|||Last visible turn in each trace, not the full game length. Unknown turns remain separate.
Occurrences consignées dans les traces disponibles, pas toutes les actions jouées. Une prise peut concerner plusieurs Récompenses.|||Occurrences recorded in available traces, not every action played. One prize-taking event may involve several Prize cards.
Effectifs observés par famille|||Observed counts by family
Effectifs des traces disponibles|||Available trace counts
Aucune donnée disponible|||No data available
Aucune trace disponible pour cette vue.|||No traces available for this view.
Famille inconnue|||Unknown family
Vues détaillées|||Detailed views
Tous les résultats|||All outcomes
Aucun rapport conservé disponible; aucun résultat calculé.|||No saved report available; no result calculated.
Effectifs absolus · survoler pour le détail|||Absolute counts · hover for details
Corpus conservé : n=|||Saved corpus: n=
bilan descriptif, taux global inconnu|||descriptive summary, overall rate unknown
détails disponibles :|||details available:
vue sélectionnée : n=|||selected view: n=
Bilan|||Summary
Adversaires|||Opponents
Tours|||Turns
Actions|||Actions
Cartes jouées|||Cards played
Prises de Récompenses|||Prize-taking events
Dégâts consignés|||Recorded damage
Évolutions|||Evolutions
Attachements|||Attachments
Ordre du rapport · chronologie non attestée|||Report order · chronology not attested
Combats datés · plus récents en premier|||Dated games · most recent first
Dernier tour observé :|||Last observed turn:
Carte jouée|||Card played
K.O. observé|||Observed Knock Out
Récompense prise|||Prize taken
Aucun événement détaillé disponible dans ce rapport.|||No detailed events available in this report.
Traces disponibles seulement. Les intervalles et les informations cachées ne sont pas reconstruits.|||Available traces only. Gaps and hidden information are not reconstructed.
Rôle inconnu|||Unknown role
Tour inconnu|||Unknown turn
Tour ?|||Turn ?
Tour 13 et +|||Turn 13 and up
Tours 1–4|||Turns 1–4
Tours 5–8|||Turns 5–8
Tours 9–12|||Turns 9–12
Cause de la défaite inconnue.|||Cause of the loss unknown.
Frise des événements connus|||Known event timeline
deck exact adverse inconnu.|||exact opponent deck unknown.
Détail non disponible|||Detail unavailable
Toi|||You
Adversaire|||Opponent
Emblème PokeMind décoratif|||Decorative PokeMind emblem
Choisir le dossier de projet PokeMind|||Choose the PokeMind project folder
Ce dossier ne contient pas le projet PokeMind.|||This folder does not contain the PokeMind project.
Préférences ou données locales indisponibles. Aucun historique remplacé. Vérifier les fichiers de l’application dans data/local/chat.|||Preferences or local data unavailable. No history replaced. Check application files in data/local/chat.
Aucun rapport local valide disponible. Utilise Actualiser ou colle un journal complet; aucune partie inventée.|||No valid local report available. Use Refresh or paste a complete log; no games invented.
PokeMind · données locales|||PokeMind · local data
Corpus choisi; taux de victoire global inconnu. Les défaites orientent les priorités pédagogiques.|||Selected corpus; overall win rate unknown. Losses guide learning priorities.
Source : rapport canonique PokeMind|||Source: canonical PokeMind report
Learning Loop local.|||local Learning Loop.
Réponse locale : les statistiques ne sont pas envoyées au cloud avec ton réglage actuel.|||Local answer: statistics are not sent to the cloud with your current settings.
Pour que Codex ou Claude s’en servent, choisis « Ajouter statistiques… » dans Réglages.|||For Codex or Claude to use them, choose “Add statistics…” in Settings.
Partie sélectionnée : issue|||Selected game: outcome
version jouée|||played version
Cartes adverses observées :|||Observed opponent cards:
Reconstruction :|||Reconstruction:
Aucune liste exacte adverse prouvée.|||No exact opponent list proven.
RECONSTRUCTION / HYPOTHÈSE|||RECONSTRUCTION / HYPOTHESIS
légalité/Live inconnus|||legality/Live unknown
État non consulté|||Status not checked
Inconnu|||Unknown
Nom inconnu|||Unknown name
Taux global inconnu|||Overall rate unknown
rapport|||report
catalogue|||catalog
deck public|||public deck
méta|||meta
 · D=||| · L=
 V / ||| W /\u0020
 D, n=||| L, n=
événements|||events
Références|||References
Mémoire|||Memory
victoires; causalité non prouvée.|||wins; causality not proven.
défaites enregistrées · n=|||recorded losses · n=
préservés.|||preserved.
Source :|||Source:
Sources :|||Sources:
Adversaire :|||Opponent:
adversaire :|||opponent:
Reconstruction|||Reconstruction
Licence :|||License:
impression|||printing
variante|||variant
État|||Status
Partie|||Game
Prises|||Prize-taking events
Analyse mon dernier combat.|||Analyze my latest battle.
Reconstruis le deck de mon dernier adversaire.|||Reconstruct my latest opponent's deck.
Pourquoi je perds contre Dragapult?|||Why do I lose against Dragapult?
Quelles sont mes erreurs récurrentes?|||What are my recurring mistakes?
Compare mon deck aux meilleures listes actuelles.|||Compare my deck with the best current lists.
Propose trois modifications pour contrer ce deck.|||Suggest three changes to counter this deck.
Quel deck devrais-je jouer selon ma collection?|||Which deck should I play based on my collection?
Prépare-moi un deck 60/60 prêt à copier.|||Prepare a 60/60 deck ready to copy.
Entraîne-moi à gérer mon Banc et mes Énergies.|||Train me to manage my Bench and Energy.
Cherche les changements récents de la méta et mémorise-les.|||Find recent meta changes and remember them.
Confirmer?|||Confirm?
Test de traduction.|||Translation test.
Quelle est la prochaine amélioration utile de PokeMind?|||What is the next useful improvement to PokeMind?
Affiche mon statut Codex.|||Show my Codex status.
Cache local disponible|||Local cache available
Cache absent ou non accessible|||Cache missing or inaccessible
règles|||rules
hypothèse de famille|||family hypothesis
Référence personnelle|||Personal reference
Bibliothèque PUBLIC|||PUBLIC library
placements observés|||observed placements
Inconnus|||Unknown
Erreur|||Error
Interrompu|||Interrupted
Consultation de la mémoire publique locale|||Reading local public memory
Recherche publique bornée → validation → mémoire locale|||Bounded public research → validation → local memory
Tournois et pairings publics → instantané du cerveau existant|||Public tournaments and pairings → existing knowledge snapshot
Comparaison des observations aux variantes publiques60|||Comparing observations with public 60-card variants
Journal reconnu · validation locale réussie|||Log recognized · local validation passed
Doublon détecté · journal existant conservé|||Duplicate detected · existing log retained
Le contenu ne correspond pas à un journal texte.|||The content is not a text battle log.
Joueur ou participants non résolus, ou plusieurs parties concaténées.|||Player or participants unresolved, or multiple games concatenated.
Les deux participants et le joueur de référence doivent être reconnus.|||Both participants and the reference player must be recognized.
Aucun tour de jeu fiable reconnu.|||No reliable game turn recognized.
Résultat final absent ou contradictoire : aucune partie comptabilisée.|||Final result missing or contradictory: no game counted.
Deux participants distincts sont requis.|||Two distinct participants are required.
Identité de participant invalide.|||Invalid participant identity.
Le journal contient des identités ou résultats contradictoires.|||The log contains contradictory identities or results.
Analyse non terminée; fichier conservé, relancer Actualiser.|||Analysis incomplete; file retained, run Refresh again.
Partie historique reconnue; aucun rapport analytique disponible pour cette entrée.|||Historical game recognized; no analysis report available for this entry.
Résultat PokeMind — mémoire publique|||PokeMind result — public memory
Enregistrement local confirmé par le reçu du moteur.|||Local save confirmed by the engine receipt.
faits ajoutés|||facts added
révisés|||revised
déjà connus|||already known
non vérifiés|||unverified
Recherche partielle; les limites de collecte restent présentes.|||Partial research; collection limits still apply.
Aucune nouvelle écriture de faits pendant ce tour; consultation du cache local.|||No new facts written this turn; using the local cache.
Enregistrement local non confirmé; aucun compte d’écriture annoncé.|||Local save unconfirmed; no write count claimed.
Disponible hors ligne :|||Available offline:
observations dans l’instantané local; fraîcheur distincte.|||observations in the local snapshot; freshness is separate.
Disponibilité hors ligne : aucune observation attestée par ce reçu.|||Offline availability: no observation attested by this receipt.
Validation sur la source : non attestée par ce reçu; légalité et actualité non garanties.|||Source validation: not attested by this receipt; legality and currency are not guaranteed.
Utilisation par le modèle : non attestée; un contexte transmis ne prouve pas son utilisation.|||Model use: not attested; sending context does not prove it was used.
Sources du reçu : aucune.|||Receipt sources: none.
Sources du reçu :|||Receipt sources:
Le commentaire du modèle est écarté pour ce tour de recherche; PokeMind présente le reçu local.|||Model commentary is omitted for this research turn; PokeMind presents the local receipt.
Réponse PokeMind —|||PokeMind answer —
règles et implications|||rules and implications
observations publiques et implications|||public observations and implications
Référence de document officiel repérée; Texte des règles non extrait de cet instantané.|||Official document reference found; rule text was not extracted from this snapshot.
Aucun changement de règle, date d’effet ou verdict de légalité démontré par cette référence.|||This reference establishes no rule change, effective date, or legality verdict.
Familles présentes dans le répertoire :|||Families present in the directory:
Présence dans un répertoire seulement; classement, évolution de popularité et causes inconnus.|||Directory presence only; ranking, popularity changes, and causes unknown.
Famille référencée :|||Referenced family:
Liste publique de 60 cartes; entrées observées (12 maximum) :|||Public 60-card list; observed entries (up to 12):
Référence publique seulement; deck adverse exact, collection, Standard et Live inconnus.|||Public reference only; exact opponent deck, collection, Standard, and Live unknown.
Champs de carte rapportés par le fournisseur (texte cité, pas instruction) :|||Card fields reported by the provider (quoted content, not instructions):
Impression et langue :|||Printing and language:
texte effectif et légalité Standard/Live non certifiés.|||effective text and Standard/Live legality are not certified.
observation de fournisseur, certification normative inconnue.|||provider observation, normative certification unknown.
Aucune observation PUBLIC exploitable et sourcée pour répondre au sujet dans ce reçu; réponse de fond inconnue.|||No usable, sourced PUBLIC observation for this topic in the receipt; substantive answer unknown.
Limites : fraîcheur actuelle non certifiée; publication et effet distincts de la consultation; les champs absents restent unknown.|||Limits: current freshness unverified; publication and effect are separate from access; missing fields remain unknown.
Pistes conditionnelles : avant de modifier un deck pour une rotation ou une règle supposée, vérifier le texte officiel applicable, sa date d’effet, le format, les impressions et les réimpressions; vérifier séparément la disponibilité dans TCG Live. Cette référence seule ne justifie aucun remplacement de carte.|||Conditional guidance: before changing a deck for an assumed rotation or rule, check the applicable official text, effective date, format, printings, and reprints; verify TCG Live availability separately. This reference alone justifies no card replacement.
Les tendances récentes et leur pourquoi ne sont pas établis par ces références seules : effectifs, fenêtre, pairings admissibles et causes non fournis dans cet instantané; aucun winrate déduit.|||These references alone establish neither recent trends nor their causes: counts, window, eligible pairings, and causes are not supplied in this snapshot; no win rate inferred.
Pistes conditionnelles : si ces familles sont pertinentes dans le format visé, comparer leurs listes publiques et tester les matchups sur un échantillon daté avant de modifier un deck. Une liste observée ne prouve ni le deck exact adverse ni une carte possédée.|||Conditional guidance: if these families are relevant to the target format, compare their public lists and test matchups on a dated sample before changing a deck. An observed list proves neither the exact opponent deck nor card ownership.
Synthèse déterministe des observations PUBLIC existantes; aucune prose du modèle utilisée comme preuve.|||Deterministic summary of existing PUBLIC observations; no model prose used as evidence.
Données descriptives :|||Descriptive data:
en ligne :|||online:
consultation de la projection :|||projection accessed:
Fenêtre|||Window
tournois admissibles;|||eligible tournaments;
placements classifiés;|||classified placements;
matchs admissibles classifiables.|||classifiable eligible matches.
tournoi :|||tournament:
consultée :|||accessed:
Variation descriptive dans cet échantillon, archétype|||Descriptive change in this sample, archetype
points de pourcentage.|||percentage points.
Échantillon temporel/classifié insuffisant : aucune tendance calculée; minimum par fenêtre : 2 tournois, 10 placements classifiés, 80 % de classification, 5 matchs classifiables.|||Insufficient dated/classified sample: no trend calculated; minimum per window: 2 tournaments, 10 classified placements, 80% classification, 5 classifiable matches.
Définition : identifiant d’archétype publié par le fournisseur, stabilité non vérifiée; un placement publié, pas un joueur unique. Matchs publiés, pas parties individuelles; aucun winrate calculé.|||Definition: provider-published archetype identifier, stability unverified; a published placement, not a unique player. Published matches, not individual games; no win rate calculated.
Limites : sélection de tournois, top cuts, absences et classification; représentativité mondiale inconnue; seuils descriptifs, aucune significativité revendiquée; causalité : unknown.|||Limits: tournament selection, top cuts, missing entries, and classification; global representativeness unknown; descriptive thresholds, no significance claimed; causality: unknown.
Hypothèse de conseil : tester les familles observées dans le format visé; aucune amélioration causale démontrée.|||Advice hypothesis: test the observed families in the target format; no causal improvement demonstrated.
Dossier de données :|||Data folder:
Hors du projet; l’original reste dans le projet tant que tu ne le supprimes pas toi-même.|||Outside the project; the original stays in the project until you delete it yourself.
Dans le dossier du projet (un nettoyage Git ou un agent peut l’effacer).|||Inside the project folder (a Git clean-up or an agent can erase it).
Revenir au dossier du projet|||Go back to the project folder
Sortir mes données du projet…|||Move my data out of the project…
Au prochain démarrage, PokeMind reprendra les données du dossier du projet. Ce qui a été ajouté depuis la copie (combats, decks, discussions) reste dans la copie et n’y sera pas. Continuer?|||At the next start, PokeMind will use the data in the project folder again. Anything added since the copy (battles, decks, conversations) stays in the copy and will not be there. Continue?
Ferme et rouvre PokeMind : le changement de dossier de données se fera au démarrage.|||Close and reopen PokeMind: the data folder changes at startup.
Sortir tes données du projet|||Move your data out of the project
Tes données PokeMind (combats, decks, discussions, mémoire) sont encore dans le dossier du projet, où un nettoyage Git ou un agent pourrait les effacer. PokeMind peut les copier dans :|||Your PokeMind data (battles, decks, conversations, memory) is still in the project folder, where a Git clean-up or an agent could erase it. PokeMind can copy it to:
fichiers, chacun vérifié).|||files, each one verified).
L’original reste intact dans le projet. Copier maintenant et utiliser la copie?|||The original stays untouched in the project. Copy now and use the copy?
Copie vérifiée de tes données…|||Verified copy of your data…
Copie interrompue :|||Copy interrupted:
Rien n’a été remplacé; PokeMind continue avec le dossier du projet et te reproposera la copie.|||Nothing was replaced; PokeMind keeps using the project folder and will offer the copy again.
Copie vérifiée :|||Verified copy:
fichiers. PokeMind utilise maintenant :|||files. PokeMind now uses:
L’original reste dans le projet. Vérifie tes combats, decks et discussions; en cas de problème : Réglages → « Revenir au dossier du projet ».|||The original stays in the project. Check your battles, decks and conversations; if something is wrong: Settings → “Go back to the project folder”.
Le dossier de données copié est introuvable. PokeMind utilise le dossier du projet; Réglages permet de refaire la copie.|||The copied data folder cannot be found. PokeMind is using the project folder; Settings lets you copy again.
Le chat travaille dans le dossier PokeMind, comme Codex ou Claude Code dans un terminal : règles du dossier (AGENTS.md, CLAUDE.md), fichiers et commandes selon le mode ci-dessous, outils du coach, sessions gardées avec celles du dossier. Un journal collé reste confié au coach isolé, sans shell.|||The chat works in the PokeMind folder, like Codex or Claude Code in a terminal: the folder's rules (AGENTS.md, CLAUDE.md), files and commands per the mode below, coach tools, sessions kept with the folder's. A pasted log stays with the isolated coach, without a shell.
Agrandir la discussion dans une grande fenêtre|||Open the conversation in a large window
Ramener|||Dock
Remettre la discussion à droite|||Put the conversation back on the right
Écris ta question ou colle ton journal TCG Live…|||Type your question or paste your TCG Live log…
Entrée pour envoyer · Maj+Entrée pour une nouvelle ligne|||Enter to send · Shift+Enter for a new line
Accès complet · données privées accessibles|||Full access · private data reachable
Standard · données privées accessibles|||Standard · private data reachable
Le coach répond encore; ton message reste prêt ici.|||The coach is still answering; your message stays ready here.
Actualiser mes combats au démarrage|||Refresh my battles at startup
Afficher les illustrations publiques TCGdex|||Show public TCGdex artwork
Bibliothèque locale|||Local library
Ce que Codex et Claude peuvent faire|||What Codex and Claude may do
Ce que le coach reçoit|||What the coach receives
Coach IA|||AI coach
Codex et Claude sont en ligne; Ollama reste sur ce PC.|||Codex and Claude are online; Ollama stays on this PC.
Comme Claude Code ou Codex dans un terminal.|||Like Claude Code or Codex in a terminal.
Diagnostic|||Diagnostics
Données|||Data
Dossier de données|||Data folder
Dossier de travail|||Working folder
En plus de ta question|||Besides your question
Français ou anglais|||French or English
Général|||General
Images gardées en cache sur ce PC|||Images kept in a cache on this PC
Le chat travaille dans le dossier PokeMind|||The chat works in the PokeMind folder
Les nouvelles parties sont analysées à l’ouverture|||New games are analysed when PokeMind opens
Masquer les détails|||Hide details
Moteur du chat|||Chat engine
Mémoire locale · conseils sourcés|||Local memory · sourced advice
Pages affichées instantanément|||Pages appear instantly
Pendant que PokeMind est ouvert|||While PokeMind is open
Plus mes statistiques anonymisées|||Plus my anonymised statistics
Rapport technique sans données privées|||Technical report without private data
Relatif au dossier PokeMind|||Relative to the PokeMind folder
Réduire les animations|||Reduce motion
Révoquer les consentements|||Revoke consents
Sombre ou clair|||Dark or light
Surveiller les nouveaux journaux|||Watch for new logs
Sécurité|||Security
Tes préférences, enregistrées sur ce PC.|||Your preferences, saved on this PC.
Teste la connexion au moteur choisi|||Tests the connection to the chosen engine
Thème|||Theme
Ton compagnon TCG|||Your TCG companion
Un shell peut lire tes données privées.|||A shell can read your private data.
V1 · audit requis|||V1 · audit required
Voir les détails|||Show details
Vérifier|||Check
À propos|||About
Connaissances publiques|||Public knowledge
+ mes statistiques anonymes|||+ my anonymous statistics
Accès complet (--yolo)|||Full access (--yolo)
Tes adversaires, classés par défaites. Clique sur un adversaire pour revoir tes parties.|||Your opponents, ranked by losses. Click an opponent to review your games.
Parties|||Games
Adversaire le plus coriace|||Toughest opponent
Barre : victoires en bleu, défaites en rouge, issues inconnues en jaune|||Bar: wins in blue, losses in red, unknown results in yellow
Parties contre cet adversaire|||Games against this opponent
Choisis un adversaire dans la liste, puis une partie : sa frise apparaîtra ici.|||Pick an opponent in the list, then a game: its timeline will show here.
Ce que PokeMind retient de tes parties, et quoi tester ensuite.|||What PokeMind remembers from your games, and what to test next.
Parties observées|||Observed games
Adversaires suivis|||Tracked opponents
Plans à tester|||Plans to test
Mise à jour|||Updated
<h3>Tes bilans par adversaire</h3>|||<h3>Your record by opponent</h3>
Bleu : victoires · rouge : défaites · jaune : issues inconnues. Bilan descriptif; aucune causalité.|||Blue: wins · red: losses · yellow: unknown results. Descriptive record; no causality.
<h3>À tester ensuite</h3>|||<h3>To test next</h3>
<b>Contre |||<b>Against\u0020
Défaites : |||Losses:\u0020
<br>➜ Base à tester : <b>|||<br>➜ Base to test: <b>
<a href="pokemind://page/2">ouvrir dans Deck Lab</a>|||<a href="pokemind://page/2">open in Deck Lab</a>
<h3>Historique des révisions</h3>|||<h3>Revision history</h3>
 · version précédente conservée||| · previous version kept
Aucune observation enregistrée pour l’instant.|||No observation recorded yet.
<p>Aucune observation enregistrée pour l’instant.</p>|||<p>No observation recorded yet.</p>
Observations|||Observations
Bilans par adversaire|||Records by opponent
Feuillette le classeur ou cherche une carte; tout reste hors ligne.|||Leaf through the binder or search for a card; everything stays offline.
Tout le classeur|||Whole binder
Revenir à toutes les cartes, de la plus récente extension à la plus ancienne|||Back to every card, from the newest set to the oldest
Fermer la fiche|||Close the card sheet
Résultats : |||Results:\u0020
Recherche locale terminée · |||Local search done ·\u0020
Classeur|||Binder
Page précédente|||Previous page
Page suivante|||Next page
Pochette vide|||Empty sleeve
Couverture du classeur|||Binder cover
Catalogue local absent : synchronise d’abord le catalogue public.|||Local catalogue missing: sync the public catalogue first.
Codex, Claude Code ou PowerShell, dans le dossier PokeMind.|||Codex, Claude Code or PowerShell, in the PokeMind folder.
Accès complet · Ctrl+V colle · Ctrl+C copie|||Full access · Ctrl+V pastes · Ctrl+C copies
Ton compte OpenAI, en ligne|||Your OpenAI account, online
Ton compte Anthropic, en ligne|||Your Anthropic account, online
Un modèle local, rien ne quitte ton PC|||A local model, nothing leaves your PC
Bienvenue dans PokeMind|||Welcome to PokeMind
Retour|||Back
Suivant|||Next
Commencer|||Start
Ton compagnon Pokémon TCG Live : tes combats, tes decks et tes cartes restent sur ton PC.|||Your Pokémon TCG Live companion: your battles, decks and cards stay on your PC.
Ton coach|||Your coach
PokeMind parle avec un moteur que tu as déjà. Tu pourras changer plus tard.|||PokeMind talks to an engine you already have. You can change it later.
installé|||installed
non trouvé sur ce PC|||not found on this PC
Les journaux bruts, identités et chemins ne sont jamais envoyés automatiquement.|||Raw logs, identities and paths are never sent automatically.
Tes combats|||Your battles
Colle un journal TCG Live dans le chat, ou dépose un fichier .txt / .log.|||Paste a TCG Live log in the chat, or drop a .txt / .log file.
Surveiller les nouveaux journaux pendant que PokeMind est ouvert|||Watch for new logs while PokeMind is open
Pour l’entraînement et la révision après la partie : pas pendant un tournoi officiel.|||For practice and post-game review: not during an official tournament.
Tout est prêt|||All set
Tu peux tout changer dans Réglages.|||You can change everything in Settings.
oui|||yes
non|||no
Coach : |||Coach: 
Envoi au cloud : |||Cloud sending: 
Surveiller les journaux : |||Watch logs: 
Illustrations TCGdex : |||TCGdex artwork: 
Le dossier de données PokeMind est inaccessible.|||The PokeMind data folder cannot be reached.
Télécharger le catalogue des cartes FR/EN (environ 25 Mo, TCGdex)|||Download the FR/EN card catalogue (about 25 MB, TCGdex)
Catalogue des cartes : |||Card catalogue:\u0020
téléchargé à l’ouverture|||downloaded when PokeMind opens
Télécharger le catalogue (environ 25 Mo)|||Download the catalogue (about 25 MB)
Sur ce PC, dans le dossier de l’application.|||On this PC, in the app’s folder.
Télécharger|||Download
Une archive publique TCGdex (GitHub), importée sur ce PC; rien de personnel n’est envoyé.|||A public TCGdex archive (GitHub), imported on this PC; nothing personal is sent.
Catalogue de cartes|||Card catalogue
Catalogue local illisible · |||Local catalogue unreadable ·\u0020
Les cartes ne sont pas encore sur ce PC. Le catalogue public FR/EN (TCGdex) se télécharge une fois, puis tout fonctionne hors ligne.|||Cards are not on this PC yet. The public FR/EN catalogue (TCGdex) downloads once, then everything works offline.
Sur ce PC, hors ligne (TCGdex, FR/EN).|||On this PC, offline (TCGdex, FR/EN).
Pas encore sur ce PC : environ 25 Mo depuis GitHub (TCGdex), 175 Mo sur le disque.|||Not on this PC yet: about 25 MB from GitHub (TCGdex), 175 MB on disk.
Téléchargement du catalogue de cartes… |||Downloading the card catalogue…\u0020
Import du catalogue sur ce PC (environ une minute)…|||Importing the catalogue on this PC (about a minute)…
Catalogue de cartes prêt|||Card catalogue ready
Téléchargement du catalogue interrompu · |||Catalogue download stopped ·\u0020
. Rien n’a été remplacé; réessaie plus tard.|||. Nothing was replaced; try again later.
Code sous licence MIT · cartes : TCGdex (MIT) · projet de fans non officiel|||MIT-licensed code · cards: TCGdex (MIT) · unofficial fan project
Coach|||Coach
Recherche web|||Web research
Développement|||Development
Mode du message|||Message mode
Coach : ta mémoire locale et le catalogue, sans Internet.|||Coach: your local memory and the catalogue, no Internet.
Recherche web : collecte publique bornée avant la réponse, pour ce message seulement.|||Web research: a bounded public collection before the answer, for this message only.
Développement : Codex ou Claude travaillent sur le code de PokeMind.|||Development: Codex or Claude work on the PokeMind code.
'''

CATALOG = {}
for _line in _PAIRS.strip().splitlines():
    _fr, _en = _line.split('|||', 1)
    CATALOG[_fr.replace(r'\n', '\n')] = _en.replace(r'\n', '\n').replace(r'\u0020', ' ')

_pattern = re.compile('|'.join((r'(?<!\w)' if key[0].isalnum() else '') + re.escape(key) +
    (r'(?!\w)' if key[-1].isalnum() else '') for key in sorted(CATALOG, key=len, reverse=True)))


def english(source):
    return _pattern.sub(lambda match: CATALOG[match.group()], source)
