# Vision locale H — corpus et preuves

2026-10-14 Québec (mesures UTC 2026-10-15). Aucun paquet ou modèle installé.
Tesseract, Pillow, OpenCV et ONNX Runtime absents dans l'environnement local.

`python -m pokemind match benchmark-ocr --json` construit **22 cas, 88 champs**
FR/EN en mémoire : police originale 5×7, accent visible, numéro, code et HP;
petits caractères, zoom, cadrage, inclinaison par cisaillement, bruit, occlusion,
mauvaise impression, numéro/HP incompatibles et identité inconnue. Les PNG sont
réellement rasterisés et décodables; aucun marqueur ne code le texte attendu.
Ce corpus volontairement simple ne représente pas une capture réelle du jeu.

Le benchmark appelle le vrai adaptateur Tesseract seulement s'il existe déjà.
Aucun runner TSV injecté dans ce parcours. Sans moteur :
`OCR_ENGINE_NOT_INSTALLED`, zéro champ tenté, erreurs/identités/taux d'abstention
non mesurés (`null` pour les taux), aucune précision annoncée. Les compteurs exacts
restent accompagnés de `attempted=0`. La latence mesurée du rasteriseur n'est pas
une latence OCR; le pic tracemalloc Python exclut le moteur enfant. CPU et mémoire
du moteur sont explicitement inconnus. Preuve agrégée :
`docs/evidence/lot_h_ocr_windows.json`. Le test d'OCR réel est ignoré si absent;
les tests de rasterisation et des garde-fous sont exécutés sans mock OCR.

L'adaptateur de reconnaissance existant conserve `ocr_uncertain` et `unknown` pour
les informations illisibles/cachées. La recherche d'impression filtre désormais
code+numéro dans SQLite avant comparaison FR/EN normalisée; nom et HP restent
contrôlés, sans équivalence inférée par le nom ni main adverse déduite.

## Revue locale volontaire

Les nouvelles commandes sont préparées pour des actes propriétaires distincts :

```text
match review --session SESSION --observation ID --verdict confirmed --scope owner_training --calibration-sha256 SHA --json
match review ... --apply --confirm-owner --json
match revoke-review --review ID --json
match revoke-review --review ID --apply --confirm-owner --json
```

La prévisualisation n'écrit rien. L'application exige une observation active exacte,
un SHA du profil et une confirmation. Stockage textuel privé dans `metadata` du
schéma 13 : séance, tour, contexte, digest de l'état, profil, verdict et date UTC.
Pas de pixels ni chemin d'image. Une correction invalide le digest précédent;
une révocation conserve l'audit. `match show` et `match advise` exposent les comptes
de revue. La sauvegarde/restauration conserve les événements de revue.

Une revue `owner_asserted` n'est jamais une calibration indépendante. Même trois
revues positives, des marqueurs synthétiques et un score OCR élevé ne peuvent
promouvoir `visual_certain` ni passer la porte V1. Les essais H sont synthétiques.

## Audit des briques et essai futur

[Tesseract](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE) est sous
Apache-2.0; le binaire et les données de langue choisis devront faire l'objet d'un
audit version/taille/origine séparé avant toute installation. Pillow, OpenCV et ONNX
ne sont pas des dépendances de H; leur licence/version et consommation exactes ne
sont pas attestées puisqu'aucun artefact n'est sélectionné. Le runtime H reste
Python standard/SQLite; aucune nouvelle dépendance, serveur ou framework.

Après ordres distincts : sélectionner/installer le moteur, benchmarker, calibrer
les ROI et tester trois tours d'une partie d'entraînement où l'aide est permise.
Tour 1 après l'adversaire : observation→revue des champs visibles→conseil et repli.
Tours 2 et 3 : nouvelle image volontaire après changement déterminant, correction
si nécessaire, conseil et relecture de mémoire. Refuser identité fausse, information
cachée inventée ou perte de provenance. Pas de capture furtive, cloud, clic,
overlay ou accès au processus du jeu. Ce parcours réel demeure BLOQUÉ.
