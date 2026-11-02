# Vision locale I3 — sélection préparée, aucune installation

Observation du 2026-10-15 UTC : `match preflight` retourne
`OCR_ENGINE_NOT_INSTALLED`, eng/fra absents, SHA/version et CPU/RSS inconnus.
Le benchmark H de 22 cas/88 champs rasterisés demeure disponible par
`python -m pokemind match benchmark-ocr --json`; aucune précision n'est attribuée
quand le moteur est absent. Les tests TSV injectés vérifient le contrat seulement.

Choix proposé après autorisation : Tesseract 5, Windows x 64, packs `eng` et `fra`
de `tessdata_fast`. Le projet décrit ces modèles entiers comme un compromis
vitesse/précision; leur licence est Apache-2.0. La documentation officielle
renvoie aux installateurs **tiers UB Mannheim** pour Windows; cela ne constitue
pas une signature ou une validation du binaire choisi. Sources consultées :
[installation officielle](https://tesseract-ocr.github.io/tessdoc/Installation.html),
[modèles officiels](https://github.com/tesseract-ocr/tessdata_fast),
[types de modèles](https://tesseract-ocr.github.io/tessdoc/Data-Files.html).

Version exacte du distributeur, architecture du PE, SHA-256 attendu de
l'installateur et des deux packs, taille disque et mémoire moteur : **unknown**.
Aucun fichier n'a été téléchargé pour les déterminer. Avant une installation
autorisée, fixer ces artefacts/version/URL immuables, vérifier les SHA et licences,
indiquer leur volume, puis obtenir l'ordre d'installation. L'architecture
`AMD64` du prévol désigne la machine, pas une analyse du binaire.
Le SHA éventuellement mesuré par `preflight` est celui de l'exécutable installé,
pas une preuve de chaîne d'approvisionnement. Les SHA des packs restent inconnus.

I renforce les identités candidates : nom + set + numéro + HP lisibles, langue
compatible et détail du catalogue non marqué périmé. Une langue étrangère au profil,
HP absent/contradictoire, mauvaise impression/numéro, score insuffisant, lignes
ambiguës ou catalogue futur/incomplet conduisent à l'abstention. Même une
correspondance exacte reste `ocr_uncertain`; aucune promotion de certitude,
légalité, contenu caché ou attaque assurée. Seuil de champ minimal 0,90,
défaut 0,95 : seuils techniques, **non calibrés empiriquement**.

## Essai propriétaire préparé, à ne pas exécuter implicitement

1. Autoriser séparément moteur/packs, benchmark raster puis calibration sur des
   captures volontairement fournies d'entraînement où l'assistance est permise.
2. Distinguer trois corpus : texte artificiel H; imitation synthétique de capture
   des tests de contrat; vraie capture autorisée. Rapporter exactitude par champ,
   abstentions, faux positifs d'identité, latence; CPU/RSS moteur restent inconnus
   sans instrumentation distincte. Aucune métrique synthétique n'est transférée
   automatiquement aux vraies cartes.
3. Ouvrir une séance training datée; observer au début du tour, faire confirmer
   les champs, donner séquence conditionnelle/repli/raison. Reprendre une image
   seulement après pioche/recherche/effet déterminant ou changement majeur.
4. Répéter trois décisions, noter corrections/erreurs/inconnues, faire auditer les
   preuves. SQLite garde le texte et les digests, jamais les pixels. Les fichiers
   sources restent sous le contrôle du propriétaire; aucune suppression implicite.

État : préparation technique testée; OCR mesuré et essai réel
`BLOCKED_WITH_REASON`. Revue `owner_asserted` et ancien `visual_certain` ne lèvent
aucune gate; `test_lot_h_vision.py` reste une régression obligatoire.
