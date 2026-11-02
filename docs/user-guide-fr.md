# Guide d'utilisation de PokeMind

## Premier lancement
Un court assistant te demande ta langue, ton moteur de coach et comment tu gardes tes journaux de combat,
puis propose le catalogue public des cartes (environ 25 Mo, une minute). Tu peux le faire plus tard dans
**Réglages → Données**.

## Importer tes combats
Dans TCG Live, copie un journal de combat et colle-le dans le chat, dépose des fichiers `.txt` / `.log`, ou
utilise **Joindre un journal**. PokeMind analyse la partie, la garde localement et n'importe jamais deux fois
le même journal. La page **Combats** liste tes parties, classe les adversaires par défaites et montre chaque
partie en frise.

## Parler au coach
Choisis un moteur en haut du chat (Codex CLI, Claude Code ou Ollama), puis autorise une fois le partage cloud
dans **Réglages → Coach IA** si tu utilises un moteur cloud. La liste à gauche d'**Envoyer** choisit ce que
fait le message :

- **Coach** : répond avec ta mémoire locale et le catalogue, sans Internet;
- **Recherche web** : une collecte publique bornée avant la réponse, pour ce message seulement;
- **Développement** (depuis le dossier des sources seulement) : Codex ou Claude travaillent sur le code.

**Agrandir** ouvre la discussion en grande fenêtre. **Arrêter** interrompt une réponse.

## Decks et cartes
**Deck Lab** garde tes listes de 60 cartes, les compare et les exporte pour TCG Live. **Cartes & méta** ouvre
un classeur hors ligne : tourne les pages avec ‹ ›, clique une carte pour ses textes FR/EN, ses impressions
et sa légalité datée.

## Tes données
Tout est dans `%LOCALAPPDATA%\PokeMind`; **Réglages → Données** montre le dossier. La désinstallation
(Paramètres Windows → Applications) garde tes données. N'ouvre pas deux copies de PokeMind en même temps.
