---
name: combat
description: Importer le dernier journal de combat Pokémon TCG Live fourni par l’utilisateur et donner un bref suivi prudent du profil PokeMind.
---

# Dernier combat PokeMind

Utilise ce Skill quand l’utilisateur demande d’importer son dernier combat et de le conseiller.

1. Ne lis le presse-papiers que si l’utilisateur le demande explicitement et indique avoir copié le journal. Lance alors `python -m pokemind log import --clipboard --deck principal --json`. Pour un fichier joint ou nommé, utilise plutôt ce fichier; n’affiche et ne conserve jamais le journal brut.
2. Lance ensuite `python -m pokemind profile summary --deck principal --json`. Lance aussi `python -m pokemind profile review --deck principal --json` seulement si le résumé ou la demande exige les preuves par partie.
3. Réponds brièvement en français (Québec) avec l’issue reconnue, doublon oui/non, progression `n/5`, puis une ou deux observations corroborées. Une observation de carte est corroborée seulement si `games_seen >= 2`; sinon, présente-la comme un fait isolé ou omets-la.
4. Affiche les incertitudes importantes. Avant cinq parties valides, ne transforme pas l’échantillon en recommandation de deck. À cinq parties ou plus, toute recommandation demeure exploratoire et cite `n`.

Ne déduis jamais la liste de 60 cartes ni la collection à partir des journaux. N’invente ni carte manquante, ni légalité, ni coût, ni statistique de méta. N’interagis pas avec le client Pokémon et n’aide pas pendant une situation où l’assistance externe est interdite.

Si le Skill n’est pas découvert, le repli concret est : `python -m pokemind log import --clipboard --deck principal --json`, puis demander « Résume et révise le profil principal avec PokeMind ».
