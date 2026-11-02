# Vision locale optionnelle — LOT G

Au prévol Windows du 2026-10-14 : Pillow, OpenCV, pytesseract, exécutable
Tesseract, EasyOCR et ONNX Runtime non détectés. Aucune installation ni ressource
téléchargée. `PARTIAL_WITH_EVIDENCE` : le code et le contrat sont testés, aucune
reconnaissance de capture TCG Live n’est attestée.

Le nouvel adaptateur `pokemind_tesseract_roi_v1` accepte uniquement une image PNG
RGB/RGBA volontaire et un profil privé explicite. Les zones de texte sont découpées
localement, l’exécutable Tesseract reçoit les octets sur stdin sans shell, et les
résultats TSV sont validés. Langues permises : `eng`, `fra`, `eng+fra`. Aucun modèle
cloud, fichier temporaire d’image ou accès au jeu. Le décodeur refuse au-delà d’un
million de pixels; 12 zones au maximum et timeout de 10 secondes par zone.

Exemple de profil **synthétique**, à construire sous `data/local/` :

```json
{
  "schema_version": 1,
  "adapter": "pokemind_tesseract_roi_v1",
  "language": "eng+fra",
  "reference_size": [800, 600],
  "fields": [
    {"field": "name", "roi": [20, 20, 300, 40], "min_confidence": 0.95},
    {"field": "set_code", "roi": [20, 500, 100, 30]},
    {"field": "collector_number", "roi": [130, 500, 80, 30]},
    {"field": "hp", "roi": [600, 20, 100, 40]},
    {"field": "damage", "roi": [400, 300, 100, 40]}
  ]
}
```

`match observe --image IMAGE --calibration PROFIL --turn N --dry-run --json`
utilise ce contrat. Un backend absent rend `NEEDS_MANUAL_ANNOTATION` sans écrire.
Les zones sont mises à l’échelle seulement si le ratio d’aspect demeure cohérent.
Une ligne ambiguë, un score non fini/faible, un compteur illisible ou une identité
incomplète produit `unknown`. Le nom, le code TCG Online et le numéro doivent tous
concorder avec une impression locale sourcée; HP contradictoire interdit la
candidate. Ni nom approchant, ni couleur, ni icône inconnue ne prouve une identité.

Même avec concordance exacte, la provenance reste `ocr_uncertain`, l’emplacement
`ambiguous` et les actions non attestées. Aucune couleur ne code un nom de carte.
Phase et joueur actif restent inconnus; une annotation propriétaire distincte peut
confirmer ces faits. L’ancien adaptateur de marqueurs est conservé uniquement pour
ses tests d’architecture. Les tests du nouvel adaptateur utilisent des images de
cadres/glyphes/compteurs générées et un OCR simulé :
`verified_on_synthetic=false`, `test_contract_only=true`, aucun succès OCR inventé.

## Suite propriétaire séparée (LOT H)

1. Décider explicitement d’installer une pile locale et ses langues, après audit de
   la source, licence, version et taille; cette décision n’est pas acquise en G.
2. Exécuter le benchmark sur texte FR/EN réellement rasterisé avec jeux positifs et
   négatifs distincts, occlusion, résolution et cadrage. Mesurer erreurs par champ,
   taux d’abstention, CPU/mémoire et latence; aucun seuil arbitraire ne certifie une
   précision réelle. Le seuil 0,95 courant est un filtre conservateur non calibré.
3. Calibrer zones/seuils et corroborer identité, compteurs, énergies et état complet.
   Une étape échouée reste PARTIAL et ne promeut pas `visual_certain`.
4. Sur un autre ordre, faire un essai avec capture volontaire d’entraînement et
   trois décisions, puis relire corrections/mémoire. Aucun tournoi interdit,
   automatisation du client ou transfert réseau de pixels. Les fichiers originaux
   sont conservés par le propriétaire; PokeMind ne les supprime pas.
