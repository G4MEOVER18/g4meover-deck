# G4MEOVER — Ökosystem-Masterplan

**Vision:** Flipper Zero · Heltec LoRa v3 · LilyGo T-Dongle S3 · ESP32-WROOM · ESP32-S3 ·
Raspberry Pi 4 — **ein nahtloses Pentest-Ökosystem**, das über *alle* Funktechnologien
verbunden bleibt, jede Aktion mit dem **jeweils geeignetsten Gerät/Funkband** ausführt,
gesteuert von **einem Punkt** aus. **Security Suite + Pentest-Cockpit** vereint auf dem Deck.
Eine UI zeigt jederzeit: **Aktion · Gerät · Funktechnologie · Status**.

---

## 0. Was JETZT live ist (Stand 2026-08-13)

| Baustein | Status |
|---|---|
| Flipper G4MEOVER-FW v2.0.0 | ✅ live geflasht (Maavurd), 418 Apps, Vault, Power-Suite |
| Flipper↔Heltec 868-FSK (`ukfe_rf`) | ✅ **live E2E** (PARSE OK, Counter zählt) |
| WROOM WiFi-Relay (ESP-NOW) | ✅ **geflasht + live** (crashende Alt-FW ersetzt) |
| Heltec ESP-NOW-RX (additiv neben 868) | ✅ **geflasht + live** (`en:` zählt) |
| Flipper→WROOM UART-TX (NET:-Menü) | ✅ gebaut + deployed, routing-robust (Dual-UART) |
| Pi-Deck `ukfe_rf.py` | ✅ **byte-genau zu C + HW-bestätigt** (Pi→WROOM→Heltec) |
| Pi-Deck OS (Daemon/CLI/Installer) | ✅ code-komplett, syntaxgeprüft |

**Ein Protokoll trägt bereits drei Transporte:** CC1101-868-FSK · GPIO-UART · ESP-NOW.

---

## 1. Hardware-Rollen — jedes Gerät spielt seine Stärke

| Gerät | Kernstärke | Rolle im Ökosystem |
|---|---|---|
| **Raspberry Pi 4** | Compute, Netz, Storage, LLM | **Gehirn/Deck** — UI, Orchestrierung, Cracking, Report |
| **Flipper Zero** | 300–928 MHz OOK/FSK, 13.56 NFC, 125 kHz RFID, IR, iButton | **RF-Frontend** + tragbares UI |
| **Heltec LoRa v3** (S3+SX1262) | 868 FSK/LoRa Langstrecke, natives USB-HID | **Funk-Satellit** + BadUSB-Penetrator |
| **LilyGo T-Dongle S3** | natives USB-HID, TFT, kompakt | **USB-Penetrator** (Drop-Device) + Anzeige |
| **ESP32-WROOM** | 2.4G WiFi/BLE, günstig | **WiFi-Relay/Koordinator** (ESP-NOW-Hub) |
| **ESP32-S3** | natives USB, mehr RAM | **USB/WiFi-Angriff** + HID |
| **CC2531 / ESP32-C6/H2** | echtes 802.15.4 | **Zigbee-Sniffing** (Pi/Flipper = Controller) |

---

## 2. Funk-/Transport-Matrix (die Verbindungswege)

| Kanal | Zwischen | Technik | Status |
|---|---|---|---|
| 868-FSK | Flipper ↔ Heltec | CC1101 ↔ SX1262, `ukfe_rf` | ✅ live |
| ESP-NOW 2.4G | WROOM → Heltec/LilyGo/S3 | ESP-NOW-Broadcast, `ukfe_rf` | ✅ live (Heltec) |
| GPIO-UART | Flipper/Pi ↔ WROOM | 115200, `ukfe_rf` (Dual-UART) | ✅ live (Pi-sim) |
| USB-RPC | Pi ↔ Flipper | flipperbridge (CDC) | ✅ Deck-Modul |
| USB-HID | S3-Satellit → Ziel-PC | native USB-Tastatur | ✅ Heltec-FW |
| WiFi-STA/AP | ESP → Netz/Ziel | Marauder/GhostESP/EvilPortal | 📐 integrieren |
| LoRa Langstrecke | Heltec ↔ Heltec | SX1262 LoRa | 📐 dual-mode |
| 802.15.4 | CC2531/C6 → Wireshark | Zigbee-Sniff | 📐 Controller-App |

---

## 3. Fähigkeits-Matrix — Aktion × geeignetstes Gerät × Funk

| Aktion | Bestes Gerät | Funk | Warum |
|---|---|---|---|
| SubGHz Replay/Brute/Jam | Flipper | 300–928 OOK/FSK | CC1101 nativ |
| Rolling-Code (RollForge/ProtoPirate) | Flipper | 433/868 | eigene Apps |
| WiFi Deauth/EvilPortal/Wardrive | ESP32/LilyGo | 2.4G WiFi | Marauder/GhostESP |
| BLE-Spam / NRF24-Mousejack | Flipper/ESP | 2.4G | BLE + nRF24 |
| NFC Read→Dict→Nested | Flipper | 13.56 | 4475-Key-Dict |
| RFID/iButton | Flipper | 125 kHz | nativ |
| BadUSB/HID-Injection | Heltec/LilyGo/S3 | USB | natives USB |
| LoRa-Fernbefehl | Heltec | 868 LoRa | Langstrecke |
| Zigbee-Sniff | CC2531/C6 | 802.15.4 | echtes Radio |
| Handshake/Hash-Cracking | Pi | — | hashcat/Compute |
| OSINT/Recon/Report | Pi | Netz | Cockpit+LLM |

**Kernidee:** Die UI wählt automatisch das geeignetste Gerät/Funkband pro Aktion —
oder lässt den User explizit routen. Ein Befehl, viele Ausführungspfade.

---

## 4. Coordination-Layer — das „nahtlose"

```
              ┌─────────── UNIFIED UI ───────────┐
              │ Aktion · Gerät · Funk · Status    │  ← Web/TFT/Flipper
              └───────────────┬───────────────────┘
                    HTTP :8712 │ (deck-daemon)
        ┌──────────────────────┴──────────────────────┐
        │  DECK-ORCHESTRATOR (Pi)                        │
        │  ukfe_rf (1 Vokabular) · Router · Capture-DB   │
        └──┬───────────┬───────────────┬────────────────┘
      USB-RPC     GPIO-UART        (künftig) MQTT/WS
        │           │
    [Flipper]   [WROOM-Relay] ──ESP-NOW──► [Heltec][LilyGo][S3]
```
- **Ein Vokabular:** `ukfe_rf` (signiert, Rolling-Counter) über 868/UART/ESP-NOW — verifiziert.
- **Ein Backend:** `deck-daemon` HTTP-API, jede Antwort `{action, device, radio, status}`.
- **Ein Router:** wählt Transport/Gerät je Aktion (Fähigkeits-Matrix als Regeln).

---

## 5. Integration Security Suite + Pentest-Cockpit (auf dem Deck)

- **Pentest-Cockpit** (PySide6, `python` 3.12) läuft nativ auf dem Pi → wird die
  **UI-Shell** des Decks. Neue Seite „Ökosystem": Geräte-/Funk-/Status-Board + Aktions-Router.
  Neues `core/deck.py` spricht die deck-daemon-API. (Flipper-Funk-Modul = Strang D.)
- **Security Suite** (defensiv, read-only [[feedback_security_suite_readonly]]) → als
  Blue-Team-Tab eingebunden; Findings ins Deck-Reporting.
- **Hashcat-Tool** → Cracking-Backend des Decks (WiFi-Handshakes von ESP-Satelliten).
- **Bridge:** Cockpit ↔ deck-daemon ↔ (Flipper USB-RPC | Satelliten ukfe_rf).

---

## 6. Die einheitliche UI (Innovation pur)

**Leitbild:** *Eine Oberfläche, die zeigt was gerade passiert, auf welchem Gerät, über
welches Funkband, mit welchem Status — und aus der jede Aktion startbar ist.*

- **Live-Board:** Kacheln je Gerät (online/Funk aktiv/Batterie/RSSI/Counter).
- **Aktions-Palette:** Aktion wählen → UI schlägt geeignetstes Gerät/Funk vor (Matrix) → Start.
- **Funk-Karte:** welche Transporte gerade tragen (868/ESP-NOW/UART/USB/WiFi), Farbcode Status.
- **Timeline/Log:** jede Aktion mit `{action, device, radio, status, counter, ts}`.
- **Umsetzung:** deck-daemon liefert die Envelopes; Frontend = Cockpit-Seite (Desktop) +
  optional Web-Dashboard (Handy) + Flipper-Vault als mobiles Mini-UI.

---

## 7. Roadmap (Phasen · TODO)

### Phase A — WiFi-Kette schließen  *(fast fertig)*
- [x] WROOM-Relay ESP-NOW · Heltec-RX · Flipper-UART-TX · Pi-`ukfe_rf`
- [ ] **LilyGo T-Dongle S3: ESP-NOW-RX-FW** (gleiche Handler wie Heltec) — *nächster Bau*
- [ ] Flipper→WROOM am realen Devboard verdrahten + „NET:"-Ping live testen
- [ ] Response-Pfad Satellit→Flipper/Pi (ACK/Status zurück) end-to-end

### Phase B — Deck-Gehirn scharf
- [ ] Pi 4 mit SD provisionieren (install.sh) + UART↔WROOM verdrahten, `deck-ctl` live
- [ ] deck-daemon als UI-Backend härten (Auth, Geräte-Discovery, Persistenz)
- [ ] Flipper-USB-RPC-Modul (Strang D) in Cockpit

### Phase C — UI vereinen
- [ ] Cockpit-Seite „Ökosystem" (Live-Board + Aktions-Router + Funk-Karte)
- [ ] Security-Suite-Tab (Blue-Team) + Hashcat-Backend anbinden
- [ ] Web-Dashboard (Handy) auf deck-daemon

### Phase D — Funk-Breite
- [ ] ESP-Firmwares G4MEOVER-branden (Marauder/GhostESP) + `ukfe_rf`-RX
- [ ] Heltec LoRa-Langstrecke (dual FSK/LoRa)
- [ ] Zigbee-Kette (CC2531/ESP32-C6 → Wireshark, Controller-App)
- [ ] Wardriving-Rig (Heltec+GPS, LoRa-Uplink)

### Phase E — Innovation & Stabilität
- [ ] Auto-Router (Aktion→bestes Gerät) als Regel-Engine
- [ ] Ein Capture-Pool (Flipper-Vault ↔ Pi-DB Sync)
- [ ] CI + App-Härtung (Crash-Muster-Checkliste) über alle Firmwares
- [ ] Ein Identitäts-/Secret-Management (Pairing statt Hardcode-Secret)

---

## 8. Innovations-Ideen (Anreicherung)

1. **Auto-Transport-Failover:** Befehl geht über 868; kein ACK → automatisch ESP-NOW → USB.
   (Der Rolling-Counter macht Mehrfachzustellung sicher.)
2. **„One-Tap-Attack":** UI-Aktion orchestriert mehrere Geräte (Flipper captured Handshake →
   Pi cracked → Heltec meldet Ergebnis per LoRa).
3. **Funk-Situationskarte:** Live-Heatmap welcher Kanal/Band gerade trägt (RSSI je Link).
4. **Blue/Red-Umschalter:** dieselbe UI, Security-Suite-Modus (defensiv) vs. Pentest (offensiv).
5. **Mobiler Kopf:** Flipper-Vault als abgesetztes Mini-UI, wenn der Pi nicht dabei ist.
6. **Shared Secret via Pairing-Dance** (Flipper zeigt Code → Satelliten übernehmen) statt Hardcode.

---

## 8b. Grand Vision — die universelle Steuer-/Streu-Fabrik

**Leitsatz (User):** *Alle Sensoren, Radio-/Radar-Boards und Mikrocontroller — unter
jeder Bedingung, mit meiner Firmware — über jede vorhandene Funktion steuern UND streuen.
Kontrolliert. KI-gestützt, automatisiert und frei. „Alle für alle." Max Funktion, max
Kompatibilität, max Radio-Duty-Cycle, max Flexibilität, max Userfriendly.*

**Architektur, die das trägt:**
1. **Ein Bus, viele Radios (`ukfe_rf` + Deck-Router):** jedes Board wird zum adressierbaren
   Knoten. Der Router zerlegt einen High-Level-Befehl in geräte-/funk-spezifische Aktionen
   und **streut** ihn (Broadcast) ODER **steuert** gezielt (Unicast an einen Knoten).
2. **Capability-Registry:** jedes Gerät meldet beim Boot, was es kann (Bänder, Sensoren,
   HID, Duty-Cycle-Grenzen). Der Router kennt so zur Laufzeit die Fähigkeits-Matrix →
   **max Kompatibilität** (neue Hardware = neuer Registry-Eintrag, kein Umbau).
3. **Adressierung:** `ukfe_rf` bekommt ein optionales **Ziel-ID-Feld** (0 = Broadcast/„alle
   für alle", sonst Geräte-ID) → gezielte Steuerung neben dem Streuen.
4. **Duty-Cycle-Governor:** der Deck kennt pro Band die legalen/thermischen Grenzen und
   taktet Streuung so, dass **max Duty-Cycle ohne Regelbruch/Overload** gefahren wird.
5. **KI-Schicht (lokal, frei):** Ollama-LLM auf dem Pi als (a) Befehls-Übersetzer
   (Natürliche Sprache → Router-Aktionen), (b) Auto-Pilot für Szenarien, (c) Auswerter
   (Captures → Befund → nächster Schritt). „Automatisiert und frei" = lokal, kein Cloud-Zwang.
6. **Universal-Firmware-Kern:** ein gemeinsames C-Modul (`ukfe_rf.c` + Capability-Announce +
   Command-Dispatch), das auf JEDES Board portiert wird (ESP32/-S3/-C6, nRF, RP2040…),
   darüber board-spezifische Treiber. Neue Sensoren/Radios = Treiber dazu, Kern bleibt.

## 8c. Szenario-Labor (die Pentest-Firma)

**Ziel:** reproduzierbare, versionierte Pentest-Szenarien, die viele Leute **fahren →
verbessern → re-testen** können. Grundlage der Firma.

- **`scenarios/<name>/`** — Definition (Ziel, benötigte Geräte/Bänder, Schritte als
  Router-Aktionen, erwartetes Ergebnis, Erfolgskriterium).
- **Runner:** `deck-ctl scenario run <name>` fährt die Schritte über den Router, protokolliert
  jede Aktion als `{action, device, radio, status, ts}` (dieselben UI-Felder) → Report.
- **Labor-Loop:** Ergebnis vergleichen → Szenario verbessern (Git-versioniert) → erneut fahren.
- **Determinismus:** SD-Profile (siehe `sd-profiles/`) sorgen für identische Test-Setups.
- **Rollen:** Blue (Security Suite, defensiv) vs. Red (Cockpit, offensiv) im selben Runner.

## 8d. HackRF One — das Universal-Radio des Decks

**Rolle:** Die HackRF (1 MHz–6 GHz, TX/RX) hängt am **Deck (Pi/PC)** und deckt genau die
Lücken, die Flipper (300–928 MHz OOK/FSK) und ESP (2,4 GHz) lassen. Sie ist der
**„jede Frequenz, jede Modulation"-Fallback** des Auto-Routers. Deck-Modul `hackrf_link.py`
(Sweep/Capture/Transmit über die hackrf-CLI).

**Interessante Dienste/Szenarien (wo die HackRF JETZT echten Mehrwert bringt):**

1. **Weitband-Spektrum-Recon → Hand-off.** HackRF `hackrf_sweep` über 1 MHz–6 GHz findet
   aktive Signale in Sekunden. Der Router verteilt: **sub-GHz-Treffer → Flipper** (Capture/
   Replay), **2,4-G-Treffer → ESP** (WiFi/BLE), **Rest → HackRF**. Das „Spektrum-Auge",
   das kein anderes Gerät hat.
2. **Out-of-Band-TX, was Flipper/ESP NICHT können:**
   - **GPS-Simulation** (1575,42 MHz) → eigenes Ökosystem-GPS (Flipper/Heltec) gegen Spoofing
     testen, oder Ziel-GPS prüfen. Schlägt die Brücke zum GPS-Thema.
   - **ADS-B** (1090), **AIS** (161,975), **ACARS** (131,55), **POCSAG-VHF/UHF-Pager** —
     Frequenzen weit außerhalb des CC1101.
   - **ISM 433/868/915 mit beliebiger Modulation**, wenn der Flipper-CC1101 zu simpel ist.
3. **Capture → Deck-Analyse → koordinierter Replay.** HackRF nimmt Roh-IQ eines Signals auf,
   das der Flipper nicht dekodiert → **Deck demoduliert** (URH / GNU Radio) → Protokoll raus →
   **in-band Flipper** (RollForge/ProtoPirate) ODER **out-of-band HackRF** spielt zurück.
   Der Flipper wird zum Präzisionswerkzeug, die HackRF zum Breitband-Sensor.
4. **Passive SIGINT / Counter-Surveillance.** HackRF lauscht weitband *parallel*, während
   Flipper/ESP aktiv arbeiten — erkennt versteckte Sender/Wanzen (FlipDeFlock-Synergie),
   protokolliert die RF-Umgebung.
5. **Jamming/Noise (nur autorisiert, abgeschirmt)** an beliebiger Frequenz für RF-Resilienz-
   Tests, die der Flipper-Jammer nicht abdeckt.
6. **„One-Tap Multi-Radio":** EINE UI-Aktion → HackRF-Sweep → Zielsignal → Deck wählt das
   geeignetste Gerät (Flipper/ESP/HackRF) → führt aus. Die HackRF macht den Auto-Router erst
   vollständig (sie sieht, was die anderen nicht sehen).

**Fähigkeits-Ergänzung (zur Matrix in §3):**
| Aktion | Bestes Gerät | Funk |
|---|---|---|
| Weitband-Spektrum-Sweep | **HackRF** | 1 MHz–6 GHz |
| GPS-Spoof / ADS-B / AIS / Pager-TX | **HackRF** | out-of-band |
| Roh-IQ-Capture unbekannter Signale | **HackRF** → Deck-Analyse | beliebig |

## 9. Offene Entscheidungen (User)
- [ ] LilyGo: primär USB-HID-Penetrator, TFT-Statuskopf, oder beides?
- [ ] UI-Primär: Cockpit-Desktop (Pi-Monitor) oder Web-Dashboard (Handy) zuerst?
- [ ] Pi-Modell fürs Deck: 4 (Power) bestätigt — Formfaktor (fest vs. portabel Zero 2 W-Satellit)?
- [ ] Hardware-Inventar vervollständigen (ESP32-Typen/Anzahl, GPS, nRF-Boards) für Phase D.

> Prinzip über allem: **Ein Vokabular, jedes Gerät seine Stärke, alles an einem Punkt,
> kompatibel & stabil zuerst.** Nur autorisierte Tests auf eigenen Geräten.
