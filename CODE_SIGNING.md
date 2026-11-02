# Code signing

*Lire en français plus bas / French version below.*

PokeMind releases are **unsigned** for now. Windows SmartScreen therefore shows « Windows protected your
PC » the first time the installer is run: choose **More info → Run anyway**, after checking the file's
SHA-256 against the `.sha256` file published with the release.

The build is ready to sign. `scripts/Build-PokeMindInstaller.ps1 -SignArguments …` signs `PokeMind.exe`,
the installer and its uninstaller with `signtool` from the Windows SDK, verifies that each file carries a
signature, then computes the final SHA-256 on the signed installer.

## One-time setup (maintainer)

Choose one publisher identity and keep it across releases, so that SmartScreen reputation accumulates:

- **Microsoft Azure Artifact Signing** (formerly Trusted Signing): paid Azure subscription, Public Trust
  individual identity validation, a certificate profile, then
  `-SignArguments '/dlib','<dir>\Azure.CodeSigning.Dlib.dll','/dmdf','<dir>\metadata.json'`
  with `-TimestampUrl 'http://timestamp.acs.microsoft.com'`;
- **SignPath Foundation**: free signing for open source projects, on application and approval;
- an **OV or EV certificate** from a certificate authority, in the Windows store:
  `-SignArguments '/sha1','<thumbprint>'`.

A self-signed certificate does not remove the SmartScreen warning. Without any `-SignArguments`, the build
stays unsigned and produces exactly the same installer as before.

---

# Signature du code

Les releases de PokeMind ne sont **pas signées** pour l'instant. Windows SmartScreen affiche donc « Windows a
protégé votre ordinateur » au premier lancement de l'installateur : choisis **Informations complémentaires →
Exécuter quand même**, après avoir comparé le SHA-256 du fichier au fichier `.sha256` publié avec la release.

La construction est prête à signer. `scripts/Build-PokeMindInstaller.ps1 -SignArguments …` signe
`PokeMind.exe`, l'installateur et son désinstalleur avec `signtool` du SDK Windows, vérifie que chaque fichier
porte une signature, puis calcule le SHA-256 final sur l'installateur signé.

## Configuration à faire une seule fois (mainteneur)

Choisir une seule identité d'éditeur et la garder d'une release à l'autre, pour que la réputation SmartScreen
s'accumule :

- **Microsoft Azure Artifact Signing** (anciennement Trusted Signing) : abonnement Azure payant, validation
  d'identité individuelle Public Trust, un profil de certificat, puis les arguments ci-dessus;
- **SignPath Foundation** : signature gratuite pour les projets libres, sur demande et approbation;
- un **certificat OV ou EV** d'une autorité de certification, dans le magasin Windows (`/sha1`).

Un certificat auto-signé n'enlève pas l'avertissement SmartScreen. Sans `-SignArguments`, la construction
reste non signée et produit exactement le même installateur qu'avant.
