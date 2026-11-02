# PM-V1-COMPLETION-001 — preuves techniques et limites

2026-10-22 Québec. **RAPPORTÉ_PAR_CODEX_LOCAL**, **AWAITING_AUDIT / PARTIAL**;
aucune certification indépendante, V1 **NOT_RELEASE_READY**.
La demande propriétaire vise la V1 complète; aucun critère de PROJECT_SPEC ou
de la matrice A–J n'est retiré. Les travaux ne rendent pas ses portes manquantes
facultatives.

## Prévol exact

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
- Fetch/pull ff-only sans perte :28a96b3873fe7a7fff1eae8d14452a269a943013 →
  7e21676b94262d62090741c99a8b865d50f9088d.
- [Actions39714543936](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39714543936)
  au SHA7e21676b94262d62090741c99a8b865d50f9088d : Windows119613405914 et
  Ubuntu119613406110 **completed/success**, avant tout travail fonctionnel.
- Continuité, adoption V2, état, premier NEXT_ACTION, HANDOFF/RESULT/DECISIONS,
  skill executor, PROJECT_SPEC, NEXT_PROMPT et mandat courant lus.
- La correction de l'audit précédent est conservée : format d'import réel
  FIELD_VALIDATED le2026-10-11; aucun nouvel essai d'import exigé.

## Corrections du produit

1. `show_deck`, `profile_summary`, `profile_review` ne migrent plus une DB lors
   d'une consultation. Anciennes tables absentes traitées sans création;
   profils calculés dans un même snapshot de lecture. URI SQLite encodée avec
   `as_uri`, `mode=ro` et `query_only=ON`, y compris noms contenant `#` et `%`.
2. Revue conservatrice **en mémoire** des événements équivalents entre parseurs :
   métadonnées et ordre des preuves conservés; au moins12 ancrages et3 tours,
   uniquement versions de parseurs différentes. Seule la pioche adverse anonyme
   exactement reconnue est ignorée. Aucun log/événement/attestation supprimé,
   fusionné, réimporté ou réattribué. Même échantillon pour profil, analyse,
   leçons et readiness; filtre temporel appliqué avant regroupement.
   Le résultat est explicitement **probable**, les comptes stockés sont visibles
   et aucun taux de victoire n'est donné si le regroupement est incertain.
3. Diagnostics TCGdex neutres, HTTP observé et réponses fermées. Les refus stricts
   restent terminaux; les erreurs n'exposent pas de corps ou exception brute.
   Client borné en octets cumulatifs et essais configurables; ancienne API et
   son plafond1000GET par appel conservés.
4. Lanceur de mises à jour avec DB PUBLIC explicite obligatoire; contrôle du
   namespace/marqueur/alias et tables privées avant l'update. Cadence/scheduler
   dry-run sans accès ni métadonnée de DB par défaut. Le marqueur n'est pas une
   certification cryptographique de n'importe quel contenu SQLite.
5. Runner manuel de collecte neuve, lots de100 sous une enveloppe commune;
  0,5 s minimum entre GET, y compris entre clients; aucun retry, redirection,
   reprise d'un dossier existant ou autre fournisseur. STOP source/local en
   code de sortie non nul. La présence du runner ne confère aucun consentement.
6. Confiance OCR étendue aux DLL locales et au support TSV épinglés, refus de
   DLL ajoutée/modifiée/alias. Version Windows avec préfixe `v` et suffixe de
   compilation acceptée seulement si la **version entière** égale la politique.
   Aucun relâchement des portes de calibration, certitude ou release.

Les gardes E2E réseau/processus/fichiers restent actives. Leur décodage d'URI
SQLite Windows a été corrigé et renforcé; une URI encodée hors fixture reste
interdite. Les deux seuls aperçus sans DB sont reconnus explicitement par la démo.

## Nouvelle collecte PUBLIC autorisée, maintenant arrêtée

Accord actuel explicite : « Autoriser cette collecte complète bornée ».
Cache vierge séparé, aucun accès aux anciennes campagnes ni à une DB personnelle.
Plafonds50 000 GET et134217728octets de corps lus, intervalle minimal0,5 s;
arrêt sur refus/challenge/erreur source/plafond/complétude observée.

| Observation de cette campagne seulement | Résultat |
|---|---:|
| GET tentés |199|
| Corps effectivement lus |1864262octets|
| Pages valides |198|
| Sets : membres EN / FR |220 /202|
| Union des sets découverts |223|
| Cartes : membres EN / FR |9500 /9500|
| Union des impressions |10303|
| Détails cartes EN / FR présents |0 /0|
| Détails sets présents |0|
| Détails connus restant à demander |21052|
| Normes officielles ajoutées |0|

Les scans sets ont une fin observée et confirmation vide. Les scans cartes
restent partiels; pas de dénominateur courant mondial ni ratio complet.
STOP au GET199 : **HTTP503**, scope `cards:en`, page96.
`SOURCE_STOP`, `TCGDEX_HTTP_503`; aucun retry après cette réponse et aucun GET
de cette campagne après STOP. Aucun refus401/403/429 constaté dans ce run;
la cause interne du503 n'est pas connue. **L'échec historique distinct reste
UNKNOWN** : ce résultat ne le reconstruit pas.
Les49 801 GET non consommés ne permettent pas une reprise d'un run arrêté.
Base/rapports bruts conservés localement, aucun binaire/image ni DB dans Git.

Diagnostic technique distinct antérieur à l'accord large : **1 GET**, page27 EN,
HTTP200 et100 membres acceptés en mémoire seulement. Il ne fait pas partie des
199 GET de cette campagne et n'a rien importé. Les anciens budgets ne sont jamais
additionnés à celui-ci.

## OCR portable autorisé, preuves d'extraction

Accord actuel explicite : « Autoriser OCR portable et tests ».
Les cinq fichiers publics épinglés de [V1_COMPLETION_STATUS](../docs/V1_COMPLETION_STATUS.md)
ont été téléchargés : **34082807octets**, sous64 MiB. Sources canoniques et digests
de release/objets Git contrôlés; aucun installateur lancé.
`7zr.exe` vérifié a extrait uniquement le moteur d'archive et sa licence;
`7z.exe` vérifié a listé puis extrait les composants OCR sélectionnés.
Inventaires contrôlés avant extraction : chemins relatifs, pas de traversal,
ADS, lien ni réutilisation d'un dossier existant. **105390675octets** de payloads
portables extraits/copiés, sous160 MiB.

Revue locale : moteur AMD64 et55 DLL AMD64, imports statiques fermés sur les DLL
fournies et19 bibliothèques système Windows connues, aucun delay-import déclaré.
Pas d'outil de formation, plugin NSIS, désinstalleur ou JAR exécuté. Licence
Apache2.0 moteur/modèles relue, licence7-Zip relue; bibliothèques embarquées sous
licences amont distinctes, aucun binaire redistribué dans Git.

Empreinte du **binaire public extrait** Tesseract :
`c66f0f12ed76f6aa455dac97684bbc86756d6a732380bee09122454cfda3f420`.
Version réellement répondue : `5.5.3.20260724`, packs `eng` et `fra` disponibles.
Le prévol initial a refusé le suffixe de compilation; vérification corrigée
avec régressions d'égalité exacte, puis prévol `OCR_INSTALLED_UNCALIBRATED`.
Politique et chemins d'exécution locaux hors Git; aucun de leurs hachages publié.

Origine **operator_reviewed**, signatures non contrôlées et dépendances non
indépendamment auditées. Une empreinte de release n'est pas une signature ni
une preuve d'absence de vulnérabilités. Aucun PATH, registre, tâche Windows,
jeu, image réelle ou donnée personnelle touché.

Benchmark réel22 cas/88 champs : **0 champ accepté,88 abstentions,0 identification
positive**, seuil95% inchangé,0 mock/0 réseau/0 image persistée. Zéro faux positif
dans un test qui refuse tout ne prouve pas la qualité. Les quatre diagnostics
supplémentaires sur texte propre révèlent des glyphes erronés à faible confiance;
le parseurTSV reçoit correctement les sorties, pas d'erreur d'adaptateur observée.
Corpus public original5×7, empreinte
`09d654750687173554c6e17054e62a603b9862fbd987968e885a655ceb6310c5`.
Durée339,056 s; médiane3,814 s/champ incluant vérification d'empreintes et processus,
sous charge de tests concurrente; picPython105922335octets. CPU/RSS enfant non
mesurés. Pas de calibration sur cartes réelles ni de certitude promue.

## Validation et publication

- Suite intermédiaire587 passed / 3 skipped avant derniers flags de bilan provisoire
  et avant enveloppe de collecte/OCR portable; ne pas la présenter comme finale.
-44 tests ciblés après limites de corps/version/DLL/échantillon : réussis.
- Prévol `RUNTIME_READY`, Python3.13.15/SQLite3.50.4/FTS5, aucun réseau/DB/écriture.
- Démo finale `SYNTHETIC_REHEARSAL_PASSED`,79 CLI/13 checkpoints/10 citations,
  tous dans un workspace synthétique supprimé normalement; aucun accès personnel.
- Suite complète locale avec opt-in OCR : **605 passed / 1 skipped en680,53s**.
  Le seul skip concerne la création de lien symbolique non permise localement.
  Les deux tests OCR facultatifs sont réellement exécutés, sans mock.
  Deux tests d'enveloppe ont ensuite été ajoutés et le STOP de phase détails sur
  plafond d'octets précisé; suite ciblée finale **9 passed**. Ces changements sont
  aussi soumis à la suite complète CI du HEAD de livraison.
- Compilation/diffcheck réussis. Hygiène revue après préparation explicite des
  seuls fichiers non sensibles. CI de livraison à contrôler après push, au SHA
  contenant ces preuves; la CI initiale7e21676 n'en est pas la preuve finale.
- Hygiène finale :306 fichiers suivis,36 chemins explicitement préparés, aucun
  contenu local privé/binaire dans l'index. Deux anciens chemins absolus déjà
  présents dans une archive NEXT_ACTION sont caviardés, portée historique intacte.
  État/ID/STOP et permissions consommées cohérents dans les documents préparés.

Un nettoyage de deux dossiers de fixtures synthétiques a été refusé par la
validation automatique (`blocked by policy`). Aucun contournement; les dossiers
ignorés sont conservés. Aucun effet sur les données personnelles ou Git.

## Limites de fin V1, inchangées

Catalogue/détails, normes complètes/errata/réimpressions/Live, sources méta à
qualifier et TrainerHill, calibration puis3 décisions sur captures d'entraînement,
activation réelle du planificateur avec opt-in et audit, récupération/ACL/
chiffrement/exclusion/durabilité, attestations personnelles et audit indépendant
restent à résoudre. Heures retenues :08:15 quotidien, 19:30 mardi/vendredi,Toronto;
préférence de préparation seulement, aucune installation consentie.
Nouvelle sauvegarde/migration/purge toujours interdites. Aucun assouplissement
de gate ni déclaration de V1 complète pour fermer artificiellement la demande.
