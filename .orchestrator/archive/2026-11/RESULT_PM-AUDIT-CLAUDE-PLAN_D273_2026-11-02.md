# RESULT — PM-AUDIT-CLAUDE-PLAN : retours d'essai du propriétaire corrigés (D-273), 2026-11-02

Exécuteur : Claude Code (Opus 5.5). Demande : retours du propriétaire après essai de l'app (chargement invisible,
suppression de toutes les discussions, lignes d'outils brutes et typographie du chat, erreurs du coach et
enregistrement de deck refusé). Session précédente (D-272) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D272_2026-11-02.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D272_2026-11-02.md).

## Corrigé (commit `9a9c6b4`)
- **Règle de deck manquante** : une liste avec deux cartes AS TACTIQUE (ACE SPEC) était déclarée valide, car
  `special_card_rule_limits` restait « non vérifié ». `rules.check_deck_entries` compte maintenant les cartes ACE SPEC
  et Radieux d'après la rareté du catalogue (`DECK_ACE_SPEC_LIMIT_EXCEEDED`, `DECK_RADIANT_LIMIT_EXCEEDED`);
  `validate_deck` le signale carte par carte; `save_deck` refuse une liste qui viole une règle de deck.
  **Ce défaut existe dans la préversion publique 0.9.0.**
- **Enregistrement refusé** (`SAVE_DECK_REQUIRES_OWNER_REQUEST`) : la détection par mots-clés du message ne
  reconnaissait pas la demande. `save_deck` (création seulement, jamais d'écrasement) n'en dépend plus;
  `save_candidate` garde sa barrière. Le chat confirme « Deck ajouté à Mes decks : … ». Consignes du coach : chaque
  carte lue avec `cards` et un rôle justifié, 1 ACE SPEC et 1 Radieux au plus.
- **Chargement visible** : grand bandeau au-dessus de toutes les pages avec barre de progression (« N / M journaux
  lus »); au premier chargement, « … » au lieu de zéros et graphiques masqués jusqu'aux vrais chiffres.
- **Tout supprimer** dans l'historique du chat, avec une confirmation qui donne le nombre de discussions.
- **Chat** : les lignes `[Outil · mcp__pokemind__…]` deviennent une seule ligne discrète (« Outils · cartes ×3 ·
  validation du deck »); titres, listes, tableaux et blocs de code rendus de façon sûre (tout est échappé);
  police Segoe UI Variable avec repli Segoe UI, interligne aéré; boutons de l'historique sur deux rangées.
  Les discussions enregistrées gardent le texte brut; seul l'affichage change.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `9a9c6b4` : Qt 99, cœur 1546 réussis, 3 ignorés.
- Captures hors écran sur un dossier inventé : bandeau, tuiles « … », chat (ligne d'outils, tableau, listes) et
  boutons de l'historique entiers.
- EXE reconstruit depuis `9a9c6b4` : 75 modules `pokemind` identiques aux sources, aucun module QA; fumées mode
  projet, mode autonome et copie installée : sortie 0; installation et désinstallation silencieuses propres.
  Déployé dans `dist/PokeMind/` (ancien conservé sous `dist/PokeMind-before-0.9.0-fixes-<id>`); installateur copié
  dans `dist/installer/` (celui publié renommé `-publie.exe`, hors Git). SHA-256 du nouvel installateur
  `953D652B5ABEEB9084899387F1E5FD1CAF6C6CAADE4B665B1900AA8A9FACF9A2` (non publié).

## Limites
- Vitesse de l'analyse au démarrage : pas encore optimisée. Le coût vient de la réanalyse de tout le corpus quand
  un journal change (M-4). Il faut les lignes « Analyse · étape · durée » du diagnostic masqué du propriétaire
  (Réglages → Copier le diagnostic) avant de toucher au moteur.
- Pikachu ex « ASC 057 » de la réponse du coach : impression non vérifiée ici (catalogue du propriétaire non lu).
- Dépôt public inchangé : une 0.9.1 publique exige un GO.
