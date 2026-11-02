# PokeMind 0.9.0 — first public pre-release

Your Pokémon TCG Live companion for Windows: battles, decks and cards, remembered on your PC.
**Pre-release**: tested on Windows 11, feedback welcome. Unofficial fan project by Sébastien Dubé, MIT licence.

## Install
1. Download `PokeMind-Setup-0.9.0.exe` below and run it. It installs for your account only (no administrator
   rights) in `%LOCALAPPDATA%\Programs\PokeMind`, with a Start menu shortcut.
2. The installer is **not code-signed** yet. If Windows shows « Windows protected your PC », choose
   **More info → Run anyway**. You can check the file first against `PokeMind-Setup-0.9.0.exe.sha256`.
3. On first launch, a short assistant asks for your language and coach engine, then offers to download the public
   card catalogue (TCGdex, French and English, about 25 MB to download, 175 MB on disk, about one minute).

Uninstall from Windows Settings → Apps → PokeMind. Your data in `%LOCALAPPDATA%\PokeMind` is kept.

## What is inside
- Battle logs from TCG Live: paste them in the chat or drop `.txt` / `.log` files; every game stays on your PC.
- A coach that talks to your own Codex CLI, Claude Code or local Ollama model, with sources and stated unknowns.
- Deck Lab, an offline card binder (French and English texts, printings, dated legality), learning notes and a
  built-in terminal.
- Nothing is sent to a cloud engine until you allow it in Settings → AI coach.

## Requirements
Windows 10 or 11, 64-bit. Optional for the coach: Codex CLI, Claude Code or Ollama (your own account or install).

## Known limits
- Not code-signed (SmartScreen warning above).
- The card catalogue is a pinned TCGdex snapshot; newer sets arrive with a later release.
- Pre-release: report problems in the Issues tab, without pasting private logs or personal data.

---

# PokeMind 0.9.0 — première préversion publique

Ton compagnon Pokémon TCG Live pour Windows : combats, decks et cartes, gardés sur ton PC.
**Préversion** : testée sous Windows 11, commentaires bienvenus. Projet de fans non officiel de Sébastien Dubé, licence MIT.

1. Télécharge `PokeMind-Setup-0.9.0.exe` ci-dessous et lance-le : installation pour ton compte seulement
   (sans droits administrateur), raccourci dans le menu Démarrer.
2. L'installateur n'est **pas encore signé**. Si Windows affiche « Windows a protégé votre ordinateur », choisis
   **Informations complémentaires → Exécuter quand même**. Son SHA-256 est dans `PokeMind-Setup-0.9.0.exe.sha256`.
3. Au premier lancement, un assistant te demande ta langue et ton moteur de coach, puis propose le catalogue
   public des cartes (TCGdex, FR/EN, environ 25 Mo à télécharger, 175 Mo sur le disque, environ une minute).

Désinstallation : Paramètres Windows → Applications → PokeMind. Tes données restent dans `%LOCALAPPDATA%\PokeMind`.
Rien ne part vers un moteur cloud sans ton accord (Réglages → Coach IA).
