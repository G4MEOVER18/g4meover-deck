#!/usr/bin/env python3
"""G4MEOVER Deck — Satelliten-Link.

Sendet signierte ukfe_rf-Befehle ueber die Pi-GPIO-UART an den WROOM-Relay
(-> ESP-NOW an LilyGo/Heltec) bzw. direkt an einen Satelliten. Der Rolling-Counter
wird auf Platte persistiert (ueberlebt Reboots) — wichtig fuers Anti-Replay, da die
Satelliten nur monoton steigende Counter akzeptieren.
"""
from __future__ import annotations
import os
import threading

import serial  # pyserial

import ukfe_rf


class SatelliteLink:
    def __init__(self, port: str = "/dev/serial0", baud: int = 115200,
                 secret: bytes = ukfe_rf.DEFAULT_SECRET,
                 counter_file: str = "/var/lib/g4meover-deck/counter"):
        self.port = port
        self.baud = baud
        self.secret = secret
        self.counter_file = counter_file
        self._lock = threading.Lock()
        self._serial: serial.Serial | None = None
        self._counter = self._load_counter()

    # ---- Counter-Persistenz (Anti-Replay ueber Reboots) ----
    def _load_counter(self) -> int:
        try:
            with open(self.counter_file) as f:
                return int(f.read().strip() or "0")
        except (OSError, ValueError):
            return 0

    def _save_counter(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.counter_file), exist_ok=True)
            tmp = self.counter_file + ".tmp"
            with open(tmp, "w") as f:
                f.write(str(self._counter))
            os.replace(tmp, self.counter_file)  # atomar
        except OSError:
            pass

    # ---- Verbindung ----
    def open(self) -> None:
        if self._serial is None:
            self._serial = serial.Serial(self.port, self.baud, timeout=0.5)

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    # ---- Senden ----
    def send(self, cmd: int, args: bytes = b"") -> int:
        """Baut Frame mit naechstem Counter und sendet ihn. Gibt den Counter zurueck."""
        with self._lock:
            self.open()
            self._counter += 1
            frame = ukfe_rf.build_frame(self.secret, self._counter, cmd, args)
            assert self._serial is not None
            self._serial.write(frame)
            self._serial.flush()
            self._save_counter()
            return self._counter

    # ---- Bequeme Befehle ----
    def status(self) -> int:
        return self.send(ukfe_rf.CMD_STATUS)

    def trigger(self, payload_id: int, delay_ms: int = 0) -> int:
        return self.send(ukfe_rf.CMD_TRIGGER,
                         bytes([payload_id & 0xFF]) + int(delay_ms).to_bytes(4, "little"))

    def wifi_deauth(self, bssid: bytes, channel: int) -> int:
        if len(bssid) != 6:
            raise ValueError("bssid muss 6 Byte sein")
        return self.send(ukfe_rf.CMD_WIFI_DEAUTH, bssid + bytes([channel & 0xFF]))

    def evil_portal(self, portal_id: int = 0) -> int:
        return self.send(ukfe_rf.CMD_EVIL_PORTAL, bytes([portal_id & 0xFF]))

    def beacon_spam(self, mode: int = 0) -> int:
        return self.send(ukfe_rf.CMD_BEACON_SPAM, bytes([mode & 0xFF]))

    def abort(self) -> int:
        return self.send(ukfe_rf.CMD_ABORT)
