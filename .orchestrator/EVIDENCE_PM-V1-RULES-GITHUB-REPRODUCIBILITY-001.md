# PM-V1-RULES-GITHUB-REPRODUCIBILITY-001 — preuves assainies

2026-10-22 Québec. Correction manuelle demandée par le propriétaire.
**AWAITING_AUDIT**, V1 **NOT_RELEASE_READY**.

## Problème et résultat

Le registre Git contenait16assertions recomptables, mais aucune reproduction
spécifique en CI de leur chargement SQLite et des exemples de décision. L'audit
historique avait correctement réservé les opérations du PC à Codex local.

`tests/test_rules_versioned_registry.py` charge maintenant les **deux registres
versionnés inchangés** dans une SQLite synthétique neuve. Il compare toutes les
assertions SQL et la règle de structure avec leur JSON, contrôle les références
de sources, retrouve15sources/22assertions/1règle, vérifie intégrité/FK et stabilité
des lignes normatives au rechargement. Le timestamp de chargement est exclu :
aucune idempotence d'octets d'import n'est revendiquée.

Sans catalogue, le cas Super Bonbon reste unknown/PRINTING_NOT_FOUND_LOCAL.
Six impressions minimales sont ensuite insérées **comme fixtures synthétiques**,
sans cache existant ni texte de carte téléchargé. Huit décisions sont vérifiées :

| Impression | Format/plateforme/date | Résultat contrôlé |
|---|---|---|
| sm1-129, swsh2-154 | Standard présentiel2026-10-22 | legal par équivalence explicite |
| me01-125, me01-114 | Standard présentiel2026-10-22 | legal sous les entrées de fixture |
| sm5-114 | Étendu présentiel2026-10-22 | not_legal, restriction explicite |
| sv07-086 | Standard présentiel2026-10-22 | unknown, disponibilité par impression manquante |
| me01-125 | Standard Live2026-10-22 | unknown, restrictions client non couvertes |
| me01-125 | Standard présentiel2026-10-23 | unknown, fenêtre normative expirée |

Les huit lectures gardent octets/mtime de la seule SQLite synthétique inchangés;
possession, fabrication et support Live restent unknown. Le test interdit sockets,
résolution réseau, processus externes et toute connexion SQLite autre que sa
fixture neuve. Aucune base existante n'est consultée.

## Preuve GitHub reproductible

Le test inscrit une propriété JUnit `public_rules_reproduction` seulement après
tous ses contrôles. Le publieur CI existant exige cette propriété unique, les
totaux, huit résultats et empreintes SHA256 des deux fichiers PUBLIC du checkout.
Il refuse une preuve absente/doublonnée/incohérente, un faux statut de base locale
vérifiée, une empreinte ou décision modifiée et une suite en échec. Il publie un
ensemble de champs autorisés, sans recopier de texte JUnit supplémentaire.

Les deux jobs Windows/Ubuntu de la CI normale exécutent ce test hors ligne puis
publient `rules_registry_evidence` et un résumé liés au **SHA testé**. Le journal
explicite `local_database_verified=false`, `source_documents_revalidated=false`
et `competitive_data_acquired=false`. Un résumé Git ou un nombre de tests verts
ne remplace pas ce contrôle exécuté.

Reproduction locale depuis le dépôt :

```powershell
python -m pytest -q tests/test_rules_versioned_registry.py --junitxml=data/local/ci/rules-reproduction.xml
```

## Prévol et validation

Arbre initial propre, fetch/pull ff-only sans perte de884a956 vers
885f01e054eb92eb0f9ac200a9137d53e0d9e756. Attente sans travail fonctionnel pendant
le job Windows; Actions39865516511, Windows120126602088/Ubuntu120126602540
completed/success au SHA exact avant exécution. Instructions, continuités,
état/premier mandat, rapports/audit, PROJECT_SPEC et skills executor/knowledge lus.

Tests ciblés : **22 passed**. Suite complète locale : **729 passed /3 skipped en
328,13s**, Python3.13.15. Deux skips OCR sans opt-in et un symlink Windows local
non permis, limites déjà connues. Compilation, hygiène et diff contrôlés;
dernier contrôle après staging.
CI de livraison : vérifier deux jobs completed/success au HEAD exact **contenant
ce rapport**, distinct du prévol885f01e. Les logs portent SHA, compteurs, empreintes
PUBLIC et décisions; aucun fichier SQLite ou JUnit n'est versionné.

## Limites préservées et STOP

Le test reproduit le **chargement du registre réel versionné** et le comportement
du moteur sur des impressions synthétiques. Il ne certifie pas les identités
TCGdex, le contenu des PDF, les écritures historiques, l'intégrité ou les résultats
de la base du PC. Ceux-ci restent **CODEX_LOCAL_REPORTED**. L'audit ChatGPT précédent
est conservé sans extension de son verdict.

Les véritables listes et résultats compétitifs restent **NOT_ACQUIRED**; zéro
nouveau GET fournisseur, aucune ancienne campagne reprise, aucune donnée privée,
OCR/OS/client, sauvegarde/migration privée/restauration/purge/merge. La proposition
PM-V1-COMPETITIVE-DECKLISTS-BOUNDED reste distincte et non exécutée.
AWAITING_AUDIT, permission de correction consommée, STOP audit indépendant ChatGPT.
