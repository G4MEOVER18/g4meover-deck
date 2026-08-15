#!/usr/bin/env python3
"""G4MEOVER ukfe_rf — Python-Portierung des gemeinsamen Command-Protokolls.

Bit-genaue Portierung von lora-ukfe/rf/ukfe_rf.c, damit das Raspberry-Pi-Deck
DIESELBEN signierten Frames spricht wie Flipper/WROOM/Heltec. Der Pi kann so die
Satelliten direkt ueber seine GPIO-UART (an den WROOM/Heltec) kommandieren.

Frame (nach Sync bei Funk; roh bei UART/ESP-NOW):
  [LEN][MAGIC=0x47][VER=0x01][COUNTER(4 LE)][CMD][ALEN][ARGS..][MAC(4)][CRC16(2 LE)]
"""
from __future__ import annotations

MAGIC = 0x47
VERSION = 0x01
MAX_ARGS = 40
SECRET_LEN = 16

# ---- Commands (identisch zu ukfe_rf.h) ----
CMD_STATUS = 0x01
CMD_TRIGGER = 0x02
CMD_ABORT = 0x03
CMD_PAYLOAD_LIST = 0x04
CMD_PAYLOAD_RUN = 0x05
CMD_LORA_SCAN = 0x10
CMD_WIFI_SCAN = 0x20
CMD_WIFI_DEAUTH = 0x21
CMD_WIFI_STOP = 0x22
CMD_EVIL_PORTAL = 0x23
CMD_BEACON_SPAM = 0x24

_MASK = 0xFFFFFFFF


def crc16(buf: bytes) -> int:
    """CRC16-CCITT (0x1021, init 0xFFFF) — wie ukfe_rf_crc16."""
    crc = 0xFFFF
    for byte in buf:
        crc ^= (byte << 8) & 0xFFFF
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def _mix32(h: int, data: bytes) -> int:
    """FNV-artiger 32-bit Mixer — exakt wie mix32() in C (uint32-Arithmetik)."""
    for d in data:
        h = (h ^ d) & _MASK
        h = (h * 0x01000193) & _MASK      # FNV-Prime
        h = (h ^ (h >> 15)) & _MASK
        h = (h * 0x2545F491) & _MASK
    return h


def mac(secret: bytes, counter: int, cmd: int, args: bytes) -> bytes:
    """4-Byte keyed MAC ueber VER|COUNTER|CMD|ALEN|ARGS, key-gesandwicht."""
    hdr = bytes([
        VERSION,
        counter & 0xFF, (counter >> 8) & 0xFF,
        (counter >> 16) & 0xFF, (counter >> 24) & 0xFF,
        cmd & 0xFF,
    ])
    h = 0x811C9DC5                          # FNV-offset
    h = _mix32(h, secret)                   # key vorne
    h = _mix32(h, hdr)
    h = _mix32(h, bytes([len(args)]))       # arg_len
    h = _mix32(h, args)
    h = _mix32(h, secret)                   # key hinten (Sandwich)
    return bytes([h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF, (h >> 24) & 0xFF])


def build_frame(secret: bytes, counter: int, cmd: int, args: bytes = b"") -> bytes:
    """Baut den kompletten Wire-Frame (LEN..CRC). Wirft bei ungueltigen Args."""
    if len(secret) != SECRET_LEN:
        raise ValueError("secret muss 16 Byte sein")
    if len(args) > MAX_ARGS:
        raise ValueError("args zu lang")
    body = bytes([
        MAGIC, VERSION,
        counter & 0xFF, (counter >> 8) & 0xFF, (counter >> 16) & 0xFF, (counter >> 24) & 0xFF,
        cmd & 0xFF, len(args),
    ]) + args + mac(secret, counter, cmd, args)
    length = len(body) + 2                  # LEN = body + CRC
    frame = bytes([length]) + body
    c = crc16(frame)                        # CRC ueber LEN..MAC
    return frame + bytes([c & 0xFF, (c >> 8) & 0xFF])


# ---- Bequeme Builder (Spiegel der C-Helfer) ----
def make_trigger(secret: bytes, counter: int, payload_id: int, delay_ms: int = 0) -> bytes:
    args = bytes([payload_id & 0xFF]) + delay_ms.to_bytes(4, "little")
    return build_frame(secret, counter, CMD_TRIGGER, args)


def make_status(secret: bytes, counter: int) -> bytes:
    return build_frame(secret, counter, CMD_STATUS)


def make_wifi_deauth(secret: bytes, counter: int, bssid: bytes, channel: int) -> bytes:
    if len(bssid) != 6:
        raise ValueError("bssid muss 6 Byte sein")
    return build_frame(secret, counter, CMD_WIFI_DEAUTH, bssid + bytes([channel & 0xFF]))


# Gemeinsames Geheimnis — IDENTISCH mit RF_SECRET/UKFE_SECRET (out-of-band pairen!).
DEFAULT_SECRET = bytes([
    0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
    0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF,
])


if __name__ == "__main__":
    import sys
    f = make_status(DEFAULT_SECRET, 1000)
    print(" ".join(f"{b:02X}" for b in f))
    sys.exit(0)
