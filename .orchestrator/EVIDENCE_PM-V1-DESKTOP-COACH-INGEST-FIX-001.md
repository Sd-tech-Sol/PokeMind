# PM-V1-DESKTOP-COACH-INGEST-FIX-001 — preuves du correctif

2026-10-26 — **CODEX_LOCAL_REPORTED**. Les observations du PC restent distinctes
de la CI et de l'audit indépendant. V1 **NOT_RELEASE_READY**.

Prévol : branche autorisée propre, fetch + pull ff-only sans perte à
`acca11f09b738f37422b182751d2a79a8c1d37c0`;
[CI initiale40273276920](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40273276920)
success au SHA exact, Windows1353/2 et Ubuntu1352/3. Prévol local RUNTIME_READY,
sans DB personnelle implicite. Nouvel ordre propriétaire documenté dans le
[mandat](MANDATES/PM-V1-DESKTOP-COACH-INGEST-FIX-001.md), sans relancer l'ancien STOP.

## Implémentation

Le service réutilise rapports canoniques, parseur, déduplication, `battle_coach`,
Learning Loop, SQLite/public caches et versions de decks existants. Les chiffres
personnels et sources locales sont prioritaires et préservés sous la limite24Ko;
la méta complète ces données. Préférences cloud conservées; réponse locale avec
les vrais chiffres si le partage personnel est désactivé, pas de question répétée.
Un index privé de correspondance ouvre la partie sans exposer ses empreintes.

Collage/attachement/drop : routage avant tout fournisseur, validation du joueur,
participants/tours/résultat, publication atomique exclusive, noms générés,
doublons historiques et traitement local jusqu'à2Mo. Texte brut absent de
l'historique fournisseur; notifications locales filtrées et anciens fils contenant
un journal isolés sans effacer l'historique. Confirmation/résultat/adversaire,
nouveaux uniques/statistiques et bouton d'analyse branchés sur les résultats réels.
L'actualisation du corpus GUI refuse les parties incomplètes. Aucun deck joué
ou lien d'attestation n'est deviné.

Activité animée et temps réel, étapes de consultation/attente/génération/fin,
Enter/Shift+Enter/Stop. Démarrage en arrière-plan optionnel et surveillance
optionnelle seulement pendant l'ouverture (poll5s, stabilité minimale10s).
Index de fraîcheur lié au contenu et au snapshot validé : pas de retraitement
complet quand rien n'a changé. Il ne contient aucune statistique concurrente.

Graphiques du corpus, priorités pédagogiques distinctes, galerie groupée60/60,
liste conservée, images/agrandissement, sources et cache personnel local. HTTPS
TCGdex uniquement pour métadonnées/illustrations publiques, budgets/taille et
dimensions bornés, refus source sans retry automatique, repli propre. Les données
du dépôt MIT ne donnent pas une licence présumée des illustrations; droits et
usage personnel local affichés, aucune illustration du cache redistribuée.
[Guide](../docs/DESKTOP_GUI_CHAT_GUIDE.md), [avis](../docs/DESKTOP_THIRD_PARTY_NOTICES.md).

## QA Windows native

`scripts/qa_desktop_ingestion.py --real-windows --owner-codex` exercé dans de
vraies fenêtres Qt sur Windows, sans plateforme offscreen pour ces essais.

| Parcours | Résultat rapporté et portée |
|---|---|
| Collage + Enter, enregistrement et confirmation | Réussi; vrai pipeline sur corpus inventé isolé |
| Doublon exact/sémantique, aucun incrément | Réussi; fichiers/rapports historiques consultés |
| Journal incomplet et collage ambigu | Refus explicite, zéro partie ajoutée, aucun fournisseur |
| Journal volumineux au-delà du flux de question ordinaire | Réussi localement |
| Pièce jointe/drop MIME Qt .log | Fichier conservé, import et compteurs réels réussis |
| Bouton vers chronologie de la partie | Réussi, y compris famille inconnue |
| Réouverture avec option de démarrage | Nouvelle partie réellement traitée, comptes actualisés |
| Question personnelle à Codex réellement connecté | Chiffres du vrai rapport propriétaire retrouvés, source/date/limite |
| Collage d'un doublon propriétaire réel | Aucun appel IA supplémentaire; corpus et fichiers bruts préservés |
| Streaming, attente animée/temps et interruption Codex | Réussis avec le vrai fournisseur |
| Shift+Enter et Enter | Exercés dans la fenêtre native et par régressions |
| Galerie60, vraies illustrations et agrandissement | Réussis sur données conservées et source TCGdex |
| Préférences cloud propriétaire après QA | Restaurées, comparaison égale |

Les nouvelles parties de test sont **inventées et isolées du corpus propriétaire**;
elles proviennent du vrai parseur et du vrai moteur, jamais de compteurs injectés.
Le rapport propriétaire et la réponse Codex sont réels. Seuls des agrégats anonymisés
bornés ont été transmis pour cette question expressément autorisée; aucun journal,
pseudo, chemin ou empreinte personnelle. Captures, réponses et traces restent dans
`data/local/desktop-dev`, fichiers de test dans `data/local/test-runs`; rien de ces
données dans GitHub. Ces tests ne constituent pas un audit indépendant du PC.

## Régressions et portable

**230 tests ciblés réussis,50 nouveaux et180 hérités**, neuf modules explicites :
desktop ingestion/workflow Qt/images/services/Qt existant, providers, battle batch,
battle coach et legacy bridge. Fixtures inventées, Qt offscreen pour ces régressions,
pipes/HTTP inventés pour les fournisseurs. Couverture : validation/refus, doublons
historique/normalisation, écriture atomique interrompue/concurrente, identité,
schéma7 inchangé octet pour octet sur fixture, cache de fraîcheur invalidé par un
contenu modifié, contexte prioritaire borné et matchup spécifique, vie privée de
l'historique, raccourcis/activité/arrêt, démarrage/watch temporisé, galerie/images,
provenance/cache altéré/refus source et aperçu sûr du Markdown sans images distantes.

PySide6 6.12.0 Windows, PyInstaller6.22.3, Codex0.163.0, Claude2.1.310; dépendances Windows inchangées,
venv du projet uniquement. Ollama reste une dépendance externe absente sur ce PC;
adaptateur HTTP loopback testé sur serveur inventé, aucun modèle téléchargé.
Compilation/tabnanny/hygiène/diff et portable Windows reproduit. Programme frozen
ouvert visiblement sur Windows, sortie0; rapport, référence60, six pages, galerie,
contrôles import/activité/option démarrage présents. Dernière suite ciblée :230/230.

### Correctif de fermeture après la première CI

Le [run40405113842](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40405113842)
au SHA `ec1fd2015b82688cf2aecb6a2428fecd7d38c10a` a terminé les1402 tests Ubuntu
(3 ignorés), puis échoué134 pendant la finalisation Python : `bool_dealloc`,
ramasse-miettes d'une extension native. Ce n'est pas une CI verte. Le job Windows de ce même run est réussi :1403/2.
Les fixtures fermaient les fenêtres sans détruire explicitement leurs objets Qt;
`processEvents` seul ne traite pas les suppressions différées sans boucle `exec`.
Correction : attendre les deux pools et leurs retours, détruire explicitement la
fenêtre pendant que Qt/Python sont actifs, drainer DeferredDelete et contrôler
l'invalidation native. La fixture attend aussi tous les chargements initiaux
avant injection d'une galerie, évitant un résultat initial encore en file. Ce
retard a été révélé par une vérification additionnelle en Python3.11 isolé sur
Windows;26 parcours Qt y passent après correction. Aucun test désactivé.
Fermeture produit : arrêter les trois timers avant sortie.
L'origine précise du défaut de références de l'extension demeure une hypothèse;
la nouvelle CI complète doit confirmer que ce nettoyage résout l'échec, sans
ignorer des tests ni contourner le code de sortie.
[Contrat Qt de suppression différée](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#PySide6.QtCore.QObject.deleteLater).

Le [run40406485950](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40406485950)
au SHA `3d2760612b71028c9824d2cb141ad210f86d7e55` reproduit le plantage Ubuntu
après1402/3; Windows1403/2 réussi. Le nettoyage des fenêtres ne suffit donc pas.
La fixture détruit aussi explicitement le singleton QApplication via `shutdown`
à la fin de chaque module Qt, vérifie `instance() is None` et collecte les cycles
pendant que Python est actif. Les modules suivants recréent leur propre app.
Ce cycle est exercé en Python3.11 Windows; aucun test ignoré, aucun changement
pour contourner un code de sortie, aucun assouplissement de la CI.
[API Qt/Python](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QCoreApplication.html).

Le [run40407373649](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40407373649)
au SHA `aa29fa1dfd9b17fc1383b88e5cc1af7cd03b8aa9` reproduit encore le défaut
Ubuntu après1402/3. La destruction explicite de QApplication ne suffit pas non
plus; aucune cause précise de corruption native n'est déclarée démontrée.
La CI lance désormais les26 tests Qt et le reste exhaustif dans **deux processus
Python distincts** par OS. Les deux modules Qt sont explicitement inclus dans le
premier et exclus uniquement du second : aucun test omis ou doublé. Chaque code
de sortie doit réussir; un abort natif reste un échec bloquant. Les deux JUnit
sont additionnés par le même publieur, sans altérer les huit reproductions.
Cette isolation évite le partage de l'état des extensions Qt avec tout le reste
de la suite, et fournit un diagnostic Qt court si le défaut subsiste.
**67 tests du publieur réussis, dont3 nouveaux** : somme de rapports indépendants
et refus de publier si le rapport Qt contient erreurs ou échecs. S'ajoutent aux
230 ciblés (50 nouveaux), soit297 vérifications ciblées distinctes et53 nouveaux.
Aucune nouvelle dépendance, aucun assouplissement des codes de sortie.

Le [run40408402330](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40408402330)
au SHA `db8e2885f96532d32b96c8b2791eb116cc48b196` isole le défaut au processus
Qt Ubuntu :26/26 passent puis bool_dealloc/134 à la finalisation. Le moteur n'est
pas exécuté après cet échec. Le découpage ne masque donc pas l'abort.
L'extra desktop est désormais épinglé à **PySide6 6.11.2 sur Linux** pour qualification;
Windows conserve6.12.0 (portable et QA réelle inchangés). La version corrective
précédente est une mesure de compatibilité bornée, pas une prétendue correction
amont démontrée : tous les tests Qt et cœur, ainsi que la terminaison des deux
processus, doivent réussir avec cette dépendance déclarée. Aucun Python minimum
relevé pour masquer les références booléennes, aucun exit forcé ou test ignoré.
[Distribution officielle Qt](https://download.qt.io/official_releases/QtForPython/pyside6/),
[PySide6 6.11.2](https://pypi.org/project/PySide6/6.11.2/).

**CI finale : après push, l'exécuteur doit vérifier le HEAD distant, le SHA du run,
les deux jobs complets, les neuf marqueurs SHA/run et les deux registres canoniques
concordants avant sa réponse finale.** Le run Actions associé au dernier commit
livré est la preuve publique durable; la CI ne certifie pas les observations PC.

Aucune migration7→13, sauvegarde, restauration, suppression utilisateur,
installation globale/admin, automatisation du client du jeu, scheduler ou watcher
GitHub. Seuls les artefacts de build ont été régénérés. Rapports précédents et
journaux conservés. Fin demandée **AWAITING_AUDIT**, aucun auto-VERIFIED.
