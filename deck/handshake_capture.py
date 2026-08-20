#!/usr/bin/env python3
"""G4MEOVER Deck — Handshake-Capture-Brücke.

Schließt den WPA-Kreis: Ein Satellit im Handshake-Modus (`UkfeRfCmdHandshake` 0x25)
snifft EAPOL-Frames und gibt sie über Serial als Hex aus — Kontrakt je Zeile:

    [HSRAW] <hex des rohen 802.11-Frames>

Dieses Modul liest solche Zeilen (von der Satelliten-Serial oder aus einer Datei),
schreibt sie als gültiges .pcap (LINKTYPE_IEEE802_11 = 105) und übergibt es an
`wpa_crack.py` (-> hcxpcapngtool -> hashcat). Damit läuft „Handshake mitschneiden (Funk)
-> Passwort knacken (Deck)" ohne Zwischenschritte von Hand.

Nur für autorisierte Sicherheitstests an eigenen Netzen.
"""
from __future__ import annotations
import re
import struct
import time

LINKTYPE_IEEE802_11 = 105
_HSRAW = re.compile(r"\[HSRAW\]\s*([0-9A-Fa-f]+)")


def _pcap_global_header() -> bytes:
    # magic, ver 2.4, tz=0, sig=0, snaplen, network
    return struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, LINKTYPE_IEEE802_11)


def _pcap_record(frame: bytes, ts_sec: int, ts_usec: int = 0) -> bytes:
    return struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame)) + frame


def write_pcap(frames: list[bytes], path: str, base_ts: int | None = None) -> int:
    """Schreibt 802.11-Frames als klassisches .pcap. Gibt die Frame-Anzahl zurück.
    base_ts: Startzeit (Unix-Sekunden); Aufrufer liefert sie (kein Date.now hier)."""
    ts = base_ts if base_ts is not None else 0
    with open(path, "wb") as f:
        f.write(_pcap_global_header())
        for i, fr in enumerate(frames):
            f.write(_pcap_record(fr, ts + i))
    return len(frames)


def parse_hsraw(text: str) -> list[bytes]:
    """Zieht alle [HSRAW]-Frames aus einem Log/Stream. Ungerade/leere Hex werden verworfen."""
    frames = []
    for m in _HSRAW.finditer(text):
        h = m.group(1)
        if len(h) >= 24 and len(h) % 2 == 0:   # >=12 Byte (Header) und gerade
            try:
                frames.append(bytes.fromhex(h))
            except ValueError:
                pass
    return frames


def capture_from_serial(port: str, out_pcap: str, seconds: float = 30.0,
                        base_ts: int | None = None) -> dict:
    """Lauscht `seconds` an der Satelliten-Serial, sammelt [HSRAW]-Frames -> .pcap.
    Liefert {pcap, frames, error}. base_ts vom Aufrufer (z.B. int(time.time()))."""
    try:
        import serial  # pyserial
    except ImportError:
        return {"error": "pyserial fehlt", "frames": 0}
    buf = ""
    try:
        s = serial.Serial(port, 115200, timeout=0.3)
        s.dtr = False
        s.rts = False
        t0 = time.time()
        while time.time() - t0 < seconds:
            chunk = s.read(512)
            if chunk:
                buf += chunk.decode("utf-8", "replace")
        s.close()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e), "frames": 0}
    frames = parse_hsraw(buf)
    if not frames:
        return {"error": "keine [HSRAW]-Frames empfangen", "frames": 0, "pcap": out_pcap}
    write_pcap(frames, out_pcap, base_ts=base_ts)
    return {"pcap": out_pcap, "frames": len(frames), "error": ""}


if __name__ == "__main__":  # Selbsttest: synthetischer Frame -> pcap -> zurücklesen
    fake = "[HS] EAPOL #1 ap=00:11:22:33:44:55 len=20\n[HSRAW] 0802000000112233445566778899aabbccddeeff888e0102\n"
    fr = parse_hsraw(fake)
    print("geparste Frames:", len(fr), "erster len:", len(fr[0]))
    write_pcap(fr, "_selftest.pcap", base_ts=1000)
    raw = open("_selftest.pcap", "rb").read()
    magic, = struct.unpack("<I", raw[:4])
    net, = struct.unpack("<I", raw[20:24])
    print(f"pcap magic=0x{magic:08X} linktype={net} groesse={len(raw)}B "
          f"({'OK' if magic == 0xA1B2C3D4 and net == LINKTYPE_IEEE802_11 else 'FEHLER'})")
    import os
    os.remove("_selftest.pcap")
