---
name: visual-training-coach
description: Accompagner une partie Pokémon TCG Live d’entraînement autorisée à partir d’images locales éphémères et d’annotations prudentes, avec mémoire textuelle multi-tours et conseils conditionnels.
---

# Coach visuel d’entraînement PokeMind

Utilise ce Skill quand le propriétaire demande « voici mon plateau », un conseil de tour ou le suivi d’une partie d’entraînement où l’assistance est permise.

1. Confirme que le contexte est un entraînement autorisé. Refuse le coaching en tournoi ou si l’assistance externe est interdite. N’accède jamais au processus, au presse-papiers, à l’écran ou au client Pokémon automatiquement.
2. Ouvre une mémoire seulement sur demande explicite :
   `python -m pokemind match start --as-of DATE --format standard --platform live --apply --confirm-owner --json`.
3. Pour une image volontaire sous `data/local/`, prévisualise d’abord :
   `python -m pokemind match observe --image CHEMIN --turn N --mode training --dry-run --json`.
   L’image n’est ni copiée, ni mise en base, ni envoyée au réseau. Si la sortie dit `NEEDS_MANUAL_ANNOTATION`, demande une annotation JSON minimale; ne prétends pas avoir reconnu le plateau.
4. Une annotation validée peut être mémorisée avec `--annotation FICHIER --session ID --apply --confirm-owner`. Les cartes cachées, la pioche, la main adverse et le contenu des Récompenses restent `UNKNOWN`. Une carte sans impression exacte ne reçoit aucun effet inventé.
5. Demande le conseil avec `match advise --session ID --turn N --format standard --platform live --as-of DATE --json`. Présente une séquence courte, un repli, la justification, les conditions et la prochaine preuve minimale. Respecte `verified_possible`, `conditional` et `not_supported`; ne transforme jamais une option conditionnelle en meilleur coup certain.
6. Après une erreur, utilise `match correct`; une correction peut être annulée avec `match revoke-correction`. Relis avec `match show`. Termine volontairement avec `match close --apply --confirm-owner`.

Demande une nouvelle image seulement après une pioche/recherche/effet déterminant ou un changement majeur. Ne calcule aucun taux de victoire à partir du faible échantillon, n’automatise aucun clic et ne supprime jamais le fichier source du propriétaire. Le contrat et les exemples se trouvent dans `docs/LOT_C_VISUAL_COACH.md`.
