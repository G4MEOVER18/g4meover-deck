#!/usr/bin/env python3
"""G4MEOVER Deck — DuckyScript-Streamer (0x52).

Zerlegt ein beliebig langes DuckyScript in ukfe_rf-0x52-Chunks und schickt sie ueber
den Hub (V4/WROOM) per ESP-NOW an einen S3-Satelliten (V3/LilyGo), der das Skript als
USB-HID-Tastatur auf dem Zielrechner tippt.

Test-Setup:
  - Direkt am V4-Hub-USB (Windows):  python hid_stream_send.py --port COM14 payload.txt
  - Am Pi ueber die GPIO-UART:        python hid_stream_send.py --port /dev/serial0 payload.txt
  - Eingebautes Skript per id (0x51): python hid_stream_send.py --port COM14 --ducky 0

Nur autorisierte Sicherheitstests auf eigenen Geraeten.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # deck/ importierbar
from satellite_link import SatelliteLink  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="DuckyScript ueber ukfe_rf-0x52 an einen Satelliten streamen.")
    ap.add_argument("script", nargs="?", help="Pfad zur DuckyScript-Datei (oder '-' fuer stdin).")
    ap.add_argument("--port", required=True, help="Serieller Port des Hubs (z.B. COM14 oder /dev/serial0).")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--ducky", type=int, metavar="ID",
                    help="Statt Stream ein eingebautes DuckyScript per id ausloesen (0x51).")
    ap.add_argument("--chunk-delay", type=float, default=0.05,
                    help="Pause zwischen Chunks in s (Default 0.05).")
    args = ap.parse_args()

    # Counter-Datei plattformabhaengig (Windows hat kein /var/lib)
    counter_file = str(Path.home() / ".g4meover-deck" / "counter") if sys.platform == "win32" \
        else "/var/lib/g4meover-deck/counter"
    link = SatelliteLink(port=args.port, baud=args.baud, counter_file=counter_file)

    if args.ducky is not None:
        c = link.hid_ducky(args.ducky)
        print(f"HID-Ducky id={args.ducky} ausgeloest (counter={c}).")
        return 0

    if not args.script:
        ap.error("Entweder eine Skript-Datei oder --ducky ID angeben.")
    text = sys.stdin.read() if args.script == "-" else Path(args.script).read_text(encoding="utf-8")
    frames = link.hid_stream(text, chunk_delay_s=args.chunk_delay)
    print(f"DuckyScript gestreamt: {len(text)} Zeichen in {frames} Frames (0x52) an {args.port}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
