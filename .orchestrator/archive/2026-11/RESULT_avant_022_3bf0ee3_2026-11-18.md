# PM-UI-SIMPLIFICATION-021 — TERMINÉ / EN ATTENTE DU PROPRIÉTAIRE

2026-11-16, Québec. GO direct du propriétaire dans la session Claude Code (**D-316**), après avoir regardé
l'application avec ses vraies cartes : « le look est bon, mais c'est trop chargé pour quelqu'un qui l'ouvre la
première fois ». Branche `work/ui-premium-look`. **Rien n'est poussé.** L'audit ChatGPT de 019 reste attendu,
indépendamment (rapport 019 archivé : `archive/2026-11/RESULT_avant_021_e8479cb_2026-11-16.md`).

## Commits

| Commit | Contenu |
|---|---|
| `1e0c449`, `e8479cb` | Étapes 3 (coquille) et 4 (Deck Lab) du look premium 020, déjà faites avant ce mandat |
| `8883c9d` | Textes : mots de joueur, mises en garde derrière un bouton ⓘ, FR et EN |
| `e09fd8c` | Mise en page : galerie compacte, menu « ⋯ » du Coach, idées de questions, barre de titre, menu |
| `403a2bc` | Mode avancé : la page Terminal n'est au menu que si l'option est cochée |

Périmètre élargi par le propriétaire à `translations.py` (FR et EN) et aux tests qui verrouillaient ces textes.
À part le mode avancé, aucune logique, aucun service, aucune donnée modifiés.

## Ce qui change à l'écran

- **Une phrase d'aide par page**, plus de jargon affiché (corpus, n=, bilan descriptif, causalité,
  représentativité, batch). Les mises en garde ne sont pas supprimées : elles sont dans l'infobulle d'un bouton ⓘ
  à côté du titre concerné (survol, clic ou clavier).
- **Rien n'est affiché pour une valeur vide ou inconnue** : plus de ligne « Sources : » vide, plus de pastilles
  « inconnus », plus de « Tour ? » ni de « Rôle inconnu » dans la frise.
- « unknown » s'affiche « Adversaire non identifié » partout; le libellé du rapport reste la clé interne.
- Vue d'ensemble : « Dernière mise à jour : 16 novembre 2026 », « Toutes les saisons · 18 parties »; les
  victoires et défaites ne sont plus réécrites à côté du beigne (tuiles et beigne conservés).
- Combats : « Deck adverse », V, D, ?, « Parties », avec infobulles sur V, D et ?.
- Deck Lab : sous-titre court; les sélecteurs montrent le nom du deck (rang et « 50,8 % » seulement dans
  Classement); pastilles « Mon deck » et « Légalité à vérifier »; mise en garde de comparaison dans l'infobulle
  du bouton Comparer; galerie à 5 cartes par rangée à 1500 px, deux rangées visibles, sans étiquette « POKÉMON ».
- Apprentissage : les trois phrases de prudence dans le ⓘ; légende « Bleu : victoires · Rouge : défaites ».
- Coach : « Le coach peut lire tes données PokeMind » toujours visible; sélecteur de session, « Nouveau » et un
  seul menu « ⋯ » (Historique, Copier, Supprimer, Tout supprimer); discussion vide = trois idées cliquables
  (le clic remplit la zone de message, rien n'est envoyé seul).
- Terminal : « Codex », « Claude Code (sans confirmations) ».
- Barre de titre Windows sombre en thème sombre; case à cocher vide avec bordure.
- **« Vue d'ensemble » restait surligné** : cause trouvée. Le halo de la rangée active dépasse la rangée, et Qt ne
  repeignait que les deux rangées modifiées; la lueur de l'ancienne sélection restait sur la voisine. Chaque
  rangée peint maintenant, limitée à elle-même, la part de lueur qui la touche, et le menu entier est repeint
  au changement de page. Un test compare l'image réellement à l'écran à un rendu frais.

## Mode avancé (changement de comportement, GO explicite)

Réglages › Général › « Mode avancé », décoché par défaut, « Affiche le terminal pour Codex, Claude Code et
PowerShell ». Décoché : la page Terminal n'est pas au menu (ni atteignable par un lien interne). Coché : elle
revient à sa place habituelle. Préférence `advanced_mode` enregistrée comme les autres, conservée au redémarrage.
Si un terminal tourne quand on décoche : rien n'est arrêté, la case reste cochée et un message demande de le
fermer d'abord. Tests des deux états, de la persistance et du terminal en cours; FR et EN.

## Preuves

| Porte complète isolée | Qt réussis | Cœur réussis | Échecs | Ignorés | Total réussi |
|---|---:|---:|---:|---:|---:|
| `python scripts/local_gate.py` | 193 | 1696 | 0 | 3 | 1889 |

Compilation et hygiène vertes, exit 0, lancée sur l'arbre final (code, planches et orchestration de ce rapport).
Résultat local, **pas une CI GitHub**.
Planches avant/après : `docs/design/pokemind-brainball/captures/simplification/` (15 images, « avant » =
`e8479cb`), produites par `scripts/qa_premium_look.py --set simplification`; rapport, decks, cartes et discussion
inventés, aucune donnée personnelle, aucune illustration Pokémon, aucun réseau, aucun modèle.
Barre de titre : les captures hors écran ne montrent pas la barre Windows; vérifié à part sur la plateforme
Windows réelle avec une fenêtre de test à données inventées (attribut DWM « mode sombre » : 1 en thème sombre,
0 en thème clair, dialogues compris).

## Choix à signaler au propriétaire

1. Sélecteur de deck : le rang et le taux sont retirés aussi de son infobulle; ils restent dans Classement.
2. Deck Lab › Statistiques (chiffres publics) : l'affichage principal dit « 117 matchs », mais le volet replié
   « Sources et détails » et les descriptions des barres gardent des « n= » et « n ≥ » (non touchés ici).
3. La carte « DECK ACTIF » du menu garde son anneau « V / D » sur toutes les pages (elle fait partie du look
   accepté); sur la Vue d'ensemble les chiffres V/D restent donc lisibles là et dans les tuiles.
4. La barre de titre suit le thème par le réglage de couleurs de Qt : les dialogues natifs (ouvrir un fichier,
   messages) suivent donc aussi le thème choisi dans PokeMind.
5. Mode avancé décoché par défaut, y compris pour une installation existante : il faut le cocher une fois pour
   retrouver la page Terminal.
6. Les réponses du Coach viennent des services (non modifiés) : elles peuvent encore contenir « n= » ou
   « causalité ».
7. `CHANGELOG.md` non modifié (ses tests de métadonnées de version sont stricts); à faire avec la prochaine version.

## Limites

Aucune lecture de données personnelles, de l'application installée ou du compte du Coach; aucun build, aucune
installation, aucune publication. Le nombre de cartes par rangée est mesuré dans les captures hors écran
(polices Windows), pas sur l'écran du propriétaire. **Prochaine action : le propriétaire regarde les planches
ou l'application depuis la branche, puis décide (corrections, push, suite).**
