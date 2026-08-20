# G4MEOVER — Roadmap & Session-Handoff

**Zweck:** Selbsttragende Wiederaufnahme nach Session-/Wochen-Limits. Enthält Ist-Stand,
alle Repos, den geplanten Ausbau (inkl. *aller* Funk-Protokolle) und den Resume-Pfad.
**Bei neuer Session:** dieses Dokument lesen → Abschnitt „Ist-Stand" → beim jeweiligen
„→ NÄCHSTER SCHRITT" weitermachen. Ergänzend: die Memory-Dateien (`project_*`, `feedback_*`).

**Regeln:** Commits **deutsch, in kleinen Schritten, in G4MEOVER18s Namen, NIE Claude als
Contributor**. Professioneller Flow: Feature-Branch → PR → selbst mergen. Sensible Captures
(B1–B9.sub) nie pushen. Neue Pentest-Repos privat.

---

## Vision
Flipper Zero + Heltec (V3/V4) + LilyGo T-Dongle S3 + ESP32-WROOM + Raspberry Pi 4 + HackRF One
→ **ein nahtloses Pentest-Ökosystem** über *ein Vokabular* (`ukfe_rf`), gesteuert vom **Flipper
als Master**, über *jede* Funktechnik, jede Aktion über das geeignetste Gerät. Der **Heltec ist
das „Masterpiece"** — soll jeden erdenklichen Befehl ausführen. Der **Pi (Deck) ist das Gehirn**.

## Ist-Stand (2026-08-15) — was LIVE ist
| Baustein | Status |
|---|---|
| Flipper-App `lora-ukfe` | ✅ hierarchisches Katalog-Menü (Kategorie→Funktion), Expansion-Fix, NET→Hub |
| **Flipper → Heltec-V4-Hub (UART) → ESP-NOW → Satellit** | ✅ **live, bidirektional** (Befehl hin, ACK zurück, 12/12) |
| Heltec V4 `heltec-v4-hub` | ✅ Hub + LoRa-Terminal + GPS-ready + **interaktives OLED-Menü** (Button kurz/lang/doppelt) |
| Heltec V3 `heltec-ukfe-rx` | ✅ 868-FSK + ESP-NOW + ACK + 868→ESP-NOW-Hub |
| WROOM `g4meover-wifi-relay` | ✅ ESP-NOW-Koordinator, NVS-Counter, Dual-UART |
| LilyGo `lilygo-ukfe-rx` | ✅ ESP-NOW-Satellit + USB-HID + TFT |
| Pi-Deck `g4meover-deck` | ✅ code-komplett (ukfe_rf.py, Links, Discovery, Daemon+Dashboard, Szenario-Labor, HackRF) — **noch nicht auf echtem Pi** |
| CC2531 Zigbee | ✅ ZNP erreichbar (Z-Stack 2.6.3) |
| **LoRaWAN/TTN (LORIX One + DogyTag)** | ✅ **additiv ins Deck integriert**: `dogytag_link.py` (MQTT-Telemetrie) + `lorix_link.py` (TTN-Gateway+Flotte) + Daemon `/lorawan` + Dashboard-Sektion. Read-only, kein Produktionseingriff. |

**Alle 6 Repos auf GitHub (G4MEOVER18).** `ukfe_rf`-Protokoll byte-genau über C + Python verifiziert.

---

## Roadmap

### Phase 1 — Satelliten-Handler vervollständigen (der Heltec kann ALLES)
Der Katalog (`command_catalog.h`) + `ukfe_rf.h`-Befehlssatz sind da; die **Firmware-Handler
fehlen noch** je Befehl. → In `heltec-v4-hub`/`-ukfe-rx` `act()` ausbauen:
- **WiFi (GhostESP/Marauder/Biscuit-Klasse):** Scan, Deauth(all/target), Evil Portal, Beacon
  Spam, Handshake-Capture, Wardrive+GPS, Probe Sniff, Karma, Packet Monitor, Pwnagotchi.
  → Integrationsweg: GhostESP/Marauder-Quellen als Bibliothek einbinden ODER die Angriffe
  über `esp_wifi_*` direkt umsetzen. **Biscuit Pro** als Referenz für modernes UI/Feature-Set.
- **BLE:** Scan, Spam (Apple/Android/Samsung/Windows), Sour Apple, Sniff.
- **USB-HID:** Payloads/DuckyScript (S3-Satelliten).

### Phase 2 — ALLE Funk-Protokolle der Hardware (SX1262 + ESP32), on demand
Der SX1262 (Heltec) und der ESP32-S3 können weit mehr als der ukfe-Link nutzt. Ready bauen:
- **SX1262 LoRa:** freies LoRa-Terminal ✅ (Freq/SF/BW/CR einstellbar). Ausbauen:
  - **LoRaWAN** (Join/Uplink/Downlink) — z.B. via RadioLib-LoRaWAN oder LMIC.
  - **Meshtastic-Sniff/-Inject** (LoRa-Mesh mitlesen).
  - **APRS-over-LoRa** (Positions-Beacons).
  - **Raw-LoRa-Capture/-Replay** (beliebige Chirp-Signale).
- **SX1262 (G)FSK / OOK:** ukfe-FSK ✅. Generische ISM-Protokolle (433/868/915) in FSK/OOK
  senden/empfangen — Ergänzung zum Flipper-CC1101 (breiterer SF/Deviation-Bereich, mehr TX-Power 22 dBm).
- **SX1262 LR-FHSS** (falls Chip-Variante) für robuste Langstrecke.
- **ESP32-S3:** WiFi (b/g/n), BLE 5 + Mesh, ESP-NOW ✅, 802.11-Raw/Monitor.
- **HackRF (am Deck):** 1 MHz–6 GHz — GPS-Sim, ADS-B, AIS, Pager, Weitband-Recon (siehe MASTERPLAN §8d).
Jedes Protokoll = ein Katalog-Eintrag + ein Firmware-Handler; „schwer einsetzbar sobald gewünscht".

### Phase 3 — Flipper als Master-UI (intuitiv, verschachtelt)
- Menü-Ebene erweitern: **Funktion → Gerät → Funktechnik → Alternative → (Logins/WiFi-Suche)**.
- Rückkanal-Anzeige: ACK/Status/Scan-Hits der Satelliten am Flipper (Log-Scene ausbauen).
- Parameter-Eingabe (Kanal, BSSID, Freq/SF) per Flipper-UI statt Fix-Args.
- Login-/Credential-Verwaltung + WiFi-Netz-Auswahl.

### Phase 4 — Pi-Deck real deployen (das Gehirn)
- SD flashen (Pi OS Lite) → `install.sh` → UART↔Hub verdrahten → `deck-ctl`/Dashboard live.
- Cockpit + Security Suite + Hashcat auf dem Pi vereinen (Blue/Red in einer UI).
- Auto-Router (Aktion → bestes Gerät/Band), ein Capture-Pool, HackRF-Sweep-Integration.

### Phase 5 — Konvergenz & Stabilität
- G4MEOVER-FW v2 (Flipper) aktuell halten: neueste `lora_ukfe` bundeln + rebuild.
- CI + App-Härtung über alle Firmwares; Pairing statt Hardcode-Secret; NVS-Counter überall.

---

## Labor-Konzept: 6-ESP32-Swarm (vom Flipper + Heltec V4 gesteuert)
6 ESP32 als **ESP-NOW-Mesh**, die untereinander sprechen und zentral gesteuert werden.
Enabler (sauber vorbereitet): **Node-ID + Rolle** pro Board (`ukfe_rf` um Ziel-ID-Feld
erweitern: 0=alle/Broadcast, 1..N=gezielt, 0xF0..=Gruppe), Auto-Registrierung am Hub
(jeder Node meldet Boot: ID/MAC/Fähigkeiten), Rollen-Config in NVS.

**Was wir damit lokal ausprobieren (max benutzerfreundlich, alles vorbereitet):**
1. **Kanal-verteilter WiFi-Sweep/-Angriff:** 6 Nodes je 1–2 WiFi-Kanäle → volle 2,4-GHz-
   Abdeckung gleichzeitig (Scan/Deauth/Handshake) statt seriell auf einem Board.
2. **RSSI-Triangulation:** 6 Nodes messen die Signalstärke eines Ziels → Position schätzen
   (verstecktes Gerät / Rogue-AP / Tracker finden). One-Tap vom Flipper, Karte am Deck.
3. **ESP-NOW-Mesh-Reichweite:** Multi-Hop-Weiterleitung (A→B→C…) → große Fläche abdecken,
   Befehle über mehrere Sprünge; Failover, wenn ein Node ausfällt.
4. **Rogue-AP-/Evil-Portal-Swarm:** 6 unterschiedliche Fake-APs/Portale gleichzeitig
   (Massen-Beacon oder verteilte Captive-Portals) — realistischer Lasttest.
5. **Sensor-/Funk-Swarm:** jeder Node ein Schwerpunkt (WiFi / BLE / 2,4G-Sniff / GPS /
   Deauth-Detector) → gemeinsames Lagebild am Hub (Counter-Surveillance).
6. **Lasttei­lung:** großes Ziel (200 APs scannen, Wörterbuch, Wardrive-Fläche) auf 6 Nodes
   aufteilen → 6× schneller. Deck sammelt + merged die Ergebnisse.
7. **Synchronisierte Timing-Aktionen:** PPS/zeit-synchron koordinierter Multi-Node-Puls.
8. **CTF-/Trainings-Lab:** Nodes als Ziele + Angreifer für reproduzierbare Übungsszenarien
   (bindet ans Szenario-Labor an: `scenarios/*.json`, `deck-ctl scenario run`).

**UI/Organisation:** Flipper-Menü „Swarm" → Node/Gruppe wählen → Aktion; Heltec-V4-OLED
zeigt Swarm-Status (Nodes online, Rollen, letzte Antwort); Deck-Dashboard listet alle Nodes
als Kacheln mit Rolle/RSSI/Status. Alles über dasselbe `ukfe_rf`-Vokabular + Szenario-Runner.
→ **NÄCHSTER SCHRITT Swarm:** (a) `ukfe_rf` Ziel-ID-Feld + Node-Registry, (b) Satelliten-FW
um ID/Rolle/Boot-Announce erweitern, (c) Swarm-Kategorie im Flipper-Katalog, (d) Deck-Node-Board.

## Resume-Pfad (nach Limit hier weitermachen)
1. **Geräte finden:** `python deck/device_discovery.py` (VID:PID → Port). Flipper COM3, V4 COM14,
   V3 COM26, LilyGo COM10, WROOM COM8, CC2531 COM24 (Nummern können wechseln → per VID:PID).
2. **Autonom testen ohne Flipper-Knopf:** Frame über V4-USB (COM14) einspeisen → V4 relayed →
   V3 (COM26) zeigt `ESPNOW OK` (Beispiel-Skripte in der Git-Historie / Memory).
3. **Flipper-App bauen+deployen:** `cd lora-ukfe && ufbt` → `flipperbridge send dist/lora_ukfe.fap /ext/apps/GPIO/lora_ukfe.fap`.
4. **Firmware bauen+flashen:** `cd <repo> && pio run -t upload --upload-port <COM>`.
5. **Gotchas (teuer erkämpft):** Flipper-Expansion-Dienst blockiert die USART → `expansion_disable()`
   vor Acquire (schon gefixt). `loader close` schließt die App nicht → `power reboot`. ESP-S3-native-USB-
   CDC teils still → OLED/TFT als Debug. `esp_wifi_set_ps` VOR `esp_now_init` crasht S3. Counter-Desync
   bei Reboot → NVS-Persistenz. Kyrillischer Typname `LораUkfeApp` in der Flipper-App (Token wiederverwenden).

> Nur autorisierte Sicherheitstests auf eigenen Geräten.
