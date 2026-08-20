# G4MEOVER — Raspberry-Pi-TODO (auf dem Pi zu erledigen)

Sammelstelle für alles, was **physischen Pi-Zugriff / die reale Deck-Hardware** braucht.
Wird abgearbeitet, sobald der Pi bereitsteht (siehe [[project_g4meover_deck]]). Diese Liste
ergänzt `TODO.md` (allgemein) um die hardware-/umgebungsgebundenen Punkte.

## Pi-Provisioning (Erstinstallation)
- [ ] SD flashen: Raspberry Pi Imager → **Pi OS Lite 64-bit** → Hostname/SSH/WLAN vorkonfig.
- [ ] `git clone https://github.com/G4MEOVER18/g4meover-deck` → `sudo bash install.sh` → `reboot`
- [ ] UART verdrahten: Pi `/dev/serial0` (GPIO14/15) ↔ **V4-Hub** (bzw. WROOM) TX/RX + GND
- [ ] `raspi-config`: Serial-Login AUS, Serial-Hardware AN (GPIO-UART frei für `serial0`)
- [ ] `secret.h`/`secret_local.py` mit **neuem Secret `6d47…d2c5`** auf den Pi (NICHT committen)
- [ ] Persistenten Counter anlegen: `/var/lib/g4meover-deck/counter` (Anti-Replay, überlebt Reboot)
- [ ] systemd: `deck_daemon` als Service aktivieren (`systemd/`), Dashboard `:8712` prüfen

## Tools installieren (Pakete)
- [ ] **WPA-Pipeline**: `sudo apt install hashcat hcxtools` → `wpa_crack.py detect` muss „BEREIT" zeigen
- [ ] **HackRF** (Universal-Radio): `sudo apt install hackrf` → `hackrf_link.py` detect
- [ ] Wortlisten/Captures-Ordner: `wordlists/` (rockyou o.ä.) + `captures/` für .pcap

## Live-Tests auf echter Hardware
- [ ] `deck-ctl status` — VID:PID-Discovery aller Geräte am Pi
- [ ] Szenario-Labor: `deck-ctl scenario run ecosystem-sweep` (Flipper+Satelliten+Zigbee)
- [ ] **WPA-Kreis E2E**: `wpa_crack.py capture <sat-port> hs.pcap --wordlist …` gegen EIGENES Testnetz
      (setzt geflashtes V3-`[HSRAW]` voraus — ✅ Firmware bereit, Flash siehe TODO.md)
- [ ] Dashboard im Browser gegen echte HW (Geräte-Board + Szenario-Buttons)

## Konvergenz (später)
- [ ] Cockpit + Security-Suite + Hashcat-Tool auf dem Pi vereinen (Blue/Red in einer UI)
- [ ] Auto-Router (Aktion → bestes Gerät/Band), gemeinsamer Capture-Pool
- [ ] CC2531-Zigbee am Pi (USB), `zigbee_link.py` gegen echte Coordinator-HW
