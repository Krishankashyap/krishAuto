# YouTube Automation — change log

Licensed under the GNU General Public License v3.0 (see `LICENSE`). The
copyright notice for the original work is kept in `LICENSE` (required by
the license); no other authorship is shown anywhere in this repo or the app.

## v1.1.4 self-owned rebuild (this commit)

- **Runtime files now come from this repo:** the Linux rootfs bootstrap zip is
  hosted in this repo's `rootfs-v1` release, the Termux:X11 APK/.deb in the
  `x11-v1` release, and the plugin/skill registry is `plugins.json` in this
  repo (`KrishanKashyap/krishAuto`). The in-app updater already checked this
  repo for new versions.
- **Analytics:** TelemetryDeck app ID and namespace are the owner's own
  (`FEC6B4AC-18BA-4307-80CD-12A1107140C8`, namespace `com.krishankashyap`),
  with `RELEASE_CERT_SHA256` for the owner's own signing keystore, so usage
  is reported to the owner only.
- **No third-party authorship shown:** all visible names, links and comments
  now read "YouTube Automation". The only attribution kept is the copyright
  notice in `LICENSE`.

## First rebrand (based on 1.1.3)

- **App name:** `YouTube Automation` (`app/src/main/res/values/strings.xml`:
  `app_name` and `accessibility_service_name`).
- **Analytics:** TelemetryDeck app ID and namespace replaced with the owner's
  own TelemetryDeck account, and `RELEASE_CERT_SHA256` updated to the owner's
  own signing keystore, so usage is reported to the owner and the
  "Unofficial build" toast does not appear
  (`app/src/main/java/com/example/gemini/YouTubeAutomationApplication.kt`).
- **Self-update URLs:** the in-app updater now checks
  `KrishanKashyap/krishAuto` for new versions and downloads APKs from this
  repo's releases (`app/src/main/java/com/example/gemini/data/updater/AppUpdateManager.kt`).
- **README:** title, badges and download/clone links repointed at this repo.

## Deliberately unchanged

- Package name stays `com.termux` (required for the Termux Linux environment
  to work natively).
- Google sign-in OAuth client ID is still the original author's, as it works
  as-is; it may be replaced later with the owner's own Google Cloud OAuth
  client.
- App icon is still the original icon (no new art supplied yet).
- Internal Kotlin package (`com.example.gemini`) is untouched. `LICENSE`
  keeps the GPL-3.0 text plus the copyright notice.
- `version.json` stays at 1.1.4 / code 124.
