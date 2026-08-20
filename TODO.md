# G4MEOVER — TODO / Nächste Schritte

Lebende Checkliste (Stand 2026-08-20). Ergänzt `ROADMAP.md` (Langfrist-Vision) um die
konkrete, priorisierte Abarbeitung. Regeln: deutsche Commits, kein Claude-Contributor,
Feature-Branch→PR→self-merge; Fremd-Code nur mit Lizenzcheck, Logik neu implementieren.

## ✅ Erledigt (diese Runde)
- [x] HID-Stream `0x52` + Ducky-Bib `0x51` (V3+LilyGo), live E2E getippt
- [x] Secret rotiert + History gescrubbt (6 Repos), 5 Repos public
- [x] Alle 6 Geräte neu geflasht (neues Secret)
- [x] 42 Fremd-Repos geklont + `INTEGRATION-MAP.md`, seanec327 analysiert
- [x] WPA-Cracker ans Deck gekoppelt (`deck/wpa_crack.py` + CLI)

> Pi-/hardwaregebundene Punkte werden in **`PI-TODO.md`** geführt.

## Tier 0 — sofort fertigstellen
- [x] `wpa_crack.py` committen (PR #2 gemerged)
- [x] Szenario-Schritt-Typ `wpa` (statt Daemon-Endpoint — Test-Labor ist der richtige Ort)
- [ ] `hashcat`/`hcxtools` auf dem Pi installieren + echt testen → **PI-TODO.md**

## Tier 1 — Quick-Wins (reines Deck-Python)
- [x] **Handshake→Crack Ende-zu-Ende (code-komplett):** V3-`[HSRAW]` (PR #4) + `handshake_capture.py` (PR #3) + CLI `capture`. Aktivierung: V3 flashen (siehe unten) + Pi-Tools (PI-TODO).
- [~] ~~BadUSB-Payload-Bibliothek~~ **verworfen** — grugnoymeme-badUSB ist echte Malware (Ransomware/Keylogger/Stealer). HID bleibt bei autorisierten Test-Markern.
- [ ] WPA-Ergebnisse mit [[project_hashcat_tool]] verzahnen (gemeinsame Wortlisten/Potfile)

## Tier 2 — neue Satelliten-Fähigkeiten (Firmware)
- [ ] **Mousejacking** (viciaoxxx/evilmouse): neuer `ukfe_rf`-Handler `UkfeRfCmdMousejack` (nRF24, Logitech/MS-Unifying) — schließt 2,4-GHz-Lücke
- [ ] **RID-Scanner** (WXLN/rid-scanner-c5): ESP32-C5-Satellitenrolle „Drohnen-Remote-ID" (Scan + ID-Sim) → Swarm-Board
- [ ] **FW-Fix**: `ducky_run` bei nicht-bereitem HID früh abbrechen (statt `SendReport`-Flut) — V3+LilyGo
- [ ] `UkfeRfCmdBleSniff` (0x33) impl. (Referenz: RocketGod/Ubertooth-Bluetooth-Spy)
- [ ] `UkfeRfCmdKarma` (0x28) impl. (Probe→Response-Loop)

## Tier 3 — Funk-Protokolle (Roadmap Phase 2, SX1262 + HackRF)
- [ ] SubGHz-Protokolle aus pompel123 (`SubGrabber`, `Better-Protocols-ProtoPirate`) + RocketGod (`SubGHz-Toolkit`) in Flipper/SX1262 + ProtoPirate portieren
- [ ] `UkfeRfCmdJammer` (0x14) ausbauen (Referenz RocketGod/rf-jammer) — nur autorisiert
- [ ] Meshtastic-Sniff/-Inject am Heltec-SX1262 (Referenz RocketGod/meshtastic-web-chat)
- [ ] HackRF-Szenarien: ADS-B-Decoder + `.sub`↔HackRF-Konverter ins `hackrf_link.py`

## Tier 4 — Ökosystem / UI (Phase 3–4)
- [ ] Flipper-Master-UI vertiefen: Funktion→Gerät→Funk→Ziel (Ideen aus V3SP3R/FlipperUI)
- [ ] Pi-Deck real deployen (SD flashen → `install.sh` → UART↔V4 verdrahten → Dashboard live)
- [ ] 6-ESP32-Swarm: `ukfe_rf` Ziel-ID-Feld + Node-Registry + Rollen (siehe ROADMAP §Swarm)
- [ ] Cockpit + Security-Suite + Hashcat auf dem Pi vereinen

## Querschnitt / Referenzen (gezielt klonen bei Bedarf)
- [ ] `ESP32Marauder` (Upstream) als Referenz für Satelliten-WiFi-Handler
- [ ] `esp32-c5-dualband-deauther` für 5-GHz-Deauth
- [ ] `CSIght` (WiFi-CSI-Radar) als neuartige Sensing-Rolle
- [ ] Lizenz-Hygiene: bei jeder Übernahme Upstream+LICENSE prüfen, sensible Captures nie pushen
