# Preuves — PM-V1-SYNTHETIC-PLAYER-JOURNEY-001

**CODEX_LOCAL_REPORTED / AWAITING_AUDIT. V1 NOT_RELEASE_READY.**

## Prévol et permissions

Lancement manuel propriétaire; NEXT_PROMPT et mandat entièrement lus,
STATE/mandat concordants, issue#1 consultée comme contexte produit, pas comme
permission d’exécuter ses anciennes étapes. Synchronisation ff-only sans perte,
un commit de `6ceb8e5e6de38d9b06febbe6647ca72638919b05` vers
`9e7d041365f13751e63cd449c1e45344e2dd2f90`, arbre suivi initialement propre.

[CI40056717275](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40056717275)
du HEAD READY exact attendue avant travail fonctionnel : **completed/success**,
Windows job120761189325 **1140 réussis/2 ignorés**, Ubuntu job120761189393
**1139/3**. Neuf marqueurs contrôlés par log, huit objets JSON au SHA/run exacts
et `ci_evidence` au SHA exact; les deux empreintes JSON canoniques concordent.

Ce lot autorise exclusivement des fixtures inventées. **Aucun vrai cache PUBLIC,
DB personnelle, deck, journal, collection, compte ou presse-papiers lu.**
Aucun GET, navigateur, client, OCR, scheduler, backup, migration, installation,
scan/liste de fichiers ou nettoyage additionnel. Les commandes Git/GitHub
servent à la synchronisation, aux preuves et à la livraison autorisées.

## Livrable fonctionnel

Nouveau `tests/test_synthetic_player_journey.py` : **18 cas** traversant les
moteurs existants, avec une fixture cohérente et un test intégrateur principal.
Bibliothèque6placements/4compositions → export60 et guide sourcé → défaite FR
explicitement sélectionnée → aperçu sans écriture → import séparé/idempotent
→ attestation v1/date → adversaire partiel/proxy PUBLIC → 4contre-plans exacts60
avec protocoles conditionnels → hypothèse retirée/réouverte → version retirée
et corrigée v2 → statistiques séparées sans amélioration causale démontrée.

L’aperçu compte0partie; l’import en compte1 et ne confirme aucune version.
Une nouvelle attestation est nécessaire. La correction ne crée pas un nouveau
match. `Synthetic Delta` est la seule carte adverse visible, quantité minimale1;
`Hidden Creature` piochée est exclue. Le proxy60 n’est jamais le deck adverse
exact. Les4alternatives sont reparsées à60 et leurs différences conservent
le total. Matchup, crédits, disponibilité Live, K.O. conditionnels et causalité
restent inconnus selon les contrats existants. Un seul match par scénario;
W/L/inconnu sont testés séparément en FR/EN, sans winrate sur petit n.

Deux copies **fictives** des SQLite PUBLIC de la même fixture alimentent le
lecteur borné : humain/JSON/HTML,6placements/4compositions, filtre123:1 et
reprise HTML identique. Totaux filtrés, sélecteurs et blocages comparés.
SOURCE_UNREVALIDATED/BLOCKED_SOURCE_SCOPE et unknown présentiel/Live conservés.
Les moteurs utilisant les pages fictives ont une portée distincte du lecteur
deux-SQLite, qui ne consulte pas ces pages et ne promeut pas leur provenance.

Les vues PUBLIC utilisent huit processus CLI frais CP1252 → UTF-8 strict dans
les deux cas (complet/filtré, trois vues puis reprise HTML). Garde d’audit existant
refusant toute autre ouverture de données/DB, découverte, réseau ou écriture.
CLI de revue humaine/JSON également testée, routes de sélection implicite
interdites et erreurs sans fuite de chemin. Aucun HTML enregistré ni navigateur.

Cas négatifs : trois consentements distincts et combinaison import/attestation
refusés avant toute métadonnée; texte natif manquant ou futur rend le guide et
les mécaniques du contre-plan incomplets; sans paire PUBLIC, famille et plan
restent inconnus/absents. Aucune nouvelle architecture ou correction produit :
**aucun bug d’intégration démontré nécessitant un changement moteur**.

## Confinement et reproduction

La liste de60 est une constante inventée dans le nouveau test. L’entrée statique
de l’ancien constructeur est interceptée en mémoire avant utilisation; aucun
deck préexistant n’est lu. Les helpers existants fabriquent uniquement pages,
ledger, catalogue et DB fictifs. Tout est dans une fixture neuve.
Les compteurs du ledger de fixture décrivent la simulation, pas des GET exécutés.

Garde des moteurs : SQLite seulement dans la fixture ou en mémoire, ouvertures
de données et toutes écritures limitées à la fixture; seuls imports de code
admis en dehors. `glob/rglob/iterdir/listdir/scandir/walk`, accès fournisseur et
clipboard interdits. Non-mutation des caches fictifs contrôlée en lisant seulement
les chemins SQLite/marker/ledger littéraux et les pages référencées par le ledger
**inventé**, sans recherche de noms. Aperçu et CLI de revue ne modifient pas
la DB fictive; les écritures d’import/attestation concernent cette DB seulement.

Collecte locale : trois `pytest.Module` de chemins littéraux
`test_synthetic_player_journey.py`, `test_public_identity_rules_scoped.py`,
`test_public_evidence_explain_cli.py`; aucun collecteur de répertoire/conftest
ou plugin externe. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, bytecode désactivé,
`POKEMIND_TEST_OFFLINE=1`, `--noconftest -p no:cacheprovider --import-mode=importlib
-c pyproject.toml -o addopts=`. Fixtures conservées dans l’espace synthétique
ignoré; aucun nettoyage supplémentaire ni lecture d’anciens résidus.

[Guide reproductible et commandes](../docs/SYNTHETIC_PLAYER_JOURNEY.md).
**92 tests ciblés réussis en45,87s :74hérités +18nouveaux.** Passages précédents
87/87 en39,46s et90/90 en42,21s, puis ajout de cas CLI et passage final92/92.
Aucun échec de test. Compilation en mémoire/tabnanny du nouveau fichier,
hygiène des fichiers préparés, liens nouveaux et diffcheck réussis.
Suite locale générale non exécutée pour respecter l’interdiction de découverte.

## Livraison et limites

Code produit inchangé; tests d’intégration, guide et orchestration assainie
livrés. Full CI GitHub Windows/Ubuntu au **SHA final** requise :18tests de plus,
neuf marqueurs hérités SHA/run et deux empreintes canoniques égales. CI finale
**PENDING_UNTIL_PUSH** à l’écriture du commit; l’exécuteur attend et contrôle
les deux jobs avant son compte rendu final. Actions attaché au SHA livré est
la preuve durable finale, distincte du prévol et des déclarations locales.

La CI certifie des fixtures inventées, ni le PC ni des données réelles. Aucun
test propriétaire, légalité réelle, efficacité de contre, client, navigateur ou
accès collection/crédits démontré. Les portes A–J ne sont pas promues.
**AWAITING_AUDIT, execute_now=false, consumed=true. STOP audit ChatGPT** du diff
depuis `9e7d041365f13751e63cd449c1e45344e2dd2f90`, du HEAD distant et de ses deux
jobs finaux. Aucun mandat suivant. **V1 NOT_RELEASE_READY.**
