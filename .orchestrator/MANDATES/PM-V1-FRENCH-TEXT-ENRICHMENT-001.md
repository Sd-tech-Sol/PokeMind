# PM-V1-FRENCH-TEXT-ENRICHMENT-001 — textes français du catalogue occidental

Ordre manuel propriétaire courant : rechercher soi-même sur Internet les textes
français manquants; aucune carte japonaise demandée. Cette tâche nouvelle ne
réactive aucun budget TCGdex ou ancienne campagne arrêtée. V1 NOT_RELEASE_READY.

## Portée autorisée

1. Prévol sans perte, continuité et deux CI au HEAD exact. Base de départ ec67dd7,
   Actions39814584101 Windows119949630281 et Ubuntu119949630041 completed/success.
2. Lire uniquement le catalogue PUBLIC complet attesté
   data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3 pour
   inventorier les lacunes : noms, descriptions, effets, attaques et talents FR.
   Une absence de fiche française ne prouve pas une absence d'impression française.
3. Découvrir et qualifier les sources françaises publiques : auteur, licence,
   conditions, fraîcheur, API/distribution, correspondance exacte set/numéro/carte.
   Récupérer les textes admissibles avec URL/version/date, sans écraser le texte
   natif ni confondre traduction, réimpression, édition française ou légalité.
4. Intégrer les compléments dans le seul cache PUBLIC avec provenance distincte,
   tests synthétiques, consultation hors ligne, décompte exact avant/après et
   intégrité. Aucun nom/effet traduit automatiquement présenté comme officiel.
   Préférence confirmée : seuls textes français déjà publiés/sourcés, aucune
   traduction générée par l'agent. Une description d'une autre impression peut
   être référencée distinctement si le paragraphe anglais et les identifiants
   nationaux du Pokémon sont identiques; aucune équivalence fonctionnelle déduite.
5. Publier code/tests/agrégats assainis et orchestration cohérente, CI exacte,
   puis AWAITING_AUDIT/STOP. Aucun corpus téléchargé ni texte de cartes dans Git.

## Bornes nouvelles

Découverte :40 recherches/ouvertures Web,40 GET directs primaires maximum.
Acquisition :4000 GET de données,128MiB de corps lus cumulés,1seconde minimale
entre appels à un même fournisseur, réponses individuelles <=4MiB. Un essai
par ressource; arrêt du fournisseur sur refus401/403/429, challenge/protection,
erreur réseau finale, plafond ou conditions incompatibles. Aucun contournement,
compte, clé, paiement, serveur privé, OCR/exécutable ou installation de dépendance.
Pas de nouveau GET TCGdex API, pas de réouverture/rejeu des campagnes arrêtées.
Le catalogue PUBLIC achevé peut être consulté/enrichi sans recopier ses anciens
journaux réseau. Les sources brutes et reçus restent hors Git dans un espace
PUBLIC propre à cette tâche. Toute limite réelle est publiée honnêtement.

Aucune base personnelle/deck/journal/collection, sauvegarde, migration privée,
restauration, purge, OS/scheduler, jeu ou donnée japonaise. Pas de merge/force push,
audit indépendant ni certification release par l'exécuteur.

## Préférence propriétaire confirmée

« Non, seulement du français déjà publié et sourcé ». Aucune traduction générée
par l’agent. Les traductions communautaires déjà publiées sont admissibles avec
leur attribution, sans les présenter comme du texte officiel ou une édition FR.
