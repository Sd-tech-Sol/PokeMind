# Mise à jour courante — assistant unifié livré / AWAITING_AUDIT

2026-10-27 Québec. Après lancement explicite, **une conversation** relie Codex App Server par défaut, actions projet Codex/Claude, import+question, reconstruction hypothétique60 et mémoire Web permanente dans le cerveau existant. [Utilisation et contrats](UNIFIED_ASSISTANT_IMPLEMENTATION.md), [preuves](../.orchestrator/EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md), [état](../.orchestrator/STATE.json).

Les mentions datées de conception non lancée, terminal séparé ou chat exclusivement en lecture seule ci-dessous sont historiques et supplantées par cette livraison. Le coach conserve ses permissions propres; le développement est sélectionné par demande utilisateur explicite dans le même fil. Cloud ordinaire autorisé et mémorisé, aucun brut de journal envoyé automatiquement. Aucune migration SQLite personnelle ni nouveau backup. **V1 NOT_RELEASE_READY; STOP audit indépendant.** Réception Windows rapportée par l'exécuteur, CI au SHA final limitée par le budget Actions, sans succès présumé.

---

# Priorité produit — assistant unifié, conception en revue (2026-10-26)

Le [cahier unifié](UNIFIED_POKEMIND_ASSISTANT_DESIGN.md) prime sur les restrictions historiques du chat ci-dessous : une seule conversation doit pouvoir utiliser les outils réellement autorisés Codex/Claude et mémoriser les recherches. Lecture seule décrit **l'implémentation actuelle**, pas la capacité finale demandée. Préserver les barrières de données et permissions en ajoutant ces outils, pas de second chat/TUI. [Inventaire/CI](../.orchestrator/VERIFICATION_PM_V1_UNIFIED_ASSISTANT_REPRISE.md), [brouillon majeur](../.orchestrator/MANDATES/PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md). DESIGN_READY_OWNER_REVIEW, execute_now=false, V1 NOT_RELEASE_READY.

---

# PokeMind Desktop — décision d'architecture GUI + LLM (2026-10-25)

Correctif2026-10-26 : `desktop/ingestion.py` intercepte les journaux avant les
adaptateurs, réutilise le parseur/coaching/mémoire et publie exclusivement dans
le dossier local prévu. `desktop/widgets.py` fournit saisie/activité/graphiques/
galerie; `desktop/images.py` gère les illustrations publiques en cache local.
`services.py` garde la priorité des rapports personnels et leurs compteurs bornés.
Les questions IA restent en lecture seule; les imports sont un pipeline local
déterministe déclenché par le propriétaire. Le cache de fraîcheur/index privé
ne constitue pas un autre cerveau et ne contient aucune statistique parallèle.
Les options de démarrage et de surveillance du dossier ne fonctionnent que dans
l'application ouverte; aucun mandat GitHub n'est déclenché. [Guide](DESKTOP_GUI_CHAT_GUIDE.md).

Implémentation 2026-10-26 : [guide utilisateur](DESKTOP_GUI_CHAT_GUIDE.md),
`desktop/services.py`, `desktop/window.py`, `assistant/*`, scripts d'installation,
de build et de QA. Les preuves terrain restent locales; le contrôle de CI ne
certifie pas le PC. L'architecture ci-dessous demeure le contrat.

**Nouvelle cible explicite du propriétaire** : desktop Windows natif, chatbot à base de session **Codex CLI** par défaut, alternatives Claude Code et Ollama local, cœur analytique PokeMind inchangé. Ceci supplante toute phrase historique du PROJECT_SPEC disant « pas de GUI ».

## Technologies à réutiliser
- **Cœur** : Python >=3.11, SQLite/FTS5, cartes/decks/rapports et Learning Loop PokeMind déjà suivis. Adapter leurs APIs; ne pas les copier dans l'UI.
- **Qt/PySide6 Widgets** : extra optionnelle, build Windows portable, tests CI QPA offscreen; licence LGPLv3 et composants à examiner avant distribution. [Qt for Python officiel](https://doc.qt.io/qtforpython-6/) et [deployment](https://doc.qt.io/qtforpython-6/deployment/index.html). Electron/Tauri introduiraient un runtime lourd et une duplication d'interface backend; non retenus pour ce projet Python.
- **Codex** : `codex app-server` local `stdio` JSON-RPC, initialisation, threads, turns, streaming, interrupt et demandes d'approbation. App-server recommandé pour client UI intégré, plutôt que le TUI/PTY; utiliser les schémas générés de la version présente sur Windows. [Documentation](https://learn.chatgpt.com/docs/app-server), [présentation](https://openai.com/index/unlocking-the-codex-harness/), [SDK vs app-server](https://developers.openai.com/blog/codex-as-a-platform).
- **Claude Code** : CLI non interactif `claude -p` avec `stream-json` et session/resume, ou SDK Agent officiel au besoin; détecter availability/auth local sans nécessiter clé API additionnelle supposée. [Documentation](https://code.claude.com/docs/en/headless).
- **Ollama** : processus/service local déjà installé, `POST http://localhost:11434/api/chat` en streaming; modèle installé explicitement choisi, aucune installation automatique. [API](https://docs.ollama.com/api/chat).

## Structure suggérée
```
src/pokemind/
  desktop/              # fenêtre native + composants/navigation
  desktop/services.py   # read models/adapters vers APIs PokeMind existantes
  assistant/
    provider.py          # contrat commun
    codex_app_server.py  # stdio JSON-RPC long lived
    claude_code.py       # CLI/SDK adapter
    ollama_local.py      # API localhost-only
    context.py           # contexte PokeMind borné, sourcé
    sessions.py          # métadonnées/historique privé
```
Le nom exact des modules pourra être adapté aux patterns réels du repo; architecture logique obligatoire.

## Contrat chatbot
Provider `detect/health/start/resume/ask_stream/cancel/close`. Historique et thread IDs sous `data/local/chat`; savoir métier toujours dans PokeMind actuel, pas de deuxième SQLite cerveau. La session Codex CLI et l'historique local ne doivent pas être confondus avec la base officielle des cartes. Quand un fournisseur change, la session reste associée à son fournisseur; jamais fusionner implicitement des mémoires de services externes.

**Lecture seule par défaut** : les questions suivent des ressources PokeMind sourcées et réelles. Prompts d'attaque dans les logs/cartes ne sont pas des instructions. Ne pas accorder le shell de développeur au chatbot par défaut. Toute fonction d'écriture/destruction exige une action distincte compréhensible. Différencier cloud Codex/Claude (envoi possible des prompts/extraits sélectionnés) vs Ollama entièrement local. Préférence globale de confidentialité = contrôle explicite une fois, pas des popups par fichier.

## États à exposer à l'utilisateur
Codex disponible/auth nécessaire / session en cours / streaming / déconnecté / erreur; Claude non installé ou prêt; Ollama serveur local absent ou liste des modèles. Pour SQLite, `legacy7` signifie coaching par rapports dérivés toujours possible, pas accès illimité ou migration implicite. Statistiques des matchs = **échantillon choisi, non taux de victoire global**.

## Politique release
GUI réelle et Codex réellement lancé sur Windows sont des **preuves terrain**; les tests fake, les screenshots synthétiques et le green GitHub ne certifient pas ces étapes. L'app doit toujours rester utilisable pour l'analyse locale lorsque le moteur cloud n'est pas joignable. V1 `NOT_RELEASE_READY` tant que les critères indépendants non prouvés subsistent.
