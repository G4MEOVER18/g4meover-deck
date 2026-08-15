#!/usr/bin/env python3
"""G4MEOVER Deck — HackRF-One-Link (Wide-Band-SDR).

Die HackRF One (1 MHz–6 GHz, TX/RX) ist das „Universal-Radio" des Decks: sie deckt
die Frequenzen/Modulationen ab, die Flipper (CC1101, 300–928 MHz OOK/FSK) und die
ESP-Satelliten (2,4 GHz) NICHT erreichen. Wrapper um die hackrf-CLI-Tools
(`hackrf_info`, `hackrf_sweep`, `hackrf_transfer`) — auf dem Pi via apt installiert.

Rolle im Ökosystem: der Deck-Router schickt Aktionen, die außerhalb der Flipper-/ESP-
Bänder liegen, an die HackRF (Recon-Sweep, Out-of-Band-Capture/Replay, GPS-Sim …).

Nur für autorisierte Sicherheitstests auf eigenen Geräten / in abgeschirmter Umgebung.
"""
from __future__ import annotations
import shutil
import subprocess


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def detect() -> dict:
    """HackRF vorhanden? Liefert {present, serial, error}."""
    if not _have("hackrf_info"):
        return {"present": False, "error": "hackrf-tools nicht installiert (apt install hackrf)"}
    try:
        out = subprocess.run(["hackrf_info"], capture_output=True, text=True, timeout=8).stdout
    except Exception as e:  # noqa: BLE001
        return {"present": False, "error": str(e)}
    if "Serial number" in out or "Found HackRF" in out:
        serial = ""
        for line in out.splitlines():
            if "Serial number" in line:
                serial = line.split(":", 1)[-1].strip()
        return {"present": True, "serial": serial}
    return {"present": False, "error": "keine HackRF gefunden (angeschlossen?)"}


def sweep(start_mhz: int, stop_mhz: int, bin_width_hz: int = 100000,
          one_shot: bool = True) -> list[dict]:
    """Wide-Band-Spektrum-Sweep. Gibt die stärksten Bins zurück (Freq/dBm).
    Bereich z.B. 300–930 (sub-GHz) oder 1–6000 (alles). Nutzt hackrf_sweep."""
    if not _have("hackrf_sweep"):
        raise RuntimeError("hackrf_sweep nicht installiert")
    cmd = ["hackrf_sweep", "-f", f"{start_mhz}:{stop_mhz}", "-w", str(bin_width_hz)]
    if one_shot:
        cmd += ["-1"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    peaks: list[dict] = []
    # CSV: date, time, hz_low, hz_high, hz_bin_width, num_samples, dB, dB, ...
    for line in proc.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        try:
            hz_low = int(parts[2]); bin_w = int(parts[4])
            dbs = [float(x) for x in parts[6:]]
        except ValueError:
            continue
        for i, db in enumerate(dbs):
            peaks.append({"freq_mhz": round((hz_low + i * bin_w) / 1e6, 3), "dbm": db})
    peaks.sort(key=lambda p: p["dbm"], reverse=True)
    return peaks[:20]  # Top-20-Signale


def capture(freq_mhz: float, seconds: float, path: str, sample_rate: int = 8_000_000) -> bool:
    """Roh-IQ aufnehmen (für spätere Analyse mit URH/GNU Radio auf dem Deck)."""
    if not _have("hackrf_transfer"):
        raise RuntimeError("hackrf_transfer nicht installiert")
    n = int(sample_rate * seconds)
    r = subprocess.run(["hackrf_transfer", "-r", path, "-f", str(int(freq_mhz * 1e6)),
                        "-s", str(sample_rate), "-n", str(n), "-l", "32", "-g", "40"],
                       capture_output=True, text=True, timeout=seconds + 15)
    return r.returncode == 0


def transmit(path: str, freq_mhz: float, sample_rate: int = 8_000_000) -> bool:
    """IQ-Datei senden (Out-of-Band-Replay). NUR autorisiert / abgeschirmt!
    Deckt Frequenzen ab, die Flipper/ESP nicht können."""
    if not _have("hackrf_transfer"):
        raise RuntimeError("hackrf_transfer nicht installiert")
    r = subprocess.run(["hackrf_transfer", "-t", path, "-f", str(int(freq_mhz * 1e6)),
                        "-s", str(sample_rate), "-x", "20"],
                       capture_output=True, text=True, timeout=120)
    return r.returncode == 0


# Bekannte Ziel-Frequenzen ausserhalb der Flipper/ESP-Reichweite (autorisierte Tests)
OUT_OF_BAND = {
    "gps_l1": 1575.42,   # GPS-Simulation/-Test
    "adsb": 1090.0,      # Flugzeug-Transponder
    "acars": 131.55,     # Flug-Datenlink
    "ais": 161.975,      # Schiffs-AIS
    "pager_vhf": 148.0,  # POCSAG VHF
}


if __name__ == "__main__":
    import json
    print(json.dumps(detect(), ensure_ascii=False))
