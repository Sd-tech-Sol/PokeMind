# PokeMind 0.9.1 — pre-release

Fixes found while testing 0.9.0. Unofficial fan project by Sébastien Dubé, MIT licence.

## Fixed
- **Deck rules**: a deck may hold only one ACE SPEC card and one Radiant Pokémon. 0.9.0 did not check this and
  could call such a list valid; 0.9.1 flags each extra card, and the coach cannot save a list that breaks a rule.
- **Saving a deck from the coach**: asking the coach to add a validated deck to **My decks** no longer depends on
  exact wording. It only creates a new deck, never overwrites one, and confirms it in the chat.

## Changed
- While battles are read or analysed, a large banner with a progress bar sits above every page. On the first
  reading, numbers show « … » and charts wait for real results instead of showing zeros.
- Chat: tool calls appear as one short line (for example « Tools · cards ×3 · deck check »); headings, lists,
  tables and code blocks are rendered; more readable font and spacing.

## Added
- **Delete all** in the chat history, after one confirmation that shows how many discussions will be erased.

## Install or update
Download `PokeMind-Setup-0.9.1.exe` below and run it; it updates an installed 0.9.0 in place and keeps your data in
`%LOCALAPPDATA%\PokeMind`. The installer is **not code-signed**: if Windows shows « Windows protected your PC »,
choose **More info → Run anyway**. You can check the file against `PokeMind-Setup-0.9.1.exe.sha256`.

---

# PokeMind 0.9.1 — préversion

Corrections trouvées en essayant 0.9.0. Projet de fans non officiel de Sébastien Dubé, licence MIT.

- **Règles de deck** : un deck ne peut avoir qu'une carte AS TACTIQUE (ACE SPEC) et un seul Pokémon Radieux.
  0.9.0 ne le vérifiait pas; 0.9.1 signale chaque carte en trop, et le coach ne peut pas enregistrer une liste
  qui enfreint une règle.
- **Enregistrer un deck depuis le coach** : demander au coach d'ajouter un deck validé à **Mes decks** ne dépend
  plus de la formulation. Il crée seulement un nouveau deck, n'en écrase jamais un, et le confirme dans le chat.
- **Chargement visible** : grand bandeau avec barre de progression pendant la lecture des combats; « … » au lieu
  de zéros au premier chargement.
- **Chat** : appels d'outils regroupés en une ligne, titres, listes, tableaux et code lisibles, police plus aérée.
- **Tout supprimer** dans l'historique du chat, après une confirmation.

Télécharge `PokeMind-Setup-0.9.1.exe` ci-dessous : il met à jour une 0.9.0 installée et garde tes données dans
`%LOCALAPPDATA%\PokeMind`. L'installateur n'est **pas signé** : « Informations complémentaires → Exécuter quand
même ». Son SHA-256 est dans `PokeMind-Setup-0.9.1.exe.sha256`.
