# RESULT — PM-AUDIT-CLAUDE-PLAN : publication préparée, A-8 et A-7 (D-269), 2026-11-02

Exécuteur : Claude Code (Opus 5.5). Autorisation : D-258; demande du propriétaire « fais tout ce que tu peux sans moi ».
Code : **`c8b453a`**. Session précédente (D-268) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D268_2026-11-02.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D268_2026-11-02.md).

## Livré (décision D-269)
- `scripts/export_public.py` + `tests/test_export_public.py`; `docs/PUBLICATION.md`; `docs/RELEASE_NOTES_0.9.0.md`.
- Signature facultative dans `scripts/Build-PokeMindInstaller.ps1` et `packaging/PokeMind.iss`.
- A-8 : `window.chat_mode` (Coach / Recherche web / Développement), `Services.prepare_question(research=...)`,
  `tools.RESEARCH_STARTERS`; détecteurs par expressions régulières supprimés.
- A-7 : `services.MATCHUPS_SHOWN`, `services.context_delta`, `window.sent_context`.

## Preuves
- Porte locale `python scripts/local_gate.py` **VERTE** à `c8b453a` : Qt 95, cœur 1543 réussis, 3 ignorés (total 1638).
- Export d'essai : arbre identique à HEAD, 1 commit, aucun push; porte complète VERTE dans l'export.
- Signature : certificat auto-signé temporaire → EXE, installateur et désinstalleur signés; certificat supprimé;
  build non signé identique à l'octet près.
- A-8/A-7 : nouveaux tests (aucun mot ne choisit un mode; un seul envoi par choix de Recherche web; Développement
  absent d'une copie installée; envoi différentiel puis renvoi complet après échec ou nouvelle discussion).
- EXE depuis `c8b453a` : modules identiques aux sources, aucun module QA; fumées mode projet et mode autonome sortie 0;
  bases inventées inchangées; pointeur et dossier `%LOCALAPPDATA%\PokeMind` du propriétaire non modifiés. Déployé dans
  `dist/PokeMind/`; l'ancien est conservé dans `dist/PokeMind-before-message-mode-7d8e536dccd74c7aa9e5efee4e1b86a6`.
- Installateur `PokeMind-Setup-0.9.0.exe` (non signé) : SHA-256 `BEA4FDECF39D6F87DF3EB862996ED933CC9844AF84757D270A0D772418E89C6A`; installation silencieuse, fumée
  et désinstallation propres. Copie : `dist/installer/PokeMind-Setup-0.9.0.exe`; la précédente est renommée
  `PokeMind-Setup-0.9.0-avant-mode.exe` (hors Git).

## Limites
- Publication et signature réelle : décisions du propriétaire (voir NEXT_ACTION). V1 NOT_RELEASE_READY.
