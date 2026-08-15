# G4MEOVER Deck — Ökosystem-OS für Raspberry Pi 4

Das **Gehirn** des G4MEOVER-Pentest-Ökosystems. Verwandelt einen Raspberry Pi 4 in
die zentrale Steuerung, die **Flipper Zero**, **ESP32-Satelliten** (WROOM-Relay,
Heltec LoRa v3, LilyGo T-Dongle S3) und den Pi selbst über **alle Funkwege** hinweg
zu einem nahtlosen System verbindet — alles an einem Punkt.

```
        ┌──────────────────────── Raspberry Pi 4 (DECK) ───────────────────────┐
        │  deck-daemon (HTTP :8712)  ·  deck-ctl (CLI)  ·  ukfe_rf (verifiziert) │
        └───────┬───────────────────────────────────┬───────────────────────────┘
        USB-RPC │                       GPIO-UART    │ (ukfe_rf, 115200)
        ┌───────▼────────┐              ┌────────────▼───────────┐
        │  Flipper Zero  │              │  ESP32-WROOM (Relay)   │
        │  SubGHz/NFC/…  │              └──────┬─────────────────┘
        └────────────────┘                     │ ESP-NOW (2.4 GHz)
                                    ┌───────────▼───────────┐
                                    │  Heltec v3 · LilyGo   │  (+868-FSK Direktlink)
                                    └───────────────────────┘
```

## Ein Vokabular über alle Transporte
Der Deck spricht **`ukfe_rf`** — dasselbe signierte Protokoll (keyed MAC + CRC16 +
Rolling-Counter) wie Flipper/WROOM/Heltec. Die Python-Portierung `deck/ukfe_rf.py`
ist **byte-genau gegen die C-Implementierung verifiziert** und hardware-bestätigt
(Pi-Frame → WROOM → ESP-NOW → Heltec `PARSE OK`). Ein Befehl, egal welcher Funkweg:
868-FSK, ESP-NOW, oder (via Flipper) SubGHz/NFC/RFID/IR.

## Die SD erstellen (der physische Schritt)
1. **Raspberry Pi Imager** → *Raspberry Pi OS Lite (64-bit, Bookworm)* auf die SD.
   In den erweiterten Optionen SSH + Benutzer + WLAN setzen (headless).
2. SD in den Pi 4, booten, per SSH verbinden.
3. Deck installieren:
   ```bash
   git clone https://github.com/G4MEOVER18/g4meover-deck
   cd g4meover-deck
   sudo bash install.sh
   sudo reboot
   ```
4. Nach dem Reboot ist die SD das fertige **G4MEOVER-Deck-OS**.
   *(Ubuntu Server für Pi: alternativ `provision/user-data` als cloud-init nutzen —
   provisioniert headless beim Erstboot.)*

## Bedienung
```bash
deck-ctl status                       # Geräte, Funktechnologien, Counter
deck-ctl sat ping                     # STATUS an Satelliten (ukfe_rf/UART→ESP-NOW)
deck-ctl sat trigger 1                # Payload/Aktion 1 auslösen
deck-ctl sat deauth AA:BB:CC:DD:EE:FF 6
deck-ctl flipper info                 # Flipper über USB-RPC
deck-ctl flipper ls /ext/apps/Sub-GHz
```
HTTP-API (Backend der Ökosystem-UI), jede Antwort trägt **{action, device, radio, status}**:
```bash
curl localhost:8712/status
curl -X POST localhost:8712/sat/ping
curl -X POST localhost:8712/sat/trigger -d '{"id":1}'
```

## Verdrahtung Pi ↔ WROOM-Relay
| Pi 4 | WROOM |
|---|---|
| GPIO14 TXD (Pin 8) | RX (Flipper-UART-Eingang des Relays) |
| GPIO15 RXD (Pin 10) | TX |
| GND (Pin 6) | GND |
| 5V/3V3 | VIN/3V3 (optional Versorgung) |

> Der Relay nimmt ukfe_rf-Frames auf **beiden** seiner UARTs an (routing-robust).

## Komponenten
| Datei | Rolle |
|---|---|
| `deck/ukfe_rf.py` | Protokoll (verifiziert byte-genau zu C) |
| `deck/satellite_link.py` | UART-Sender + persistenter Rolling-Counter |
| `deck/flipper_link.py` | Flipper USB-RPC (flipperbridge) |
| `deck/deck_ctl.py` | einheitliche CLI |
| `deck/deck_daemon.py` | HTTP-Control-API (UI-Backend) |
| `install.sh` · `systemd/` · `provision/` | Provisioning → bootfähiges OS |

## Roadmap
Siehe **[MASTERPLAN.md](MASTERPLAN.md)** — der Weg zum nahtlosen Ökosystem, in dem
Security Suite + Pentest-Cockpit auf dem Deck vereint jede Aktion über das jeweils
geeignetste Gerät/Funkband ausführen, sichtbar in einer UI (Aktion · Gerät · Funk · Status).

> Nur für autorisierte Sicherheitstests auf eigenen Geräten.
