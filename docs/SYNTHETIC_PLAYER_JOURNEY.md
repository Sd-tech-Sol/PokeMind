# Parcours joueur intégré — données entièrement inventées

Le test `tests/test_synthetic_player_journey.py` traverse les moteurs existants :
bibliothèque PUBLIC → export60 → fiche sourcée → défaite choisie → adversaire
partiel → contre-plan → apprentissage et correction de version → vues PUBLIC.
Il ne consulte aucun vrai cache, journal, deck ou profil du propriétaire.

La fixture réutilise les constructeurs fictifs existants, avec une liste de
60 cartes inventée dans le test. L’ancienne entrée de deck statique est remplacée
en mémoire avant utilisation; aucun fichier de deck préexistant n’est lu.
Les pages et le ledger sont générés dans la fixture, sans GET. Quatre compositions
publiques fictives couvrent six placements; les étiquettes d’archétypes des anciens
tests sont des catégories de simulation et ne prouvent rien sur le métagame réel.

Le parcours vérifie les transitions suivantes :

| Étape | Résultat vérifié sur la fixture |
| --- | --- |
| Bibliothèque → export → fiche | 4 compositions/6 placements; exports reparsés à60 cartes; sélecteur, sources datées et affirmations soutenues conservés. |
| Défaite FR sélectionnée → aperçu | Issue `losses`, aucune partie comptée avant import, aucune écriture dans la DB fictive. |
| Import explicitement simulé | Une seule partie; reprise du même log idempotente; version jouée encore inconnue. |
| Attestation séparée | v1 et date du10octobre explicitement déclarées dans la simulation; jamais déduites de la date d’import. |
| Adversaire → référence | `Synthetic Delta` observé, quantité minimale1; carte piochée cachée exclue; famille hypothétique, proxy PUBLIC60 distinct du deck adverse exact. |
| Référence → contre-plan | 4 alternatives60, différences exactes conservant60 copies, hypothèses/protocoles de test; crédits, avantage et causalité inconnus. |
| Learning → révision | Hypothèse retirée puis réouverte sans modifier les faits; reprise identique sans doublon. |
| Correction de version | Retrait motivé de v1, attestation de v2; groupes séparés, aucune amélioration causale démontrée. Il s’agit d’une correction simulée, pas d’un changement recommandé du deck. |
| PUBLIC → humain/JSON/HTML | Même jeu de compositions sur deux copies SQLite fictives aux chemins fixes du lecteur borné; sélection123:1, dénominateurs et reprise HTML concordants. |

Le contre-plan conserve sa base PUBLIC choisie par son propre contrat. Une
correction de version dans l’historique joueur ne modifie ni le deck joué ni
cette base automatiquement. Aucune carte responsable de la défaite n’est démontrée.

Les sources PUBLIC du lecteur borné restent **SOURCE_UNREVALIDATED /
BLOCKED_SOURCE_SCOPE**, y compris en HTML. La fixture complète possède ses
propres pages inventées pour les moteurs qui revalident les sources; le lecteur
à deux SQLite ne consulte pas ces pages. Ces portées de preuve restent distinctes.
Le HTML ne fait que sortir sur stdout, sans fichier exporté ni navigateur ouvert.

Les cas négatifs couvrent les trois consentements distincts et leur combinaison
refusée avant I/O, W/L/inconnu dans les deux langues, petits n sans winrate,
texte natif manquant/futur propagé jusqu’au contre-plan, absence de paire PUBLIC,
erreurs CLI neutres et absence de fuite de chemin. Les vues PUBLIC sont lancées
dans de vrais processus CLI, démarrage CP1252 puis sortie UTF-8 stricte, sous le
garde d’I/O existant. Les appels aux moteurs refusent les DB hors fixture et les
ouvertures de données externes; écritures exclusivement dans la fixture, imports
de code seuls autorisés en dehors. Découverte de noms, accès fournisseur et
presse-papiers sont bloqués. Les fichiers PUBLIC fictifs sont comparés par leurs
chemins littéraux et les références du ledger inventé, sans parcours de dossier.

## Reproduction locale bornée

Ce script collecte uniquement les trois modules explicitement nommés, sans
conftest, collecteur de répertoire ou plugins externes. Les fixtures neuves restent
dans leur espace synthétique ignoré; aucun nettoyage additionnel n’est exécuté.
La suite générale est réservée à la CI GitHub isolée.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:POKEMIND_TEST_OFFLINE='1'
@'
import sys, tempfile
from pathlib import Path
import pytest
root = Path.cwd()
sys.path.insert(0, str(root / 'tests'))
class LiteralTests:
    @pytest.fixture
    def local_tmp(self):
        parent = root / 'data/local/test-runs'
        parent.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='player-journey-', dir=parent))
    @pytest.hookimpl(tryfirst=True)
    def pytest_collection(self, session):
        items = []
        for name in ('tests/test_synthetic_player_journey.py',
                     'tests/test_public_identity_rules_scoped.py',
                     'tests/test_public_evidence_explain_cli.py'):
            items.extend(pytest.Module.from_parent(session, path=root/name).collect())
        session.items = items
        session.testscollected = len(items)
        session.config.hook.pytest_collection_modifyitems(
            session=session, config=session.config, items=items)
        session.config.hook.pytest_collection_finish(session=session)
        return True
raise SystemExit(pytest.main(['-q', '-x', '--noconftest', '-p', 'no:cacheprovider',
    '--import-mode=importlib', '-c', 'pyproject.toml', '-o', 'addopts='],
    plugins=[LiteralTests()]))
'@ | python -B -
```

## Commandes des moteurs existants

Les variables ci-dessous désignent **uniquement les chemins renvoyés par une
fixture inventée**, jamais des données réelles à rechercher. Le test intégré
appelle directement les moteurs et vérifie également la CLI de revue humaine/
JSON. Voici les commandes correspondantes; elles ne créent pas la fixture :

```powershell
python -m pokemind meta deck-library --db $PublicFixture --as-of 2026-10-23 --json
python -m pokemind meta deck-knowledge --db $PublicFixture --reference-db $ReferenceFixture --selector 123:1 --as-of 2026-10-23 --set-aliases --json
python -m pokemind meta competitive-export --db $PublicFixture --event 123 --placement 1
python -m pokemind battle review-selected --db $PlayerFixture --deck invented --as-of 2026-10-23 --log-file $LogFixture --dry-run --confirm-owner-read --public-db $PublicFixture --reference-db $ReferenceFixture --set-aliases --json
```

Pour simuler l’import, remplacer `--dry-run` par `--apply` et ajouter
`--confirm-owner-import`. Attester ensuite **séparément** le battle-id retourné :

```powershell
python -m pokemind battle review-selected --db $PlayerFixture --deck invented --as-of 2026-10-23 --battle-id $InventedBattleId --version 1 --battle-date 2026-10-10 --apply --confirm-owner-read --confirm-owner-attest --json
```

Depuis la racine de cette fixture seulement, consulter les copies PUBLIC bornées :

```powershell
python -m pokemind meta public-identity-explain --as-of 2026-10-23
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --json
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --selector 123:1 --html
```

Les dates et confirmations sont simulées par le test; ces exemples historiques
ne permettent ni écriture antidatée réelle ni utilisation des données personnelles.

**Limites :** un seul match par scénario, résultats séparés, aucun taux de victoire
ou contre réel démontré, pas de collection/crédits ni de partie du propriétaire,
pas de test du client TCG Live ou du navigateur. Les preuves locales sont
`CODEX_LOCAL_REPORTED`; la CI certifie des tests synthétiques. Aucun bug produit
ne nécessite de correction dans ce lot. **V1 NOT_RELEASE_READY**, exigences A–J
inchangées; audit indépendant requis avant toute suite.
