#!/usr/bin/env python3
"""G4MEOVER Deck — Geräte-Discovery.

Erkennt angeschlossene Ökosystem-Geräte automatisch an ihrer USB-Identität (VID:PID)
und ordnet jedem seinen Zugangsweg zu. Grundlage für "max userfriendly": der Deck weiß
beim Start, welches Gerät an welchem Port hängt und wie es erreichbar ist. Enthält ein
**reset-sicheres Öffnen**, das ESP-Boards nicht versehentlich in den Bootloader strandet.

Cross-Plattform via pyserial (Windows COMx, Linux /dev/tty*).
"""
from __future__ import annotations
import time

import serial
import serial.tools.list_ports

# VID:PID → Gerät + Zugangswege (aus REACHABILITY.md, live verifiziert)
KNOWN = {
    (0x0483, 0x5740): dict(device="Flipper Zero",        role="RF-Frontend / Orchestrator",
                           access=["USB-RPC (flipperbridge)", "GPIO-UART"], reset_safe=False),
    (0x1A86, 0x55D4): dict(device="ESP32-WROOM (Relay)",  role="WiFi-Relay / ESP-NOW-Hub",
                           access=["USB-CLI", "ESP-NOW-Sender", "Flipper-GPIO-UART"], reset_safe=True),
    (0x10C4, 0xEA60): dict(device="Heltec LoRa v3",       role="Satellit (868 + ESP-NOW, USB-HID)",
                           access=["USB-Serial", "868-FSK", "ESP-NOW"], reset_safe=True),
    (0x303A, 0x1001): dict(device="LilyGo T-Dongle S3",   role="Satellit (ESP-NOW, USB-HID)",
                           access=["USB-Flash", "ESP-NOW", "USB-HID"], reset_safe=True,
                           note="native-USB-CDC remote still (S3-Quirk)"),
    (0x0451, 0x16A8): dict(device="CC2531 Zigbee",        role="802.15.4-Koordinator",
                           access=["USB-ZNP"], reset_safe=False),
    (0x1A86, 0x5722): dict(device="USB-Display (Fremd)",  role="NICHT Ökosystem",
                           access=[], reset_safe=False, ignore=True),
}

# Geräte, die das Ökosystem erwartet (für "fehlt gerade"-Hinweise)
EXPECTED = {"Flipper Zero", "ESP32-WROOM (Relay)", "Heltec LoRa v3",
            "LilyGo T-Dongle S3", "CC2531 Zigbee"}


def discover() -> list[dict]:
    """Liste aller erkannten Ökosystem-Geräte mit Port + Zugangswegen."""
    out = []
    for p in serial.tools.list_ports.comports():
        key = (p.vid, p.pid) if p.vid is not None else None
        info = KNOWN.get(key)
        entry = dict(port=p.device, vid=p.vid, pid=p.pid, description=p.description)
        if info:
            entry.update(info)
        else:
            entry.update(device="unbekannt", role="?", access=[], reset_safe=False, unknown=True)
        out.append(entry)
    return out


def missing() -> list[str]:
    """Erwartete Ökosystem-Geräte, die gerade NICHT angeschlossen sind."""
    present = {d["device"] for d in discover()}
    return sorted(EXPECTED - present)


def find_port(device_name: str) -> str | None:
    for d in discover():
        if d["device"] == device_name:
            return d["port"]
    return None


def open_safe(port: str, baud: int = 115200, reset_to_run: bool = True) -> serial.Serial:
    """Reset-sicheres Öffnen: DTR/RTS deassertieren, damit ESP-Boards nicht im
    Bootloader stranden. Mit reset_to_run zusätzlich EN-Puls (RTS) -> Firmware bootet.
    (CP210x/CH9102: RTS->EN, DTR->BOOT.)"""
    s = serial.Serial(port, baud, timeout=0.2)
    s.setDTR(False)                      # BOOT high = normaler Firmware-Boot
    if reset_to_run:
        s.setRTS(True); time.sleep(0.12); s.setRTS(False)   # EN low->high
        time.sleep(2.4)                  # Boot abwarten
    else:
        s.setRTS(False)
    s.reset_input_buffer()
    return s


def _fmt(d: dict) -> str:
    tag = "  (ignoriert)" if d.get("ignore") else ("  (?)" if d.get("unknown") else "")
    acc = " · ".join(d.get("access", [])) or "—"
    note = f"  [{d['note']}]" if d.get("note") else ""
    vid = f"{d['vid']:04X}:{d['pid']:04X}" if d.get("vid") else "----:----"
    return f"  {d['port']:<7} {vid}  {d['device']:<22} {acc}{note}{tag}"


if __name__ == "__main__":
    devs = discover()
    print("=== G4MEOVER Geräte-Discovery ===")
    for d in devs:
        print(_fmt(d))
    miss = missing()
    if miss:
        print("\nnicht angeschlossen:", ", ".join(miss))
