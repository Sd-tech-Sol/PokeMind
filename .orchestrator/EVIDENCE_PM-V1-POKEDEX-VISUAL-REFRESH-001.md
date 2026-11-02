# PM-V1-POKEDEX-VISUAL-REFRESH-001 — preuves assainies

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT.** V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE. Nouvelle demande manuelle du propriétaire : rendre le graphisme plus à l'image de Pokémon; elle remplace l'attente du mandat précédent pour ce nouveau périmètre visuel, sans attester sa réception personnelle ni le relancer.

## Portée et sources

Base synchronisée par fetch/pull fast-forward : `7ac46430f3b3f9194838e0845249d445aafa1556`. Source compilée : **`44f966b0bed3bc93dd917d08d952e317379684c3`**. Branche autorisée : `work/pm-v1-lotj-final-readiness-windows`.

Trois modules visuels seulement : `desktop/theme.py`, `desktop/window.py`, `desktop/widgets.py`, plus guide. Palette rouge/anthracite/blanc/jaune, Poké Ball vectorielle dessinée en Qt, marque et navigation, bannière, panneaux et graphiques, titres du coach, catégories de cartes. Deux palettes explicites clair/sombre, liens et contraste adaptés. Aucun téléchargement de police ou illustration, aucune dépendance ajoutée. Le tableau de bord défile dans une petite fenêtre et le changement de langue retrouve son titre à travers ce conteneur. Les services, imports, permissions et mécanismes de persistance restent hors du diff fonctionnel.

## Qualification locale

- Prévol : **RUNTIME_READY**, `owner_database_opened=false`, zéro écriture ou réseau indiqué par cette commande.
- Suite Qt/interaction existante exécutée avec le runner synthétique à temporaires précoces et gardes : **62 tests distincts réussis, 0 échec, 0 erreur, 0 ignoré dans la passe finale**. Plusieurs passes ne sont pas additionnées. Les gardes rapportent zéro refus, zéro GET de source, zéro appel de fournisseur réel; cela n'est pas une sandbox OS.
- Après ajout du conteneur défilant, une passe intermédiaire a produit **1 erreur de setup, 0 test appelé** : `apply_language` cherchait directement le layout de la page. Correction locale : retrouver le contenu du QScrollArea avant de mettre à jour son titre. Les passes suivantes et le portable sont verts. Aucun incident de confidentialité relevé par les gardes.
- Inspection visuelle native Windows sur fixtures inventées : sombre 1500×940, clair 1500×940 et clair 1100×700; navigation des six pages dans les trois configurations, icône présente, changements de thème fonctionnels. Les premiers chevauchements en petite taille ont motivé le défilement; après correction, les six entrées de navigation et le coach restent accessibles. Captures exclusivement fictives conservées localement, hors Git.
- Build **de production** existant en staging neuf : **exit 0**. Aucune option SyntheticQaRoot, aucun remplacement direct pendant le build, aucune installation ou changement global Windows.
- Archive PyInstaller inspectée : les trois modules visuels embarqués correspondent exactement au code source, après seule normalisation de co_filename; absence des modules qa_offline/qa_unified dans le PYZ. Le vrai candidat est lancé avec le smoke de production existant, sur une nouvelle racine fictive indépendante, aucun mode synthetic-release.
- Portable frozen Windows : **exit 0**, fenêtre visible, rapport chargé, six pages, référence60, galerie, contrôles d'import, activité et option de démarrage présents. Capture de la fenêtre normale inspectée, aucun bandeau QA embarqué. DB schéma7 **de fixture seulement** identique avant/après. Images hors ligne, consentement cloud, surveillance et actualisation automatique désactivés dans cette fixture; aucun fournisseur sollicité. Aucune prétention d'observation exhaustive des sockets Windows.

## Installation locale et conservation

Le candidat qualifié a remplacé la distribution au même **`dist/PokeMind/PokeMind.exe`**, cible déjà confirmée par le propriétaire lors du mandat précédent. Application fermée lors des contrôles avant déplacement, aucun processus tué. Chemins absolus de source/cible/rollback vérifiés à l'intérieur du projet avant les déplacements; redirections et noms de fichiers/dossiers personnels refusés.

Ancienne distribution : **788 fichiers**, dossier entier déplacé vers une destination neuve locale, sans suppression. Nouvelle distribution : **788 fichiers**, installée entière au même emplacement. Empreintes des seuls fichiers binaires/support : candidat et installation concordent; ancien dossier retenu et inventaire d'origine concordent. Nom exact du dossier de retour arrière et inventaires locaux hors Git. Aucun raccourci externe modifié, rollback non exécuté.

**Aucune ouverture ni inventaire de data/local personnel**, aucun compteur personnel recalculé : ne pas présenter un nouveau 66→66 comme vérifié par ce mandat. Aucune base personnelle lue, copiée, sauvegardée, migrée ou remplacée; aucun journal, deck, conversation, préférence ou contenu privé volontairement consulté/modifié. L'EXE n'a pas été lancé sur le projet personnel. Réception propriétaire non effectuée.

## Publication et arrêt

Hygiène du dépôt et diff préparé contrôlés; seuls code, guide et rapports assainis sont publiés, aucun binaire, capture, log brut, base, manifeste, chemin absolu, nom de rollback ou empreinte de données personnelles.

Contrôler après push le HEAD distant et les jobs CI **au SHA exact**. Si aucun job ne démarre ou si pending, conserver **AWAITING_EVIDENCE**; aucun rerun Actions ni modification du workflow/budget. Aucun résultat CI historique n'est repris comme preuve. Les contrôles définitifs post-push sont communiqués sans boucle de commits contenant leur propre SHA.

**STOP audit indépendant ChatGPT.** Le présent agent ne s'attribue pas VERIFIED et ne certifie pas la V1 complète. Prochaine réception visuelle du programme habituel par le propriétaire après audit; aucune nouvelle exécution Codex automatique.
