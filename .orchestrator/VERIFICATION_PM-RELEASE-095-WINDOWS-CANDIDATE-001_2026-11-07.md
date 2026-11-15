# Vérification indépendante ChatGPT — PM-RELEASE-095-WINDOWS-CANDIDATE-001
Date : 2026-11-07. Branche : `work/pm-v1-lotj-final-readiness-windows`.
Code et version : `24e9cc5d05b4debc7a3f6c3ad245f3f36cdfb068`.
Rapport : `a21e98a4dffdf35811d2dc29c40e4a49f674ee30`.

## Verdict
**VERIFIED_SOURCE / CANDIDATE_READY_FOR_OWNER_RECEPTION / NOT_RELEASE_READY**.
Relecture indépendante sur GitHub du commit source, du rapport et du compare `c33cf40...a21e98a` :
un commit version/documentation/tests puis un commit uniquement d'orchestration. Les changements de source applicative se limitent à `src/pokemind/__init__.py` pour passer à 0.9.5; le module Statistiques de `3a56023` est inchangé. La documentation d'une 0.9.4 jamais publiée, cumulée dans la 0.9.5, est vérifiée dans les notes et CHANGELOG. L'existence et le contenu des binaires locaux, les trois portes, les installations de test et les captures Windows **n'ont pas été rejoués indépendamment par ChatGPT** : ce sont des preuves d'exécuteur consignées dans RESULT.

## Preuves de l'exécuteur examinées
- Trois portes `local_gate.py` (source `24e9cc5`, arbre rapport, export public dry-run) : chacune Qt 121 passés, cœur 1635 passés / 0 échec / 3 ignorés, sortie 0; exécutions isolées hors dépôt.
- EXE `build/exe-upgrade-f886329deff24c7f853fbcd4f1f0ec35/dist/PokeMind/PokeMind.exe` : SHA-256 `7121BBEB277594164621DDEECD6FAA3331FAFFB87EABD55024BB2BD6E0E9E6FF`.
- Setup local non signé `dist/installer-candidate-0.9.5-24e9cc5/PokeMind-Setup-0.9.5.exe` : SHA-256 `6E7E5CB2D63FA05BB96123E3A9DF6CFACEB37E90D21C9CD7417564526C0D68CB`.
- EXE et Setup annoncent 0.9.5, icônes PE 9/9, PYZ avec `pokemind.deck_public_stats`, scan chemins personnels déclaré CLEAN.
- Fumées gelées 7 pages, Deck Lab › Statistiques FR/sombre et EN/clair, hors réseau, hors comptes Claude/Codex; calculs identiques à l'oracle synthétique.
- AppId de QA différent du propriétaire : 0.9.3 → 0.9.5 → désinstallation, 15 fichiers fictifs inchangés; première passe interrompue par erreur du script de QA, deuxième complète.
- Export public dry-run non poussé, arbre identique, porte verte; dépôt public non modifié.

## Réserves avant toute publication
1. Pas de preuve d'une installation 0.9.5 dans l'environnement propriétaire réel, du flux de mise à jour silencieuse depuis l'application, de SmartScreen ni du rendu 125% DPI.
2. La collecte vraie Limitless a été validée lors du mandat précédent; ce candidat a été fumé avec cache synthétique et réseau bloqué. Petit échantillon public, taux par archétype et non liste de 60 cartes.
3. Le nom de la source non traduit en anglais contient « API publique » : cosmétique, non bloquant.
4. Installateur non signé; attention à l'authenticité. L'utilisateur doit privilégier son artefact construit localement et vérifier le SHA-256 avant exécution. L'empreinte ci-dessus est rapportée par Claude, pas calculée par ChatGPT.
5. La release note mentionne la future procédure de téléchargement/mise à jour alors que 0.9.5 n'est pas publiée; ne pas interpréter ces instructions comme un lien actuellement disponible. La 0.9.4 locale demeure installée selon les observations de l'exécuteur.

## Prochaine action unique : réception propriétaire (GO distinct requis)
Ne plus lancer Claude/Codex. Demander un GO explicite pour la **mise à niveau réelle** avec l'installateur candidat 0.9.5 local. Avant exécution : sauvegarde indépendante des données de l'utilisateur, contrôle SHA-256, fermeture des sessions PokeMind et autres processus susceptibles d'utiliser les fichiers, vérification de l'emplacement exact du Setup, plan de restauration, puis installation contrôlée, lancement, Deck Lab › Statistiques et conservation des decks/journaux/préférences. Ne pas supprimer l'ancien candidat. Si un échec survient : documenter avant tout nouvel essai. **Aucune publication/tag/push public sans GO distinct après réception.**
