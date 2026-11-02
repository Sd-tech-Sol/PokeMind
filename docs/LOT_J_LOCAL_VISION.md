# J0 — confiance OCR sous Windows

2026-10-15 UTC. État réel : `OCR_ENGINE_NOT_INSTALLED`. Aucun moteur, pack,
installateur ou paquet téléchargé/installé. Les 22 cas/88 champs du corpus H
demeurent rasterisés; précision, faux positifs, abstentions et latence OCR sont
inconnus tant qu'aucun moteur revu n'est exécuté. CPU/RSS moteur inconnus.

`match preflight` détecte seulement la présence d'un candidat PATH. Il ne l'ouvre
ni ne l'exécute; un candidat présent devient `OCR_BINARY_UNATTESTED`. Le benchmark
et l'observation avec profil OCR ont le même refus par défaut. La présence dans
PATH ne rend plus l'adaptateur disponible. Aucun changement au schéma 13.

Une politique JSON privée sous `data/local/`, choisie avec `--ocr-trust`, doit
décrire un chemin absolu local, version, architecture PE Windows, SHA-256 attendu,
URL HTTPS du distributeur, licence, revue explicite des dépendances et dossier
contenant les packs `eng`/`fra` avec leurs SHA attendus. Scripts BAT/CMD/PS1/COM,
UNC, flux ADS, reparse points/ancêtres redirigés, hardlinks, tailles excessives et
empreintes différentes sont refusés. Le JSON est lu au même handle que son hash.
Sans `--execute-reviewed-ocr`, même une politique valide ne lance aucun programme.

Après opt-in distinct, le prévol utilise uniquement le binaire épinglé, vérifie
version et liste des langues, impose le dossier tessdata et neutralise les
variables TESSDATA héritées. La politique, le binaire et les packs sont réattestés
avant/après chaque processus. La politique reste épinglée pendant le benchmark
et les ROI d'une observation. Aucun argument issu d'un texte OCR n'est exécuté.
stdout ET stderr sont bornés en mémoire (32 000 octets diagnostic, 256 000 OCR),
timeout 5/10 s, sans shell et sans fenêtre console; entrée PNG par pipe sans
fichier temporaire hors du projet. Aucun chemin ni stderr brut ne sort du diagnostic.

Ce mécanisme n'est pas un bac à sable : signatures Windows et ACL ne sont pas
validées, dépendances/DLL seulement déclarées revues, exclusion d'un remplacement
hostile entre contrôle et lancement non prouvée, descendants malveillants non
confinés. Un SHA mesuré n'atteste pas l'origine. `origin_attestation=operator_reviewed`,
`distribution_origin_verified=false`, `signature_status=unknown_not_checked`.
Il faut obtenir les empreintes attendues par une source de confiance distincte;
recopier les empreintes d'un téléchargement inconnu ne suffit pas.

Les tests J emploient un faux PE jamais exécuté pour la politique, et le Python
déjà utilisé par pytest pour éprouver les sorties excessives, timeout et arguments
littéraux. Ils ne prouvent aucune reconnaissance Tesseract. Les deux tests OCR
réels hérités requièrent désormais `POKEMIND_TEST_EXECUTE_REVIEWED_OCR=1` ET
`POKEMIND_TEST_OCR_TRUST` pointant une politique revue; ils sont exclus par défaut.

Les faux positifs H/I, mauvaises impressions/HP/numéros/langues, revues révocables
et anciennes certitudes sont conservés dans leurs suites. Aucun adaptateur réel
calibré indépendamment : `visual_certain_allowed=false`, conseils conditionnels,
aucune attaque certifiée par une annotation ou une lecture OCR seule.

Sources de préparation : [installation Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html),
[données de langues](https://tesseract-ocr.github.io/tessdoc/Data-Files.html).
La sélection précise du distributeur/version/licence/empreintes et le volume à
installer restent à fixer après décision du propriétaire; aucune permission
d'installation ne découle de ce document. Voir `VALIDATION_PROPRIETAIRE_V1_WINDOWS.md`.
