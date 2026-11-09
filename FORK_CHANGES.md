# Fork changes — YouTube Automation (krishAuto)

This repository is a fork of [AntiGem](https://github.com/Santoshkurmi/antigem)
by Santosh Kurmi, licensed under the GNU General Public License v3.0
(see `LICENSE`). The original copyright is retained:
Copyright (C) 2026 Santosh Kurmi. Modifications Copyright (C) 2026 Krishan Kashyap.

## What changed in this fork (first rebrand commit, based on AntiGem 1.1.3)

- **App name:** `AntiGem` → `YouTube Automation`
  (`app/src/main/res/values/strings.xml`: `app_name` and
  `accessibility_service_name`).
- **Analytics:** TelemetryDeck app ID and namespace replaced with the fork
  owner's own TelemetryDeck account (`FEC6B4AC-18BA-4307-80CD-12A1107140C8`,
  namespace `com.krishankashyap`), and `RELEASE_CERT_SHA256` updated to the
  fork's own signing keystore, so usage is reported to the fork owner and the
  "Unofficial build" toast does not appear
  (`app/src/main/java/com/example/gemini/AntiGemApplication.kt`).
- **Self-update URLs:** the in-app updater now checks
  `KrishanKashyap/krishAuto` for new versions and downloads APKs from this
  fork's releases, instead of the upstream repo
  (`app/src/main/java/com/example/gemini/data/updater/AppUpdateManager.kt`).
- **README:** title, badges and download/clone links repointed at this fork;
  original copyright line kept, fork line added.

## Deliberately unchanged for the first build

- Package name stays `com.termux` (required for the Termux Linux environment
  to work natively — see upstream README, "Why the package name is `com.termux`").
- Google sign-in OAuth client ID and the Linux rootfs download URL are still
  the upstream author's, as they work as-is; they may be replaced later.
- App icon is still the upstream icon (no new art supplied yet).
- Internal class names, Kotlin package (`com.example.gemini`), and `LICENSE`
  are untouched. `version.json` stays at 1.1.3 / code 123 for the first test
  build.
