# Coach visuel — captures d'écran dans Codex

## Cadrage
Un **assistant de décision pour parties d'entraînement autorisées**, non un automate pour jouer et non un outil de compétition officielle. Les règles de tournoi peuvent interdire l'assistance pendant le match; aucune permission générale des plateformes n'est présumée. Pas d'accès mémoire au jeu, de capture furtive, d'overlay, de macros ni de clic automatisé.

## Fréquence des captures — décision produit
- **Photo initiale** : après le tour adverse, juste avant la première action du joueur : plateau complet + main + compteur de cartes Récompense et, si lisibles, nombres de cartes dans pioche/défausse.
- **Photo conditionnelle** : après une pioche, un effet de recherche, un changement de main, une évolution, ou une action qui ouvre de nouvelles options — seulement si la décision change; sinon le joueur suit la séquence annoncée.
- **Photo de correction** : si le plateau diverge de ce qui était prévu, ou si Codex ne peut pas lire le nom/texte d'une carte déterminante (crop lisible en plus).
- **Fin de match** : journal exporté, résultat; pas besoin d'une image de chaque début/fin de tour adverse si l'état final + log suffisent.

## UX Windows 11 / Codex CLI
Le joueur sauvegarde une capture via l'outil Capture d'écran Windows en PNG dans `data/local/screenshots/`. Codex reçoit le fichier **comme entrée image** par un mécanisme pris en charge par sa version (attachement, chemin vérifié ou `codex -i <path>` pour une invocation adaptée). L'import d'une image par simple copier-coller depuis le presse-papiers peut échouer sur certains Windows/terminaux; prévoir un repli fichier. Tester le parcours en session interactive réelle avant de déclarer fonctionnel.

Si utile après validation, fournir un petit helper explicitement lancé par l'utilisateur pour enregistrer la capture dans un fichier local — **aucun hook clavier global / surveillance du processus de jeu**.

## État de match local
Conserver `match_id`, horodatage, `turn`, deck version, captures attachées (local), cartes et ressources observées, actions confirmées par joueur, incertitudes, historique. Les cartes adverses non révélées, leur main et la pioche restent inconnues. Ne pas deviner la disponibilité des pièces nécessaires. Une capture isolée ne prouve pas que la main / pioche ou toutes les défausses sont visibles.

## Sortie attendue : courte, exploitable et conditionnelle
1. **Action conseillée** : suite ordonnée carte → effet → cible → suite, *seulement si légale compte tenu des infos visibles*.
2. **Pourquoi** : objectif (Récompenses, tempo, ressources), risque principal, tradeoff.
3. **Alternative** : si telle carte non disponible ou si l'adversaire répond de telle manière.
4. **Confiance / inconnues** : ce qui manque réellement. Ne jamais fabriquer la carte en main/pioche.
5. **Prochaine capture nécessaire ?** Oui uniquement après un changement conséquent.

La longueur de réponse est adaptée au temps de décision. Aucune promesse de « meilleur coup » mathématique, d'oracle parfait ni de faible latence constante; le contexte de Codex et le coût d'images peuvent être substantiels. Entre sessions, l'état structuré validé est durable, pas la totalité de l'historique en fenêtre de contexte.

## Acceptation
- Trois captures de test anonymisées : plateau clair, carte floue, état partiel. Signaler ce qu'on ne peut lire.
- Séquence d'au moins 3 tours avec suivi sans réinitialisation; refuser de déduire les cartes cachées.
- Tester l'attachement réel Windows 11; documenter recours au fichier PNG si collage échoue.
- Vérifier qu'aucune commande ne lit le processus du jeu, n'envoie d'input, ni n'automatise la partie.
