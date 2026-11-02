# PROJECT_VISION.md — Project vision

## 1. Guiding idea

A Pokémon TCG Live player learns from their own games. PokeMind is the memory and the coach that make
that learning concrete: it keeps every battle, deck and card on the player's PC, and answers with sources,
dates and stated unknowns rather than confident guesses.

## 2. Positioning

PokeMind is a companion for **practice and review after the game**. It is not a bot, an overlay or a
tournament aid, and it never interacts with the game client.

## 3. Founding principles

### 3.1 Local first
The player's data stays on their PC. The network is used only for explicit actions: the public card
catalogue, card images, a Web research message, or a cloud coach engine the player allowed.

### 3.2 Windows first
TCG Live players are mostly on Windows; PokeMind is built, tested and packaged for Windows 10 and 11.

### 3.3 Sources before opinions
Official rules and announcements come first, then sourced card texts, then observed public results, then
summaries, then hypotheses. An unknown card, legality or win rate is said to be unknown.

### 3.4 Learning by observation
PokeMind learns by keeping versioned observations and statistics with their sample sizes, never by
retraining a model. One loss is not a reason to change a card.

### 3.5 The player chooses the engine
The coach talks to the engine the player installs — Codex CLI, Claude Code or a local Ollama model — with
the same PokeMind tools, and the player decides what it may receive.

### 3.6 Non-destruction by default
Imports never duplicate, moves are done by verified copy, and the application never deletes the player's
original data.

### 3.7 French and English
The interface, the card texts and the documentation exist in both languages.

## 4. Outside the scope

- Playing for the player, automation of the game client, overlays or hidden screen capture.
- Accounts, telemetry, advertising.
- Fabricated win rates, credit costs or collections.
