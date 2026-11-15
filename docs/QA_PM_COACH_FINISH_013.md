# Coach / classement public / chat — contrat et QA 013

Mandat `PM-V1-COACH-AUTO-OPPONENT-RANKING-CHAT-FINISH-013`, base privée `9d5d3bc`.
Toutes les parties, listes, joueurs et images de cette QA sont inventés. Aucun essai sur
l’installation du propriétaire; aucun paquet EXE/Setup produit. Résultats finaux :
[RESULT](../.orchestrator/RESULT.md). Ces vérifications d’exécution ne remplacent pas l’audit ChatGPT.

## Reconstruction locale conditionnelle

L’importeur appelle `Services.save_public_opponent` uniquement après publication et analyse réussies
d’un nouveau match unique. Doublon, refus, analyse partielle et annulation ne déclenchent aucun ajout.
Une demande explicite visant le deck adverse d’une partie sélectionnée appelle le même moteur dans
un worker, même sans fournisseur IA ou consentement cloud. « Crée un deck pour battre cet adversaire »
reste une demande de construction, distincte du rattrapage. Aucun balayage historique au démarrage.

Seuil `public-opponent-013-v1`, déterministe, sans probabilité de certitude :

- Défaite attestée, ou victoire avec totaux explicitement observés de **6 Récompenses prises contre 5**.
  Totaux absents/partiels, issue inconnue et victoire non serrée : refus.
- Au moins **4 tours observés**, **6 noms distincts**, **8 mentions visibles**, **2 noms de Pokémon
  canoniques** identifiables dans l’index public, dont une signature primaire de la famille retenue.
- Référence de **60 cartes** contrôlée par la bibliothèque publique existante; source HTTPS Limitless,
  date d’échantillon ou de consultation publique dans les **28 derniers jours**, sans date future.
- Recouvrement par nom d’au moins **80 %**; tous les Pokémon identifiables dans l’index doivent être
  présents. Aucun minimum observé supérieur au nombre d’exemplaires de la référence.
- La meilleure composition doit dépasser **chaque autre composition d’au moins deux noms observés**.
  Égalités/variantes proches : `AMBIGUOUS_PUBLIC_REFERENCE`. Aucune référence datée vérifiable :
  `PUBLIC_REFERENCE_UNAVAILABLE`; sinon preuve trop faible : `INSUFFICIENT_EVIDENCE`.

Une impression différente ne supprime pas un nom corroboré; `printing_equivalence_unproven` reste
explicite. Les noms observés absents de la référence sont conservés séparément. La liste publique de
60 est une **hypothèse comparable**, jamais le deck exact, une preuve de possession ou de légalité.
Le cas à **17 noms observés** est testé; les cartes non vues et leurs quantités restent supposées.

Déduplication : composition normalisée (sections, noms, codes/numéros, quantités; ordre/espaces/casse
ignorés), puis famille canonique corroborée par les Pokémon. Les anciens fichiers propriétaire/coach
participent à cette vérification, ainsi que les références SQLite enregistrées; aucun n’est renommé
ou remplacé. Inventaire JSON dépassant 500 entrées ou lecteur legacy atteignant sa limite de 100
versions : refus conservateur, aucune déduplication supposée complète. L’ajout utilise les JSON `my-decks`
existants : verrou partagé aux ajouts manuels, staging complet avec fsync, publication atomique
exclusive par lien, retrait du seul alias de staging possédé. Une collision conserve la cible.
Métadonnées locales : origine automatique, famille, source/date publiques, seuil, noms observés et
écarts d’impression; aucun identifiant joueur/match ou journal brut. Le reçu UI n’affirme un ajout
qu’après succès. Le LLM conserve son refus `DECK_SAVE_REQUIRES_OWNER_REQUEST` sur un import non sollicité.

Le moteur ne fait aucun GET. Sans référence disponible il saute cette partie. L’actualisation normale
des statistiques peut enrichir les seules données publiques; elle ne rattrape aucun ancien match.

## Sélecteur Deck Lab

`deck_public_stats.public_view` reste la source des chiffres. Le batch partage son échantillon et ses
requêtes par archétype; il mémorise les listes de Pokémon identiques pendant ce chargement seulement.
Classement décroissant **BO1 PTCGL Standard**, fenêtre de **28 jours**, **n ≥ 20**. Taux d’archétype,
pas taux de la liste exacte ni du propriétaire. BO3 reste dans l’onglet Statistiques, jamais comparé
à BO1. Identité ambiguë, cache absent/invalide/périmé et snapshot contenant un événement futur : aucun %.
Les égalités et inconnus gardent leur ordre initial stable; les inconnus suivent les taux comparables.

Chaque entrée garde son nom complet, taux/n/mode/période/source quand disponibles, infobulle bilingue
avec URL et date de consultation et texte accessible. Le sélecteur fermé conserve son élision native.
La sélection et la comparaison utilisent `favorite_key`; un relabel ne recharge pas la galerie.
Favori, deck principal, focus clavier, scroll et réponses tardives sont testés. Le collecteur existant
reste partagé : une tentative automatique/jour, deux manuelles au maximum, intervalle de dix minutes;
aucune requête contenant une liste ou un nom privé, aucune tentative par deck ni boucle de refus.

Mesure exploratoire locale sur un tournoi artificiel, sans catalogue de cartes complet (un passage,
pas un benchmark produit) :

| Nombre de decks | Même liste de Pokémon | Listes de Pokémon distinctes |
|---|---:|---:|
| 5 | 47,9 ms | 34,1 ms |
| 50 | 33,7 ms | 82,4 ms |
| 500 | 65,8 ms | 533,4 ms |

Les tests vérifient indépendamment une lecture d’échantillon par batch et une résolution par liste de
Pokémon distincte. Tout ce calcul s’exécute dans le worker, pas dans le thread Qt.

## Chat natif et preuves

`RoundedTranscript` conserve le QTextBrowser et son document, ses liens sûrs et la sélection native.
QPainter dessine les fonds avec un rayon **12 px** à partir des cadres de messages transparents;
aucun `border-radius` HTML supposé fonctionner. Fond utilisateur `alternate`, réponse `surface`, texte
`text`, accent doré conservé. Activité `surface`, compteur discret `alternate/muted`, spinner et durée
toujours visibles. API Qt utilisée : [QAbstractTextDocumentLayout](https://doc.qt.io/qt-6/qabstracttextdocumentlayout.html).
Contrastes calculés avec le helper existant, sombre/clair respectivement : texte utilisateur
11,38 / 14,88; texte réponse 14,12 / 17,10; compteur 8,19 / 6,38; titre réponse 10,47 / 9,38.
Ces huit paires précises ne constituent pas un nouvel audit de toutes les couleurs de l’application.

Pendant le streaming, le texte échappé est ajouté par lots de 40 ms au dernier message, sans reparcourir
les anciens messages ni conserver chaque préfixe croissant en cache. Markdown, tableaux, regroupement
des outils et sources sont mis en forme à la fin du tour; les marqueurs Markdown peuvent donc être
visibles pendant la génération. Les tests vérifient 110 deltas, deux tours conservés, aucune nouvelle
analyse Markdown durant les ajouts, puis une seule à la fin. Sélection/MIME de copie, clic réel HTTPS,
XSS affiché comme texte, thèmes, langue, dock étroit et fenêtre flottante sont exercés.

Les captures proviennent de `MainWindow.grab()` et `chat_dock.grab()` sur fixtures synthétiques,
jamais du bureau personnel. Les assertions échantillonnent les pixels des coins et des fonds des
deux rôles; les captures de livraison doivent provenir du backend Windows natif, avec glyphes lisibles.
Les PNG offscreen servent aux tests automatiques et ne prouvent pas le rendu typographique Windows.

Captures natives FR, thèmes sombre/clair, 1500 px à 100 % et 1100 px à 125 %, dock 355 px et flottant :
[fenêtre sombre](qa/coach-013/mainwindow-dark-1500-100.png),
[fenêtre claire](qa/coach-013/mainwindow-light-1100-125.png),
[chat sombre](qa/coach-013/chat-dark-docked-100.png),
[chat clair flottant](qa/coach-013/chat-light-floating-125.png),
[sélecteur 1100](qa/coach-013/selector-1100-125.png),
[sélecteur 1500](qa/coach-013/selector-1500-100.png).
Les valeurs 62,5 % / n=40 et 14 s de ces vues sont des **fixtures de présentation inventées**.
Les chiffres du moteur sont vérifiés séparément avec l’oracle de pairings artificiels.
Pour ces PNG, un délai de 300 ms avant `MainWindow.grab()` laisse finir la transition Qt et la mise
en page; aucun pixel ni contenu de capture n’est retouché. Les essais natifs de la matrice comptent
28 réussites à chaque facteur, puis 6 captures stabilisées à chaque facteur, sans échec final.

## Rejouer

Depuis le dépôt, **uniquement** `python scripts/local_gate.py --keep` pour la preuve complète.
Le lanceur copie les fichiers de code sans `data/local`, compile, vérifie l’hygiène et lance Qt et cœur
sur données artificielles. Les essais natifs complémentaires se font dans cette copie, avec
`POKEMIND_TEST_OFFLINE=1`, `QT_QPA_PLATFORM=windows`, facteurs Qt 1 puis 1.25 :
`python -m pytest tests/test_desktop_qt.py tests/test_desktop_workflow_qt.py -k "013 or deck_controls"`.
Ne jamais exécuter pytest dans le dépôt contenant les données réelles.
