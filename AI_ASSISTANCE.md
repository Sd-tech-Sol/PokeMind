# AI assistance disclosure

*Lire en français ci-dessous / French version below.*

## English

PokeMind is an original project by **Sébastien Dubé**: the idea, the product vision, the requirements, the
priorities, and every approval and final decision are his. Development itself was AI-assisted, and this
document says plainly how.

- **Architecture and independent audits.** **OpenAI ChatGPT** was used as architect and independent
  reviewer of the work, from the exact commit of each delivery.
- **Implementation.** **OpenAI Codex** and **Anthropic Claude Code** were used for implementation, tests,
  audits, documentation and reviews, under Sébastien Dubé's direction and review.

This means the project's history is one of **AI-assisted development**, not a claim that every line was
typed by hand. It also means the reverse: no AI tool is an author, an owner, or a maintainer of this
project. Using these tools implies no affiliation with, and no endorsement by, OpenAI or Anthropic.

PokeMind can also *talk to* Codex CLI, Claude Code or Ollama as its coach engine. That is a feature of the
application, chosen and configured by each user with their own account or local install; it is separate
from how the project was built.

**Final responsibility and maintenance rest with Sébastien Dubé.**

### What this document does not contain

No AI chain-of-thought, prompt log, or private working notes are published here. What is public is the
record of **decisions, tasks, tests and evidence** that the project keeps under version control:

- Decisions: [`.orchestrator/DECISIONS.md`](.orchestrator/DECISIONS.md)
- Current task, results and handoffs: [`.orchestrator/`](.orchestrator/)
- Independent audits: [`docs/audits/`](docs/audits/)
- Test suite and QA scripts: `tests/`, `scripts/`

Anyone can read those and judge the work on its results, the same way they would for any other codebase.

---

## Français

PokeMind est un projet original de **Sébastien Dubé** : l'idée, la vision produit, les exigences, les
priorités, ainsi que toutes les approbations et décisions finales, lui appartiennent. Le développement
lui-même a été assisté par IA, et ce document le dit clairement.

- **Architecture et audits indépendants.** **OpenAI ChatGPT** a servi d'architecte et de vérificateur
  indépendant du travail, à partir du commit exact de chaque livraison.
- **Implémentation.** **OpenAI Codex** et **Anthropic Claude Code** ont servi à l'implémentation, aux tests,
  aux audits, à la documentation et aux revues, sous la direction et la relecture de Sébastien Dubé.

L'historique du projet est donc celui d'un **développement assisté par IA**, et non l'affirmation que tout a
été tapé à la main. Cela signifie aussi l'inverse : aucun outil d'IA n'est auteur, propriétaire ou mainteneur
de ce projet. Leur utilisation n'implique aucune affiliation avec OpenAI ou Anthropic, ni aucune approbation
de leur part.

PokeMind peut aussi *dialoguer avec* Codex CLI, Claude Code ou Ollama comme moteur du coach. C'est une
fonction de l'application, choisie et configurée par chaque utilisateur avec son propre compte ou son
installation locale; elle est distincte de la façon dont le projet a été construit.

**La responsabilité et la maintenance finales reviennent à Sébastien Dubé.**

### Ce que ce document ne contient pas

Aucune chaîne de pensée d'IA, aucun journal de requêtes, aucune note de travail privée n'est publiée ici. Ce
qui est public, c'est le registre des **décisions, tâches, tests et preuves** que le projet conserve sous
contrôle de version :

- Décisions : [`.orchestrator/DECISIONS.md`](.orchestrator/DECISIONS.md)
- Tâche courante, résultats et passations : [`.orchestrator/`](.orchestrator/)
- Audits indépendants : [`docs/audits/`](docs/audits/)
- Suite de tests et scripts de QA : `tests/`, `scripts/`

Chacun peut les lire et juger le travail sur ses résultats, comme pour tout autre code source.
