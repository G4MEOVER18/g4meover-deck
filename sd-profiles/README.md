# G4MEOVER — SD-Profile je Gerät

Jedes Gerät im Ökosystem hat eine **eigene, spezifizierte SD-/Speicher-Belegung**.
Diese Profile definieren, *was auf welche Karte gehört* — reproduzierbar, damit später
viele Leute identische Test-Setups aufbauen, Szenarien fahren, verbessern und re-testen.

| Gerät | Speicher | Profil |
|---|---|---|
| **Flipper Zero** | microSD (FAT32, getestet: 61 GB, gesund) | [flipper.md](flipper.md) |
| **LilyGo T-Dongle S3** | microSD-Slot (Payloads/Loot) | [lilygo-tdongle-s3.md](lilygo-tdongle-s3.md) |
| **Raspberry Pi 4 (Deck)** | microSD = OS | [pi-deck.md](pi-deck.md) |
| **Heltec v3 · WROOM · ESP32-S3** | Flash (SPIFFS/NVS, keine SD) | in Firmware, kein SD-Profil |

**Prinzip:** Ein Profil = Ordnerstruktur + Pflichtinhalte + optionale Payloads. Der
Deck-Provisioner (künftig `deck-ctl sd build <gerät>`) schreibt/prüft das Profil auf
die jeweils eingelegte Karte (Flipper via USB-RPC, andere via Kartenleser).

> Nur autorisierte Tests auf eigenen Geräten. Sensible Captures (B1–B9.sub etc.) bleiben lokal.
