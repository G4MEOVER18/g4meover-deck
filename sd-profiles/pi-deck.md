# SD-Profil — Raspberry Pi 4 (Deck)

**Karte:** microSD = das komplette **Deck-OS** (das Gehirn). Anders als bei den anderen
Geräten IST die SD hier das Betriebssystem.

## Erstellung
Raspberry Pi Imager → *Raspberry Pi OS Lite 64-bit* → boot → `sudo bash install.sh`
(siehe [../README.md](../README.md)). Danach trägt die SD:

```
/opt/g4meover-deck/       Deck-Software (deck/, venv, vendor/flipperbridge)
/etc/g4meover-deck/       deck.conf
/var/lib/g4meover-deck/   counter (persistenter Rolling-Counter, Anti-Replay)
/etc/systemd/system/      g4meover-deck.service  (Daemon :8712)
/usr/local/bin/deck-ctl   CLI
```

## Rolle im Ökosystem
- **Orchestrator:** spricht `ukfe_rf` (byte-genau verifiziert) über GPIO-UART an die
  Satelliten + Flipper via USB-RPC.
- **Capture-Pool + Cracking** (hashcat), **UI-Backend** (deck-daemon), später Cockpit+Suite.
- **Szenario-Host:** hier liegen die reproduzierbaren Pentest-Szenarien fürs Labor.

## Ausbau
- Cockpit + Security Suite auf denselben Pi (Phase C).
- `/opt/g4meover-deck/scenarios/` — versionierte Szenario-Definitionen (test → improve → re-test).
