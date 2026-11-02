# Audit technique PM-0001

Date : 2026-10-10. Portée : fondation locale seulement, sans requête réseau.

## Composants retenus

- **Python 3.11+ et bibliothèque standard** : lecture UTF-8, SHA-256,
  `argparse`, JSON et SQLite. Environnement de validation : Python 3.13.15.
- **SQLite natif** : version 3.50.4 locale, `PRAGMA integrity_check=ok` et
  création FTS5 validée. Le tokenizer Unicode retire les diacritiques pour
  retrouver « récompenses » avec ou sans accent. Un repli `LIKE` local est
  créé seulement si le Python cible ne fournit pas FTS5; il est moins précis.
- **Markdown fourni** : source principale parce que les titres ATX et les dates
  sont directement démontrables. Les quatre PDF demeurent intacts comme pièces
  d'origine. Aucun parseur PDF ni mappage de pages non vérifiable n'est ajouté.
- **Backend d'installation local** : `scripts/pokemind_build_backend.py` utilise
  seulement `pathlib`, `zipfile`, `hashlib` et `base64`. Il lit exclusivement
  `src/pokemind/*.py`, écrit un wheel pur et ne lance aucun processus ni réseau.

## Dépendances externes

PokeMind n'a aucune dépendance externe d'exécution ou de construction. pytest
est l'unique dépendance directe de développement, épinglée à **9.1.1**. Cette
version était déjà installée; PM-0001 n'a installé ni mis à jour aucun paquet.
Les métadonnées locales indiquent : licence MIT, source
`https://github.com/pytest-dev/pytest`, documentation
`https://docs.pytest.org/`, et deux points d'entrée console (`pytest`,
`py.test`). L'activité distante n'a pas été interrogée, car PM-0001 interdit
l'extraction réseau; aucune affirmation d'audit distant à jour n'est faite.

TCGdex et Limitless ne sont pas des dépendances de PM-0001. Leur dépôt,
licence, activité, versions, conditions d'utilisation et schémas devront être
audités avant le premier appel réseau de leur tranche respective. Aucun script
d'installation distant, `curl | sh`, service cloud ou tâche planifiée n'a été
utilisé.

## Solutions explicitement écartées

Un moteur vectoriel, LangChain, un service cloud ou un LLM local ne répondent à
aucun besoin démontré pour quatre documents structurés. Ils ajouteraient poids,
coûts, permissions, surface d'attaque et résultats plus difficiles à expliquer.
SQLite FTS5 donne ici une recherche hors ligne, déterministe et citable.

Limitless reste prévu par la roadmap, après les dépendances nécessaires au
catalogue, aux decks et aux journaux. Aucune API Pokémon TCG Live permettant
d'exporter toute une collection ou de jouer automatiquement n'est présumée.
