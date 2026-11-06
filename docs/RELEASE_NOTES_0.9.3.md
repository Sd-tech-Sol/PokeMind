# PokeMind 0.9.3 — pre-release

New BrainBall colours, and updates in one click: new cards and new versions of PokeMind, from the app.
Unofficial fan project by Sébastien Dubé, MIT licence.

## Added
- **Update available**: when a newer PokeMind is published, or TCGdex has new cards (a new set, or more cards in
  a recent one), a banner says so. **Update** installs the new cards without restarting PokeMind, then downloads
  the new installer, checks its SHA-256 and installs it; PokeMind closes and opens again by itself. Your data
  stays. **Later** hides the banner until the next launch.
- **Settings → Updates**: the PokeMind and card catalogue versions, **Check now**, and the check at startup. It
  runs at most twice a day, sends nothing about you, and can be turned off.
- **Newest cards on a first launch**: the card catalogue now comes from the newest TCGdex version, and falls back
  to the tested one if the newest cannot be imported. A card update keeps the previous catalogue once.

New sets, such as Mega Evolution—Delta Reign, appear in PokeMind once TCGdex publishes their cards.

## Changed
- **New colours, BrainBall electric**: the dark and light themes follow the PokeMind card — night and royal blue,
  electric blue for actions and selection, gold for emphasis. Wins are blue, losses red, unknown results gold; red
  otherwise only marks what erases. The light theme has a light menu and coach panel, every drawn icon follows the
  theme, and text keeps WCAG AA contrast. The terminal stays dark in both themes.
- The Settings tabs sit on two rows, so every name stays readable beside the coach.

## Install or update
Download `PokeMind-Setup-0.9.3.exe` below and run it; it updates an installed 0.9.0, 0.9.1 or 0.9.2 in place and
keeps your data in `%LOCALAPPDATA%\PokeMind`. From 0.9.3 on, the next versions install from the app itself. The
installer is **not code-signed**: if Windows shows « Windows protected your PC », choose **More info → Run
anyway**. You can check the file against `PokeMind-Setup-0.9.3.exe.sha256`.

---

# PokeMind 0.9.3 — préversion

Nouvelles couleurs BrainBall, et mises à jour en un clic : nouvelles cartes et nouvelles versions de PokeMind,
depuis l'application. Projet de fans non officiel de Sébastien Dubé, licence MIT.

- **Nouvelles couleurs, BrainBall électrique** : les thèmes foncé et clair suivent la carte PokeMind (bleu nuit et
  royal, bleu électrique pour les actions, or pour l'emphase). Victoires en bleu, défaites en rouge, inconnues en
  or; le rouge ne marque sinon que ce qui efface. Le thème clair a un menu et un coach clairs, et les textes
  gardent un contraste WCAG AA. Le terminal reste foncé dans les deux thèmes.
- **Mise à jour disponible** : quand une nouvelle version de PokeMind est publiée, ou que TCGdex a de nouvelles
  cartes (nouvelle extension ou cartes ajoutées à une extension récente), un bandeau le dit. **Mettre à jour**
  installe les cartes sans redémarrer, puis télécharge le nouvel installateur, vérifie son SHA-256 et
  l'installe; PokeMind se ferme et se rouvre tout seul. Tes données restent. **Plus tard** cache le bandeau
  jusqu'au prochain lancement.
- **Réglages → Mises à jour** : versions de PokeMind et du catalogue, **Vérifier maintenant**, et la
  vérification au démarrage (au plus deux fois par jour, rien de tes données n'est envoyé, désactivable).
- **Cartes les plus récentes au premier lancement** : le catalogue vient de la version la plus récente de
  TCGdex, sinon de celle déjà testée.
- Les nouvelles extensions, comme Méga-Évolution — Delta Reign, arrivent dans PokeMind dès que TCGdex publie
  leurs cartes.

Télécharge `PokeMind-Setup-0.9.3.exe` ci-dessous : il met à jour une 0.9.0, 0.9.1 ou 0.9.2 installée et garde
tes données dans `%LOCALAPPDATA%\PokeMind`. Les versions suivantes s'installeront depuis l'application.
L'installateur n'est **pas signé** : « Informations complémentaires → Exécuter quand même ». Son SHA-256 est
dans `PokeMind-Setup-0.9.3.exe.sha256`.
