# PM-V1-POKEDEX-MOTION-001 — preuves assainies

2026-10-27 Québec. **CODEX_LOCAL_REPORTED**. Nouvelle demande manuelle du propriétaire : transitions animées et embellissements pour rendre l'interface plus belle et attractive. Périmètre graphique et préférence UI seulement; aucune reprise d'une opération personnelle historique. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.

## Traçabilité et réalisation

- Base synchronisée par fetch/pull fast-forward : `130ac9f434b8bf98ec0202a0f46bfa3e1ff88164`.
- Source compilée : **`7dbb66858e83e2afc482a8843fd0f2326395b617`**, branche autorisée `work/pm-v1-lotj-final-readiness-windows`.
- `desktop/motion.py` : transition native entre pages par fondu/glissement bref, survol lumineux des boutons/panneaux, onde au clic et réaction de la Poké Ball. Les copies de rendu des pages restent uniquement en mémoire et sont libérées à la fin/interruption; aucune capture écrite par l'application normale.
- `desktop/widgets.py` : dessin progressif des arcs/barres, nombres du rapport conservés immédiatement; cases natives à texte multiligne pour garder les réglages lisibles. `window.py` intègre les effets dans les six écrans existants et rend les réglages défilables verticalement.
- `assistant/sessions.py` : un booléen UI `reduced_motion`, faux par défaut, fusionné aux anciennes préférences sans migration; validation de type conservée. Le choix dans Réglages interrompt les effets en cours et rend les changements de page instantanés. Aucune préférence personnelle réelle ouverte par l'exécuteur.
- Effets de durée bornée, sans boucle d'animation au repos. Arrêt sur page cachée/fermeture; redimensionnement et nouvelle navigation interrompent proprement la transition. Clavier et signaux des boutons conservés. Aucune dépendance, illustration ou police externe, aucun daemon/hook/scheduler ajouté.

## Qualification sur fixtures inventées exclusivement

- Prévol **RUNTIME_READY**, DB propriétaire non ouverte, zéro écriture/réseau indiqué par cette commande.
- Passe finale Qt native Windows : **66 tests distincts réussis, 0 échec, 0 erreur, 0 ignoré**, dont **4 nouveaux tests**. Les passes successives ne sont pas additionnées. Runner synthétique existant : temporaires précoces confinés, zéro refus et aucun incident déclaré, zéro GET de source et zéro fournisseur réel; aucune garantie de sandbox OS.
- Nouveaux scénarios : changements de page rapides et resize, retour à la vraie page et libération des images; interruption/réactivation et persistance du choix réduit; clic souris puis espace clavier non interceptés par le décor; fermeture pendant une transition sans animation restante. Réglages en petite fenêtre sans défilement horizontal.
- Inspection native en sombre/clair, grande fenêtre et 1100×700. Huit captures successives d'une transition donnent trois images distinctes, puis état final correct; ce contrôle **ne mesure pas un FPS garanti**. Navigation rapide stable, images libérées, vrais compteurs maintenus pendant le dessin du graphique, réduction sauvegardée et animations arrêtées au repos. Captures fictives et reçus gardés localement, hors Git.
- La revue visuelle a révélé un mélange de textes pendant le fondu (fond du calque transparent) et un débordement horizontal des réglages. Fond de transition rendu opaque, contenu des réglages adapté et libellés natifs multiligne, puis nouvelle inspection et suite verte. Aucun échec de test ou accès privé n'est présenté comme un succès implicite.

## Build, installation et arrêt

Build de production en staging neuf via le script existant : **exit 0**, sans option QA. Archive PyInstaller : les **5 modules modifiés** (motion/theme/widgets/window/sessions) correspondent exactement aux sources après seule normalisation de co_filename; pas de modules qa_offline/qa_unified dans le PYZ. Aucun changement du build, de l'entrée de production ou de ses gardes.

Le même candidat est lancé sur une nouvelle racine fictive indépendante avec le smoke de production existant, **pas le mode synthetic-release** : **frozen Windows exit 0**, fenêtre visible, rapport, six pages, référence60 et galerie, contrôles d'import, activité et option de démarrage présents. Capture normale inspectée localement, Poké Ball et graphique observés en cours d'animation. DB schéma7 de fixture identique avant/après. Images hors ligne, cloud/surveillance/actualisation désactivés dans cette fixture, aucun fournisseur sollicité; aucune prétention d'observation exhaustive des sockets.

Installation : distribution complète au même **dist/PokeMind/PokeMind.exe**, application fermée, aucun processus tué. Source/cible/destination de retour arrière vérifiées dans le projet avant les déplacements, sans redirection ni fichier/dossier personnel identifié dans les binaires. **788 anciens fichiers conservés intégralement**, **788 nouveaux fichiers** conformes au candidat; inventaires binaires concordants pour le nouveau dossier et l'ancien retenu. Aucun raccourci externe modifié, aucun rollback exécuté, aucun dossier supprimé.

**Aucun accès ni inventaire de data/local personnel**, aucun compteur de matchs réel recalculé, aucune ouverture propriétaire. Aucun backup de DB, migration, import, collecte réelle, installation ou changement Windows global. Ne pas annoncer 66 matchs personnels vérifiés : **66 est ici le nombre de tests Qt**, aucun nouveau contrôle du corpus réel. Les preuves brutes et destinations locales générées restent hors Git; jamais de base, capture, log brut, nom de retour arrière, chemin absolu ou empreinte personnelle publié.

Après publication : contrôler HEAD distant et CI au SHA exact, sans rerun Actions ni modification de budget/workflow; conserver AWAITING_EVIDENCE si aucun job ne démarre. STOP audit indépendant ChatGPT, aucune auto-attribution VERIFIED et aucune réception propriétaire déclarée.
