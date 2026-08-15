#!/usr/bin/env python3
"""G4MEOVER Deck — Flipper-Link.

Duenner Wrapper um flipperbridge (USB-CDC-RPC) fuer den Pi. Steuert den per USB
angeschlossenen Flipper (SubGHz/NFC/RFID/IR/Storage) vom Deck aus. Auf dem Pi
erscheint der Flipper als /dev/ttyACM0.

flipperbridge stammt aus dem Repo g4meover-companion und wird von install.sh nach
/opt/g4meover-deck/vendor gelegt (dort im sys.path).
"""
from __future__ import annotations
import glob

try:
    from flipperbridge import FlipperBridge  # aus vendor/ (install.sh)
    HAVE_BRIDGE = True
except ImportError:
    HAVE_BRIDGE = False


def find_flipper() -> str | None:
    """Flipper-Port plattformunabhängig finden: erst per VID:PID (device_discovery,
    funktioniert auf Windows COMx UND Linux), dann Fallback /dev/ttyACM*."""
    try:
        import device_discovery
        port = device_discovery.find_port("Flipper Zero")
        if port:
            return port
    except Exception:  # noqa: BLE001
        pass
    ports = sorted(glob.glob("/dev/ttyACM*"))
    return ports[0] if ports else None


class FlipperLink:
    def __init__(self, port: str | None = None):
        if not HAVE_BRIDGE:
            raise RuntimeError("flipperbridge nicht installiert (siehe install.sh)")
        self.port = port or find_flipper()
        if not self.port:
            raise RuntimeError("Kein Flipper an /dev/ttyACM* gefunden")
        self._fb: FlipperBridge | None = None

    def __enter__(self) -> "FlipperLink":
        self._fb = FlipperBridge(self.port)
        return self

    def __exit__(self, *a) -> None:
        if self._fb:
            self._fb.close()
            self._fb = None

    def info(self) -> dict:
        assert self._fb
        return self._fb.device_info()

    def storage_list(self, path: str) -> str:
        assert self._fb
        return self._fb.storage_list(path)

    def send_file(self, local: str, remote: str) -> bool:
        assert self._fb
        return self._fb.storage_send(local, remote)

    def launch(self, name_or_path: str) -> str:
        assert self._fb
        return self._fb.loader_open(name_or_path)

    def raw(self, command: str) -> str:
        assert self._fb
        return self._fb.cmd(command)
