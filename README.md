# Omarchy Shibumi music fixes

Small compatibility fixes for keeping TIDAL and YouTube Music visible in
Shibumi's narrow bar layout, and opening TIDAL when its bar widget cannot
resolve its service through Shibumi's scoped host.

## Requirements

- Omarchy with the Shibumi bar and Shibumi state plugins installed and active.
- The Omarchy plugins `quickshell.tidal` and `damir.ytmusic` installed.

Install TIDAL and YouTube Music through their upstream plugin instructions if
they are not already installed:

- [TIDAL for Omarchy](https://github.com/ph0bos/omarchy-tidal)
- [YouTube Music for Omarchy](https://github.com/Damir-VistaBlox/omarchy-ytmusic)

## Install

```bash
git clone https://github.com/diabolik-diabolik/omarchy-shibumi-music-fixes.git
cd omarchy-shibumi-music-fixes
python install.py
omarchy restart shell
```

The installer makes timestamped backups beside each file it changes. It keeps
the existing Shibumi layout and settings, adds the two music widgets to its
right side if needed, and sets TIDAL's bar icon to its compact display.

TIDAL playback also needs a configured account and backend. Follow the TIDAL
plugin's setup instructions for Mopidy and sign-in.

## What it changes

- Shibumi's final responsive stage retains `G:quickshell.tidal` and
  `G:damir.ytmusic`.
- The TIDAL bar widget opens its player through Shibumi's approved summon path
  if its scoped service lookup is unavailable. Right click opens Now Playing.
- `~/.config/omarchy/shell.json` gets the widget placements and compact TIDAL
  setting while retaining unrelated settings.

## Uninstall

Restore the timestamped backups created by the installer, then restart the
shell. The installer reports each backup path when it makes one.
