#!/usr/bin/env python3
"""G4MEOVER Deck — Zigbee-Link (CC2531 über ZNP).

Spricht das TI Z-Stack Monitor-Test-Protokoll (ZNP/MT) mit dem CC2531-Koordinator
über Serial. Bringt das echte 802.15.4-Radio ins Ökosystem — Flipper/Pi = Controller.

ZNP-Frame:  SOF(0xFE) | LEN | CMD0 | CMD1 | DATA[LEN] | FCS(=XOR LEN..DATA)
Live verifiziert: SYS_PING -> `fe 02 61 01 79 01 1a` (cap=0x0179).
"""
from __future__ import annotations
import time

import serial

SOF = 0xFE
# (cmd0, cmd1)
SYS_PING = (0x21, 0x01)
SYS_VERSION = (0x21, 0x02)


def _frame(cmd0: int, cmd1: int, data: bytes = b"") -> bytes:
    body = bytes([len(data), cmd0, cmd1]) + data
    fcs = 0
    for b in body:
        fcs ^= b
    return bytes([SOF]) + body + bytes([fcs])


class ZigbeeLink:
    def __init__(self, port: str, baud: int = 115200):
        self.port = port
        self.baud = baud
        self._s: serial.Serial | None = None

    def open(self) -> "ZigbeeLink":
        self._s = serial.Serial(self.port, self.baud, timeout=1.0)
        time.sleep(0.2)
        self._s.reset_input_buffer()
        return self

    def close(self) -> None:
        if self._s:
            self._s.close()
            self._s = None

    def __enter__(self): return self.open()
    def __exit__(self, *a): self.close()

    def _sreq(self, cmd, data: bytes = b"", timeout: float = 1.5):
        """Sendet SREQ, liest die SRSP-Nutzdaten (oder None)."""
        assert self._s
        self._s.reset_input_buffer()
        self._s.write(_frame(cmd[0], cmd[1], data))
        end = time.time() + timeout
        # auf SOF synchronisieren
        while time.time() < end:
            b = self._s.read(1)
            if b == bytes([SOF]):
                hdr = self._s.read(3)  # LEN, CMD0, CMD1
                if len(hdr) < 3:
                    return None
                ln = hdr[0]
                payload = self._s.read(ln + 1)  # DATA + FCS
                if len(payload) < ln + 1:
                    return None
                return payload[:ln]
        return None

    def ping(self) -> int | None:
        """SYS_PING -> Capabilities-Bitmaske (uint16) oder None."""
        d = self._sreq(SYS_PING)
        return (d[0] | (d[1] << 8)) if d and len(d) >= 2 else None

    def version(self) -> dict | None:
        """SYS_VERSION -> {transport, product, major, minor, maintrel}."""
        d = self._sreq(SYS_VERSION)
        if not d or len(d) < 5:
            return None
        return {"transport": d[0], "product": d[1],
                "major": d[2], "minor": d[3], "maintrel": d[4]}

    def info(self) -> dict:
        cap = self.ping()
        ver = self.version()
        return {"reachable": cap is not None, "capabilities": cap, "version": ver}


CAP_FLAGS = {  # ZNP MT-Capabilities-Bits (Auszug)
    0x0001: "SYS", 0x0002: "MAC", 0x0004: "NWK", 0x0008: "AF",
    0x0010: "ZDO", 0x0020: "SAPI", 0x0040: "UTIL", 0x0080: "DEBUG",
    0x0100: "APP", 0x1000: "ZOAD",
}


def cap_names(cap: int) -> list[str]:
    return [name for bit, name in CAP_FLAGS.items() if cap & bit]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    import device_discovery as dd
    port = dd.find_port("CC2531 Zigbee")
    if not port:
        print("CC2531 nicht gefunden"); sys.exit(1)
    with ZigbeeLink(port) as z:
        i = z.info()
        cap = i["capabilities"]
        print(f"CC2531 @ {port}")
        print(f"  erreichbar : {i['reachable']}")
        print(f"  caps       : 0x{cap:04X} ({', '.join(cap_names(cap)) if cap else '-'})")
        print(f"  version    : {i['version']}")
