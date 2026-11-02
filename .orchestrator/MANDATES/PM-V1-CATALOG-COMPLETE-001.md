# PM-V1-CATALOG-COMPLETE-001 — catalogue descriptif TCGdex FR/EN

Ordre manuel actuel : « termine le catalogue complet ». Nouvelle tâche ciblée,
2026-10-22 Québec; ne réactive ni mandat historique ni solde de budget consommé.
L'audit précédent a accepté le code/CI et a fermé ses deux permissions ciblées;
la nouvelle instruction fournit le déclenchement manuel de cette seule tâche.

## Travail autorisé

1. Prévol Git sans perte, lectures de continuité et CI Windows/Ubuntu au HEAD exact.
2. Examiner les distributions publiques officielles TCGdex et leurs licences,
   structure, fraîcheur et volumes. Privilégier un snapshot non exécutable en lot
   s'il permet une ingestion complète vérifiable; jamais lancer du code amont.
3. Compléter le catalogue descriptif FR/EN dans un nouvel espace PUBLIC isolé,
   en réutilisant tables, validateurs, FTS et provenance. Aucun ancien cache arrêté
   rouvert ni copié. Préserver les textes réellement présents et absences par langue.
4. Corriger les obstacles techniques démontrés, tests synthétiques et validation
   de couverture, recherche/show hors ligne, idempotence et intégrité. Mesurer
   les champs manquants; pas d'exhaustivité absolue inventée ni de traduction FR
   fabriquée depuis EN. Catalogue descriptif distinct des normes officielles,
   équivalences de réimpressions, légalité ou support Live.
5. Publier seulement code/tests et résultats assainis, états cohérents et CI exacte;
   AWAITING_AUDIT puis STOP. V1 reste NOT_RELEASE_READY.

## Enveloppe de cette nouvelle exécution

Maximum50000requêtes HTTP TCGdex et30GET de découverte publique primaire,134217728octets
cumulés de corps lus; intervalle minimal0,5s. Ce sont des plafonds d'exécution
conservateurs retenus pour l'ordre courant, pas un réemploi des anciennes permissions.
Retries transitoires bornés : trois tentatives au plus par ressource avec backoff,
comptées dans le même budget, sans relance de run clos. Refus401/403/429,
challenge/protection, hôte inattendu, plafond ou échec réseau final : STOP source.
Pas de scraping privé, contournement, clé, paiement, image, clone Git intégral,
installation de dépendance opaque ou exécution de TypeScript téléchargé.
Toute archive éventuelle doit d'abord être mesurée, à chemins sûrs, sans liens,
lecture/décompression bornées; aucune extraction exécutable.

Aucune donnée personnelle, deck/partie/collection/crédits, ancienne campagne,
OCR, tâche Windows, sauvegarde, migration privée, purge ou merge autorisés.

La découverte du code/schéma primaire confirme GraphQL public POST /v2/graphql.
Seules des requêtes de lecture à modèle fixe sont permises, jamais mutation,
introspection générale ou contenu propriétaire. Les POST de lecture débitent la
même enveloppe50000 que les GET REST; aucun budget supplémentaire.

## Checkpoint API et voie indépendante

Le run API courant est fermé après349requêtes et30108183octets, HTTP503 final
pendant un repli REST français; aucun nouvel appel TCGdex ni reprise de ce run.
Les deux langues de sets et le scan anglais ont progressé. Ce STOP de la source
API n'annule pas l'examen indépendant du dépôt officiel GitHub déjà inclus au
point2 :27GET de découverte/10881497octets consommés,3GET encore disponibles.
L'arbre Git officiel non tronqué mesure43199blobs/82676026octets, dont45520021
sous data/. Autoriser dans la même enveloppe restante une archive épinglée au
commit déjà vérifié : maximum32MiB comprimés,192MiB de flux décomprimé; aucun
fichier sélectionné >128KiB. Ne retenir que les données textuelles et notices,
aucune image extraite/utilisée, aucun script/exécutable exécuté. Vérifier les
objets Git de tous les fichiers retenus et refuser chemins/liens/traversal.
Nouveau workspace PUBLIC distinct; aucune copie du cache API arrêté.

## Clôture de l'exécution — AWAITING_AUDIT

L'instantané officiel a été importé hors ligne dans un espace PUBLIC distinct :
23 864impressions/223extensions,23 771détailsEN/22 192FR,indisponibilités93/1 672,
zéro pending/erreur/périmé. Détails des champs incomplets et preuves dans
`../EVIDENCE_PM-V1-CATALOG-COMPLETE-001.md`. API toujours fermée après349requêtes;
découverte définitivement close à30GET/25 605 685octets,cumul55 713 868octets.
Le checkpoint27GET ci-dessus décrit un état passé, pas un reliquat réutilisable.
Permission consommée,execute_now=false; aucun nouvel import/téléchargement ou
mandat autorisé. STOP audit indépendant ChatGPT, V1 NOT_RELEASE_READY.
