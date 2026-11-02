# PM-V1-POKEDEX-EXPERIENCE-STATS-001 — preuves assainies

GO le 2026-10-27, finalisation le **2026-10-28 Québec**. **CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT**. Demande des cinq améliorations proposées et de davantage de graphiques statistiques. Nouveau mandat; aucune opération consommée réexécutée, aucune réception personnelle présumée. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.

## Source et périmètre livré

Base synchronisée : **`9e0435bff4abda5597ec2233f7458ce30838c175`**. Implémentation principale : `ad064dcd62dfaf6ec852e90862353993d12bbd1c`. Source finale compilée : **`e8f9849c5fad71d1de70e30dadccf78d54d91ef7`**, branche `work/pm-v1-lotj-final-readiness-windows`. Seul ajustement supplémentaire : libellé Joindre/Attach raccourci pour rester lisible dans le coach compact.

- **Cartes** : illustrations déjà autorisées/cache existant, reflet et léger relief au survol, agrandissement animé et limité à la hauteur d'écran. Absence d'image conservée honnêtement. Pas de nouvelle collecte ou bibliothèque graphique; option de réduction des mouvements appliquée aux nouveaux composants.
- **Chat unique** : bulles, commandes compactes et panneau repliable regroupant jusqu'à 50 liens cités. Messages/reçus originaux conservés; texte non fiable échappé, pas de chargement d'image HTML ni aperçu réseau. Sources et permissions existantes non remplacées.
- **Accueil** : favoris de références exactes, accès aux parties détaillées et point de travail descriptif du rapport. Favori n'atteste ni version jouée ni légalité. Ordre du rapport explicite si toutes les dates de combat ne sont pas attestées.
- **Navigation** : six icônes locales, menu repliable avec clavier, info-bulles et libellés accessibles. Préférences UI `favorite_decks` et `sidebar_collapsed` fusionnées aux anciennes valeurs et validées sans migration; aucun fichier personnel réel ouvert pour ce développement.
- **Combats** : fiche de résultat et frise des seuls événements connus, tour/rôle inconnus conservés, classification hypothétique et absence de cause démontrée visibles. Accès depuis l'accueil ou une barre de famille.
- **Statistiques** : bilan du corpus, résultats empilés par famille, répartition des derniers tours observés et occurrences d'événements consignés. Filtres par résultat dans les vues détaillées, survol et navigation clavier; clic de famille vers Combats. Effectifs absolus, échantillon global et détails disponibles séparés. Dernier tour visible différent de durée complète; prise de Récompenses différente de nombre de cartes prises. Pas de taux global, chronologie ou causalité fabriqués. Couleurs victoire/défaite/inconnu cohérentes.

Les projections utilisent uniquement le rapport déjà chargé par les services existants; aucun schéma ou moteur de collecte/combat modifié, aucun enregistrement parallèle des faits. Guide mis à jour. Aucun ajout de dépendance, daemon, hook ou scheduler.

## Qualification locale sur données inventées

Prévol **RUNTIME_READY**, DB propriétaire non ouverte, aucun réseau/écriture annoncé par cette commande. Runner synthétique existant : temporaires confinés à des espaces neufs marqués, aucune base personnelle sélectionnée.

**84 tests distincts réussis**, zéro échec/erreur/ignoré dans les passes finales, dont **18 nouveaux tests**. Les passes ne sont pas additionnées; les 18 nouveaux ont aussi été confirmés séparément après le dernier ajustement du panneau de sources. Couverture : effectifs agrégés vs traces partielles, filtres et inconnues, absence de chronologie inventée, événements vs Récompenses, échappement HTML, compatibilité/validation des préférences, favoris et ouverture sans changer le deck, menu/clavier, sources regroupées, frise sans fournisseur, survol/zoom et réduction des mouvements. Les 66 tests Qt précédents restent inclus dans 84.

Deux passes intermédiaires consolidées : **83 réussis / 1 échec** dans le dernier scénario de carte; transition restée Running à temps0 dans le troisième QApplication du processus. La même série de 18 tests seule réussissait. Dispositif corrigé : une unique fixture QApplication pour toute la session pytest, comme la durée de vie normale du produit, destruction explicite finale conservée. Les suites consolidées passent ensuite 84/84. Aucun timer de contournement ajouté au produit; ces observations ne prétendent pas établir indépendamment tous les détails internes de Qt. Aucun incident de confidentialité déclaré par les gardes.

Réception technique native : huit vues/captures de tableau de bord, quatre modes graphiques, favoris/parties, cartes avec illustration **explicitement fictive**, zoom, chat/sources, frise et petite fenêtre claire avec menu replié. Fixture en mémoire inventée : n=6, 2 victoires/3 défaites/1 inconnue, 6 traces et 18 événements; chiffres contrôlés par les projections/tests, aucun chiffre personnel utilisé. Contrôles positifs : zoom, icônes repliées, absence de défilement horizontal des réglages/navigation, bouton Envoyer accessible à 1100×700 avec sources ouvertes, six pages instantanées en mouvements réduits. Captures et reçus conservés localement hors Git.

Gardes : zéro refus, zéro GET de source réel, zéro appel de fournisseur réel rapportés. Il s'agit d'instrumentation Python, **pas d'une sandbox OS ou d'une mesure exhaustive du réseau Windows**.

## Production et installation

Premier candidat principal de production : build et smoke frozen exit0, sept modules embarqués conformes à la source, installation binaire au même chemin, ancien dossier conservé. Sa revue a motivé le seul raccourcissement final du libellé de pièce jointe.

**Candidat final e8f9849 : build de production en staging neuf exit0, smoke frozen Windows exit0**, sans option de build QA ni mode synthetic-release. Entrée de production et gardes de build inchangées. Les **7 modules applicatifs modifiés** (theme/window/widgets/sessions/card_art/charts/insights) embarqués correspondent aux sources après seule normalisation de co_filename; aucun module qa_offline/qa_unified dans le PYZ. Le portable est ouvert sur une nouvelle fixture indépendante, cloud/images/surveillance/actualisation désactivés, aucun fournisseur sollicité : fenêtre normale visible, six pages, rapport, référence60/galerie, import, activité et option de démarrage présents. Capture normale inspectée; libellé Joindre lisible. DB schéma7 fictive identique avant/après. Cette vérification de démarrage frozen est distincte des parcours complets de la GUI source; ne pas prétendre avoir rejoué tous les clics de favoris/graphes dans le binaire.

**Distribution finale installée au même dist/PokeMind/PokeMind.exe**, application fermée, aucun processus tué. Chemins source/cible/retour arrière vérifiés à l'intérieur du projet avant déplacements, aucune redirection ou donnée personnelle identifiée dans la distribution. **788 nouveaux fichiers** conformes au candidat, **788 fichiers de la distribution précédente conservés intégralement** et vérifiés. Les distributions antérieures sont aussi retenues, sans nettoyage, aucun raccourci externe changé et aucun rollback exécuté.

**Aucune ouverture ni inventaire de data/local personnel**, aucun compteur de matchs propriétaire recalculé, aucune ouverture de son application sur ses données. Aucun backup de DB, migration, import personnel, collecte réelle, installation ou modification Windows globale, aucune suppression. Favoris et menu ont été manipulés seulement dans les fixtures inventées. Réception personnelle non effectuée. Rapports assainis seulement; captures, logs bruts, bases, noms de retour arrière, destinations locales générées et empreintes personnelles restent hors Git.

Après push : contrôle HEAD distant et CI SHA exact, pas de rerun Actions ni changement de budget/workflow. **STOP audit indépendant ChatGPT**, aucune auto-attribution VERIFIED, réception propriétaire non accomplie.
