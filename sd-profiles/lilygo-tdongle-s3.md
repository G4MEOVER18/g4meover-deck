# SD-Profil — LilyGo T-Dongle S3

**Karte:** microSD-Slot am T-Dongle S3. Speichert HID-Payloads (DuckyScript) und
gesammelte Loot-Dateien — der Dongle bleibt so ein autarker Drop-Penetrator.

## Struktur
```
/payloads/            DuckyScript-Payloads (.ds), per ukfe_rf-idx wählbar
│   ├── 00_marker.ds
│   ├── 01_recon.ds        (systeminfo -> loot)
│   ├── 02_wifi_export.ds
│   └── 99_lock.ds
/loot/                Exfiltrierte Dateien / Ausgaben
/config/
    └── device.json       Gerätename, ESP-NOW-Kanal, Secret-Slot (Pairing)
```

## Rolle im Ökosystem
- **ESP-NOW-Empfänger** (`lilygo-ukfe-rx`, Kanal 1) → validiert `ukfe_rf` → **USB-HID**.
- `Trigger`/`PayloadRun`-idx aus dem Funkbefehl wählt die `.ds`-Datei von SD →
  getippt am Ziel-PC (statt fest einkompilierter Payloads = **max Flexibilität**).
- Loot landet auf SD, später vom Deck eingesammelt.

## Status / offen
- Firmware geflasht (COM10). S3-native-USB-CDC-Serial gibt remote nichts aus →
  Live-Bestätigung via TFT-Statuskopf oder HID-Tippen. **SD-Payload-Loader = nächster Ausbau**
  (aktuell Payloads einkompiliert; Ziel: von `/payloads/*.ds` laden).
