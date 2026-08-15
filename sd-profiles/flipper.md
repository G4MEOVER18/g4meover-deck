# SD-Profil — Flipper Zero

**Karte:** microSD FAT32. Live getestet 2026-08-13: 61 GB, 59 GB frei, gesund
(Label FLIPPERZERO). Aufgeräumte Struktur (91 % reclaimt in früherer Session).

## Pflicht-Struktur (`/ext`)
```
/ext
├── apps/            App-Kategorien (GPIO, Sub-GHz, NFC, Tools, …) — 472 unique
│   ├── GPIO/        lora_ukfe.fap (RF-Console, NET:-Menü), g4meover_spoof, wiegand_reader
│   ├── Sub-GHz/     rollforge, proto_pirate, rolljam/rolllab_research …
│   └── Tools/       access_audit …
├── subghz/          Captures (.sub)  · live: 18
├── nfc/             Dumps (.nfc)     · live: 23  + assets/mf_classic_dict.nfc (4475 Keys)
├── lfrfid/          RFID (.rfid)     · live: 12
├── infrared/        IR (.ir)         · live: 10
├── badusb/          DuckyScripts     · live: 4
├── subghz/assets/extend_range.txt   (Pentest-Default, autorisiert)
└── update/          f7-update-g4meover-2.0.0  (SD-Selbstupdate)
```

## Rolle im Ökosystem
- **RF-Frontend-Speicher:** Captures, die der Flipper aufnimmt/sendet.
- **NET:-Menü** in `lora_ukfe.fap` sendet `ukfe_rf` über GPIO-UART an den WROOM →
  Satelliten. Die SD trägt die App, die das Ökosystem vom Flipper aus steuert.
- **Vault** (`g4meover_vault.fap`) indexiert alle Capture-Typen zentral.

## Szenario-Bereitschaft (Labor)
- Bekannte Test-Captures unter `/ext/subghz/_scenarios/…` ablegen (reproduzierbar).
- `mf_classic_dict.nfc` als Standard-Angriffswörterbuch.
- Deploy neuer Apps: `flipperbridge send <fap> /ext/apps/<Kat>/<app>.fap` (md5-verifiziert).
