# Preuves — PM-V1-PUBLIC-EVIDENCE-HTML-VIEW-001

**CODEX_LOCAL_REPORTED / AWAITING_AUDIT. V1 NOT_RELEASE_READY.**

## Prévol autorisant

Lancement manuel propriétaire; NEXT_PROMPT et mandat complet lus, état READY
concordant. Synchronisation **fast-forward sans perte**, un commit de
`5c53e6d1c785f06e09892788cec1ffc271671a21` vers
`45a5f27bb5071c3fe40780beafa04d250ae08caf`, branche
`work/pm-v1-lotj-final-readiness-windows`, aucun changement suivi préexistant.
Aucune commande de découverte de noms ni inventaire des fichiers non suivis.

Avant travail fonctionnel, [CI40052916830](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40052916830)
au SHA autorisant exact : **completed/success**, Windows job120749323210
**1111 réussis/2 ignorés**, Ubuntu job120749323348 **1110/3**.
Neuf marqueurs hérités contrôlés dans chaque log; SHA exact et run40052916830
dans les huit objets JSON, SHA exact dans `ci_evidence` (ce marqueur ne contient
pas de champ run). Empreintes JSON canoniques des deux registres égales entre OS.
Les logs GitHub sont la preuve CI; ils ne certifient aucune opération du PC.

## Produit livré

Option `--html` mutuellement exclusive avec `--json` sur la commande existante
`meta public-identity-explain`. Même appel `identity_explain`, même projection,
mêmes deux SQLite fixes read-only, même branche avant recherche de racine ou
sélection de DB personnelle. Aucun nouveau moteur, cache ou contrat JSON.

Document UTF-8 complet sur **stdout seulement**, assemblé avant émission.
Tableaux du cache complet et de la sélection, couverture par composition,
navigation par fragments générés, sections natives `details/summary`, lien
d’évitement, légendes/en-têtes de tableaux et focus visibles. Matrice d’identités
avec candidats descriptifs, sources datées comme texte brut, blocages et preuves
nécessaires séparés présentiel/Live. Le rendu ne choisit aucune édition et ne
calcule aucun nouveau verdict de légalité.

Valeurs dynamiques échappées dans des nœuds texte; aucun attribut provenant
des caches. CSP `default-src 'none'; style-src 'unsafe-inline'; base-uri 'none';
form-action 'none'`. Aucun script, ressource externe, URL réseau navigable,
formulaire ou serveur. Les URLs avec identifiants/paramètres restent masquées.
Les erreurs de lecture produisent une page complète neutre, code retour2,
sans chemin ni traceback; le conflit d’options est refusé par argparse avant
lecture, sur stderr. `SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE`, les deux
plateformes `unknown` et `NOT_RELEASE_READY` restent visibles, même sans contenu.

## Tests et QA locale

**74 tests ciblés réussis en17,95s : 45 hérités +29 nouveaux.** Premier passage
70/70 en15,95s, puis quatre cas supplémentaires adverses/vide et passage final
74/74. Aucun échec de test ni retry de lecture échouée dans ce lot.

Collecte locale explicite des seuls `tests/test_public_identity_rules_scoped.py`
et `tests/test_public_evidence_explain_cli.py`, sans collecteur de répertoire,
avec `pytest_collection` construisant les deux `pytest.Module` littéraux.
`--noconftest`, `--import-mode=importlib`, `-p no:cacheprovider`, configuration
`-c pyproject.toml -o addopts=`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
`PYTHONDONTWRITEBYTECODE=1`, `POKEMIND_TEST_OFFLINE=1`.
Fixture locale injectée : répertoires neufs inventés exclusivement dans l’espace
synthétique ignoré; conservés sans suppression ni nettoyage additionnel.
Aucun autre test/conftest/dossier local découvert. La collecte normale complète
est réservée aux environnements CI GitHub isolés.

Les29cas couvrent : vraie entrée `python -m pokemind`, HTML complet/filtré,
égalité des totaux et blocages avec JSON, reprise identique, démarrage CP1252
puis UTF-8 strict, non-mutation, cache absent/sélecteur inconnu, mauvais
paramètres, conflit HTML/JSON, données malformées, document sans contenu,
liens internes valides, éléments clavier et CSP. Texte hostile inventé dans
les caches et dans **tous** les champs textuels projetés, candidats inclus;
aucune balise/attribut actif créé, champs bruts hors projection non rendus.
URLs avec paramètres/identifiants et dates hostiles couvertes.
Les sous-processus protégés refusent toute découverte, réseau, écriture ou
ouverture hors des deux SQLite après préchargement du code statique.

Syntaxe/compilation en mémoire et tabnanny sur les trois fichiers Python
nommés, hygiène des seuls fichiers préparés et `git diff --check` réussis.
Un premier contrôle maison trop large a signalé des espaces de fin de ligne
historiques dans DECISIONS, hors diff. Le contrôle a été borné aux lignes
ajoutées, sans réécrire les archives; ce signal n’est pas un échec de test produit.
Ni prévol/démo générique ni suite locale générale susceptibles de découvrir
des fichiers additionnels exécutés. Aucun paquet installé.

## QA des deux caches PUBLIC du PC — déclarative

**Cinq processus CLI frais**, sous CP1252, UTF-8 décodé strictement : HTML
complet, JSON complet, HTML581:1, JSON581:1, reprise HTML581:1.
Garde d’audit identique aux tests : ouvertures limitées aux deux chemins SQLite
fixes, URIs `mode=ro&immutable=1`; tout autre fichier/DB, découverte, réseau ou
écriture refusé après import statique; routes racine/DB par défaut interdites.

**CODEX_LOCAL_REPORTED** : 32 placements/28 compositions HTML et JSON,
158/168 identités listées uniques,626/698 lignes et1439/1680 copies résolues.
Filtre581:1 :3placements/1composition,21/24 lignes,51/60 copies.
Reprise HTML identique;10 identités encore inconnues,28unknown présentiel et
28unknown Live, tous les blocages conservés. Les deux fichiers SQLite ont
les mêmes octets et métadonnées avant/après; aucune empreinte de cache publiée.
0GET, aucune page/ledger/marqueur ni donnée personnelle consultée.
Aucun document HTML écrit sur disque, aucun navigateur ouvert.

Ce contrôle est une observation locale, **pas une certification indépendante**
du PC, de la provenance des listes, des règles ni de l’exclusion d’écrivain
concurrent. La structure clavier est vérifiée par parseur; aucun essai réel
de navigateur `file://`, lecteur d’écran ou rendu visuel n’est attesté.
Le guide explique seulement la sauvegarde/ouverture **manuelle distincte**
de l’utilisateur; aucune action de fichier/OS supplémentaire effectuée.

## Livraison et audit

[Guide de consultation](../docs/PUBLIC_EVIDENCE_HTML_VIEW.md).
Rapports/state cohérents : **AWAITING_AUDIT, execute_now=false, consumed=true**.
Audit indépendant ChatGPT demandé depuis
`45a5f27bb5071c3fe40780beafa04d250ae08caf`, au HEAD distant final et dans ses
deux jobs CI. Les29nouveaux cas doivent être collectés dans la suite complète.
Les neuf marqueurs hérités et les deux empreintes JSON canoniques concordantes
restent exigés. CI finale **PENDING_UNTIL_PUSH** lors de l’écriture du commit;
l’exécuteur attend et contrôle les deux jobs au SHA livré avant sa réponse.
Les résultats Actions attachés à ce SHA sont les preuves durables de livraison,
distinctes de la CI initiale et des déclarations sur le PC.

Aucune certification V1, porte A–J promue, nouvelle permission privée,
opération jeu/clipboard/OS/OCR/scheduler/backup/restauration/migration/purge,
merge ou nouveau mandat. **STOP audit ChatGPT. V1 NOT_RELEASE_READY.**
