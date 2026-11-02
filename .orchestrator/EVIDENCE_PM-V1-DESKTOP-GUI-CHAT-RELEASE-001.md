# PM-V1-DESKTOP-GUI-CHAT-RELEASE-001 — preuves de livraison A–F

2026-10-26 — **CODEX_LOCAL_REPORTED**, livraison soumise à audit indépendant. Les observations sur le PC ne sont pas certifiées par GitHub. **V1 NOT_RELEASE_READY** pour les portes indépendantes restantes. Synchronisation ff-only sans perte à `92677989a2216e5df478d4f2563ed97eab9425a1`; [CI initiale40266454542](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40266454542) deux jobs success, Windows1314/2 et Ubuntu1313/3, neuf marqueurs et registres canoniques concordants.

Application PySide6 native à six rubriques et panneau chat, API PokeMind existantes, lecture canonique et Learning Loop, bibliothèque PUBLIC et versions personnelles exactes60, recherche FR/EN et règles datées. Aucun second cerveau. Processus Codex App Server stdio géré, outils système désactivés, outil de consultation PokeMind borné; Claude Code stream-json et Ollama loopback sous contrat commun. Préférences et historiques privés atomiques, consentement cloud mémorisé; contexte public seul pendant les essais réels.

Venv locale Python3.13, PySide6 **6.12.0**, PyInstaller **6.22.3**, pytest **9.1.1**, tzdata **2026.5** Windows; origine PyPI et licences revues, notices copiées au portable. WebEngine/PDF/QML exclus, bibliothèques Qt dynamiques remplaçables. Backend de wheel adapté aux sous-packages et extras, installation editable exercée. [Avis](../docs/DESKTOP_THIRD_PARTY_NOTICES.md).

| Vérification Windows locale | Résultat rapporté |
|---|---|
| Fenêtre native visible, six rubriques fonctionnelles | Réussi |
| Vrai rapport conservé, mémoire et chronologie d'un matchup consultés | Réussi |
| Copie d'une référence vérifiée à exactement60 cartes | Réussi |
| Recherche FR et fiche de carte du catalogue réel | Réussi |
| Codex0.163.0 App Server stdio : deux tours même fil et streaming | Réussi |
| Fermeture/réouverture et reprise du fil Codex | Réussi |
| Interruption d'un vrai tour Codex depuis l'interface | Réussi |
| Claude2.1.310 CLI : réponse puis reprise réelle d'une session | Réussi |
| Portable EXE compilé puis exécuté, Qt windows/frozen/visible | Réussi |
| Fenêtre native EXE observée avec handle Windows non nul | Réussi; lancement interactif visible |
| Ollama : sélection et diagnostic d'absence | Réussi; pas de réponse locale réelle |

La QA réelle utilise uniquement des questions et du contexte publics côté cloud; aucun agrégat propriétaire ni journal brut envoyé. Captures de notre fenêtre, historique et identifiants restent sous `data/local/desktop-dev` et `data/local/chat`, hors Git. Contrôle Windows externe indisponible après reprises prescrites par son skill : Qt/QTest, signaux et capture de notre propre fenêtre utilisés. Aucune vérification indépendante du PC revendiquée. Ollama : **BLOCKED_EXTERNAL_DEPENDENCY** sur ce PC, service absent; protocole testé contre HTTP loopback inventé, aucun modèle installé.

**180 tests ciblés réussis :39 nouveaux,141 hérités**, modules explicites `test_desktop_services`, `test_assistant_providers`, `test_desktop_qt`, `test_battle_coach`, `test_legacy_batch_bridge`, `test_battle_batch`. Fixtures inventées conservées dans le projet, pipes/HTTP local et Qt offscreen. Compilation Python, tabnanny, hygiène et contrôle du diff complètent ces tests. Cas couverts : lecture sans création/migration DB, schéma7 conservé, versions60, contexte privé opt-in borné24Ko, outil sans chemins/SQL/commandes, contenu hostile/HTML/liens, historique atomique et fichiers redirigés, tours/reprise/cancel/timeout, connexion Codex concurrente unique, session Claude validée, Ollama distant refusé, erreurs d'écriture neutres, annulation locale à frontière sûre, export60 sans écraser l'existant.

Schémas JSON-RPC générés avec le Codex réellement installé, contrat confronté à la documentation officielle. Codex en lecture seule sans shell/plugins/hooks/MCP externes; Claude sans outils système. Authentification CLI existante sans lecture des jetons par PokeMind. Chat distinct de la mémoire factuelle. Préférence de partage cloud explicite et mémorisée; aucune autorisation d'envoi de données brutes déduite des options du terminal.

La CI conserve ses neuf marqueurs et registres hérités, installe l'extra desktop et teste Qt offscreen sur Windows/Ubuntu. **Après push, contrôle obligatoire du HEAD distant, de la CI complète au SHA exact, des neuf marqueurs SHA/run par job et des empreintes canoniques concordantes avant réponse finale.** Le run Actions attaché au commit livré est la preuve publique durable.

Ouverture : rapports conservés en lecture seule. Actualisation manuelle : moteur `battle coach --update` existant, hors ligne, progress/cancel sans second moteur. Aucune réanalyse réelle pendant les essais GUI. Biais de défaites, petits n et causes inconnues explicites; collection/crédits/légalités non établis restent inconnus.

Aucune migration7→13, sauvegarde, restauration, suppression utilisateur, installation globale/élévation, interaction jeu, scheduler ou données personnelles Git. Seuls les artefacts de construction de l'application ont été régénérés. Portable local non signé, non publié comme release GitHub. [Guide de lancement et partage](../docs/DESKTOP_GUI_CHAT_GUIDE.md). **AWAITING_AUDIT**, aucun nouveau mandat, portes V1 non promues.


Correction de préparation CI après le premier push : le run40272972824 au SHA6f23351 échoue sur Ubuntu à la collecte Qt (`libEGL.so.1` absente). Le workflow prépare désormais `libegl1` et `libopengl0` sur le runner Ubuntu jetable uniquement; aucune installation sur le PC propriétaire, aucun test Qt ignoré pour masquer cet échec. [Dépendances Qt/Linux](https://doc.qt.io/qt-6/linux-requirements.html). Nouvelle CI complète au HEAD corrigé requise avant réponse finale.
