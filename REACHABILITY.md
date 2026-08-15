# G4MEOVER — Hardware- & Erreichbarkeits-Analyse

Live erhoben 2026-08-13 am realen Aufbau. Für jedes Gerät: exakte Identität (VID:PID)
und **alle** Zugangswege — direkt-USB, über ESP-NOW, verschachtelt über den Flipper.

## Geräte-Identität (exakt)
| Gerät | Port | Chip · VID:PID | Rolle |
|---|---|---|---|
| **Flipper Zero** | COM3 | ST native CDC · `0483:5740` | RF-Frontend / Orchestrierung |
| **ESP32-WROOM** | COM8 | WCH CH9102 · `1A86:55D4` | WiFi-Relay (ESP-NOW-Hub) |
| **Heltec LoRa v3** | COM26 | SiLabs CP210x · `10C4:EA60` | 868-FSK + ESP-NOW-Satellit, USB-HID |
| **LilyGo T-Dongle S3** | COM10 | Espressif native · `303A:1001` | ESP-NOW-Satellit, USB-HID |
| **CC2531 Zigbee** | COM24 | TI · `0451:16A8` | 802.15.4-Koordinator |
| *(Fremd)* USB-Display | COM4 | CH340 · `1A86:5722` „USB35INCHIPS" | **nicht Ökosystem** — ignorieren |

## Erreichbarkeits-Matrix (live getestet)
| Gerät | Direkt-USB | Via ESP-NOW | Via Flipper (GPIO/RPC) | Testergebnis |
|---|---|---|---|---|
| Flipper | ✅ RPC (`device_info` ok) | — | — | Maavurd · g4meover-2.0.0 · API 87.1 |
| WROOM | ⚠️ CLI **nur standalone** | ✅ als Sender | ✅ GPIO-UART-Ziel | *aktuell am Flipper → USB-CLI kontendiert* |
| Heltec | ✅ Serial (Banner ok) | ✅ RX (`ESPNOW OK` 3/3 früher) | ✅ 868-FSK (PARSE OK) | live |
| LilyGo | ⚠️ CDC **still** (S3-Quirk) | ✅ RX (Pattern-bewiesen) | — | geflasht; Serial remote blind |
| CC2531 | ✅ ZNP (`SYS_PING`→`fe 02 61 01 79 01 1a`) | — | (künftig Controller-App) | Zigbee-Koordinator antwortet |

## Harte Erkenntnisse (teuer erarbeitet)

1. **WROOM-am-Flipper-Signatur:** esptool „Download mode detected, but **TX path seems
   to be down**" ⇒ der WROOM steckt am Flipper-GPIO — seine UART0 ist mit Flipper-Pin
   13/14 querverdrahtet, die USB-CLI (COM8) ist dann kontendiert. Standalone flasht/spricht
   er einwandfrei. **→ Zugang je nach Steckzustand wechseln.**
2. **DTR/RTS-Auto-Reset-Falle:** Ein naives `serial.open()` assertiert DTR/RTS und kann
   ESP-Boards in den **ROM-Bootloader stranden** (dann still). Nach dem Öffnen **immer**
   `setDTR(False); setRTS(False)`. Recovery: Reset-to-run-Sequenz (RTS low-puls) — beim
   **CP210x (Heltec) klappt sie**, beim **CH9102 (WROOM) andere Polarität** → dort
   esptool-Hardreset oder **USB kurz abziehen**.
3. **S3-native-USB (LilyGo/COM10):** CDC gibt remote nichts aus (Composite-HID-Quirk).
   Erreichbar/verifizierbar nur via ESP-NOW-Wirkung, TFT-Statuskopf oder HID-Tippen.
4. **CC2531 lebt** und spricht ZNP (Z-Stack) — bereit als echtes 802.15.4-Radio,
   Flipper/Pi als Controller (`zigpy-znp`/Wireshark-Pipeline).

## Zugangswege pro Gerät (für „max Erreichbarkeit")
- **Flipper:** USB-RPC (Pi/PC) · GPIO-UART (Pi) · GPIO-UART→WROOM (Satelliten-Streuung).
- **WROOM:** *standalone* USB-CLI/Flash · *am Flipper* via Flipper-NET:-Menü (GPIO-UART) ·
  Funk: ESP-NOW-Sender an alle Satelliten.
- **Heltec:** USB-Serial (CP210x) · 868-FSK vom Flipper · ESP-NOW vom WROOM · USB-HID zum Ziel.
- **LilyGo:** USB-Flash (S3) · ESP-NOW vom WROOM · USB-HID zum Ziel.
- **CC2531:** USB-ZNP (Pi/PC) — Zigbee-Sniff/-Inject, Controller = Flipper/Pi.

## Empfehlungen für Stabilität & Flexibilität
- **Fester Steckplan dokumentieren:** WROOM entweder „am Flipper" (Feld) ODER „am Pi/USB"
  (Labor/Flash) — der Deck erkennt den Modus (Port-Sync vs. Flipper-NET).
- **Geräte-Discovery im Deck-Daemon:** VID:PID-Tabelle (oben) → automatische Zuordnung
  Port→Gerät→Zugangsweg beim Start (= „max userfriendly").
- **Reset-sicheres Öffnen** als Standard in allen Deck-Tools (DTR/RTS-Deassert + Reset-to-run).
- **LilyGo-Statuskopf** (TFT/LED) nachrüsten für Feld-Verifikation ohne Serial.
