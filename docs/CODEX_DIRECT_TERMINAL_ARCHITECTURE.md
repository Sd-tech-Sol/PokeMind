# ARCHIVE ANNULÉE — deux conversations / terminal Codex Direct

**2026-10-26 : ce document est supplanté par [UNIFIED_POKEMIND_ASSISTANT_DESIGN](UNIFIED_POKEMIND_ASSISTANT_DESIGN.md).** Ne pas exécuter son ancienne décision ni développer Coach séparé/Codex Direct. Le [mandat unifié proposé](../.orchestrator/MANDATES/PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md) est un brouillon sans autorisation. Le texte historique est conservé ci-dessous uniquement pour traçabilité.

---

# PokeMind — Codex direct dans Qt, distinction terminal et Coach (2026-10-26)

## Diagnostic code réel
`src/pokemind/assistant/codex_app_server.py` est un chat agentisé volontairement read-only : shell désactivé, `sandbox=read-only`, `approvalPolicy=on-request`, demandes de commande refusées. `/status` dans ce chat ne peut pas avoir le comportement d'une vraie commande slash de l'application Codex CLI. Ne pas « fixer » cela en retirant seulement DISABLED et en interprétant `/status` comme une question LLM.

## Décision architecture
Créer une **vraie instance Codex interactive** avec terminal pseudo-console Windows ConPTY dans l'interface PySide6. Réutiliser prioritairement un composant mature (ex. `pywinpty` + `pyte`, comparer licences et activité) avec rendu VT correct. Garder **deux sessions différentes** : Coach App Server API PokeMind lecture seule, et Codex Direct TUI dans le widget. Ne jamais prétendre que leur session historique, droits et outils sont interchangeables.

Comportement : dock redimensionnable, bascule Coach/Codex direct/Claude direct, focus clavier fidèle, slash commands natives, /status réel, Ctrl+C, VT/colors, resize, consultation des écrans PokeMind côte à côte, reprise si CLI compatible. `--yolo` activable seulement par utilisateur dans Réglages avec avertissement initial et badge persistant; option normale par défaut. Le choix affecte une nouvelle session TUI, pas le chatbot Coach. Pas de permissions système au-delà du compte Windows connecté.

Références :
- <https://developers.openai.com/blog/codex-as-a-platform> — App Server pour interfaces orchestrées, pas remplacement de la TUI.
- <https://developers.openai.com/blog/mastering-codex-remote-for-engineering> — commande `/status` native et détails d'utilisation.
- <https://devblogs.microsoft.com/commandline/windows-command-line-introducing-the-windows-pseudo-console-conpty/> — Windows pseudo console.
- <https://pypi.org/project/pywinpty/> — liaisons ConPTY/WinPTY pour Python.

## État
Ce document définit le **mandat à exécuter**, pas une livraison déjà testée. La CI du code précédent est verte au HEAD `2e28b33` run `40408811095`. Aucune vraie TUI nouvelle n'est créée avant l'exécution Codex locale. V1 `NOT_RELEASE_READY`.
