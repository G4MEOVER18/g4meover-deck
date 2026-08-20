#!/usr/bin/env python3
"""G4MEOVER Deck — WPA/WPA2-Handshake-Cracker.

Koppelt die von unserem `UkfeRfCmdHandshake` (0x25) an den Satelliten gecaptureten
EAPOL-.pcaps an die hashcat-Pipeline: `.pcap` -> `hcxpcapngtool` -> `.hc22000`
(hashcat-Modus 22000) -> `hashcat` (Dictionary oder Maske/Bruteforce). Damit schließt
sich der Kreis „Handshake mitschneiden (Funk) -> Passwort knacken (Deck/Rechenknoten)".

Portiert (Logik, nicht 1:1) aus grugnoymeme/flipperzero-CLI-wifi-cracker (MIT,
(c) 2023 47LeCoste) — hier als importierbares, nicht-interaktives Deck-Modul im Stil
der anderen `*_link.py`, mit strukturierten Rückgaben statt input()-Prompts.

Nur für autorisierte Sicherheitstests an eigenen Netzen.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess


HASHCAT_MODE = "22000"  # WPA-PBKDF2-PMKID+EAPOL


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def detect() -> dict:
    """Prüft die Pipeline-Tools. Liefert {ready, hcxpcapngtool, hashcat, error}."""
    hcx = _have("hcxpcapngtool")
    hc = _have("hashcat")
    err = ""
    if not hcx:
        err += "hcxpcapngtool fehlt (apt install hcxtools). "
    if not hc:
        err += "hashcat fehlt (apt install hashcat). "
    return {"ready": hcx and hc, "hcxpcapngtool": hcx, "hashcat": hc, "error": err.strip()}


def _fmt_mac(hexmac: str) -> str:
    """'aabbccddeeff' -> 'AA:BB:CC:DD:EE:FF'."""
    h = hexmac.strip().lower()
    return ":".join(h[i:i + 2] for i in range(0, len(h), 2)).upper() if len(h) == 12 else hexmac


def parse_hc22000(text: str) -> list[dict]:
    """Zerlegt hc22000-Zeilen -> [{ssid, bssid, kind}]. Format je Zeile:
    WPA*<01=PMKID|02=EAPOL>*<hash>*<mac_ap>*<mac_sta>*<essid_hex>*..."""
    nets: list[dict] = []
    for line in text.splitlines():
        f = line.strip().split("*")
        if len(f) < 6 or f[0] != "WPA":
            continue
        try:
            ssid = bytes.fromhex(f[5]).decode("utf-8", "replace")
        except ValueError:
            ssid = f[5]
        nets.append({
            "ssid": ssid,
            "bssid": _fmt_mac(f[3]),
            "kind": "PMKID" if f[1] == "01" else "EAPOL",
        })
    # nach (bssid,ssid) deduplizieren, Reihenfolge erhalten
    seen, out = set(), []
    for n in nets:
        k = (n["bssid"], n["ssid"])
        if k not in seen:
            seen.add(k); out.append(n)
    return out


def pcap_to_hc22000(pcap: str, out_path: str | None = None) -> dict:
    """Konvertiert .pcap/.cap/.pcapng -> .hc22000. Liefert
    {hc22000, networks:[...], count, error}."""
    if not _have("hcxpcapngtool"):
        return {"error": "hcxpcapngtool nicht installiert", "networks": [], "count": 0}
    if not os.path.isfile(pcap):
        return {"error": f"Datei nicht gefunden: {pcap}", "networks": [], "count": 0}
    out_path = out_path or (os.path.splitext(pcap)[0] + ".hc22000")
    try:
        subprocess.run(["hcxpcapngtool", "-o", out_path, pcap],
                       capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        return {"error": f"hcxpcapngtool-Fehler: {e}", "networks": [], "count": 0}
    if not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        return {"error": "keine Handshakes/PMKID im .pcap gefunden", "networks": [],
                "count": 0, "hc22000": out_path}
    nets = parse_hc22000(open(out_path, encoding="utf-8", errors="replace").read())
    return {"hc22000": out_path, "networks": nets, "count": len(nets), "error": ""}


def _run_hashcat(args: list[str], timeout: int) -> str:
    proc = subprocess.run(["hashcat", "-m", HASHCAT_MODE] + args,
                          capture_output=True, text=True, timeout=timeout)
    return (proc.stdout or "") + (proc.stderr or "")


def show_cracked(hc22000: str) -> list[dict]:
    """Liest bereits geknackte Passwörter aus hashcats Potfile (--show).
    Liefert [{ssid, bssid, password}]."""
    if not _have("hashcat") or not os.path.isfile(hc22000):
        return []
    out = _run_hashcat([hc22000, "--show"], timeout=60)
    results = []
    for line in out.splitlines():
        f = line.strip().split("*")
        if len(f) >= 6 and f[0] == "WPA":
            # letztes Feld hinter dem letzten ':' ist das Passwort
            pw = line.rsplit(":", 1)[-1] if ":" in line else ""
            try:
                ssid = bytes.fromhex(f[5]).decode("utf-8", "replace")
            except ValueError:
                ssid = f[5]
            results.append({"ssid": ssid, "bssid": _fmt_mac(f[3]), "password": pw})
    return results


def crack_dictionary(hc22000: str, wordlist: str, timeout: int = 3600,
                     extra: list[str] | None = None) -> dict:
    """Dictionary-Angriff (hashcat -a 0). Liefert {cracked:[...], error}."""
    if not _have("hashcat"):
        return {"cracked": [], "error": "hashcat nicht installiert"}
    if not os.path.isfile(hc22000):
        return {"cracked": [], "error": f"hc22000 fehlt: {hc22000}"}
    if not os.path.isfile(wordlist):
        return {"cracked": [], "error": f"Wörterliste fehlt: {wordlist}"}
    try:
        _run_hashcat([hc22000, "-a", "0", wordlist] + (extra or []), timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"cracked": show_cracked(hc22000), "error": "Timeout (Teilergebnis via Potfile)"}
    return {"cracked": show_cracked(hc22000), "error": ""}


def crack_mask(hc22000: str, mask: str, timeout: int = 3600,
               extra: list[str] | None = None) -> dict:
    """Bruteforce per Maske (hashcat -a 3, z.B. '?d?d?d?d?d?d?d?d' = 8 Ziffern).
    Liefert {cracked:[...], error}."""
    if not _have("hashcat"):
        return {"cracked": [], "error": "hashcat nicht installiert"}
    if not os.path.isfile(hc22000):
        return {"cracked": [], "error": f"hc22000 fehlt: {hc22000}"}
    if not re.fullmatch(r"[\?\w]+", mask):
        return {"cracked": [], "error": f"ungültige Maske: {mask}"}
    try:
        _run_hashcat([hc22000, "-a", "3", mask] + (extra or []), timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"cracked": show_cracked(hc22000), "error": "Timeout (Teilergebnis via Potfile)"}
    return {"cracked": show_cracked(hc22000), "error": ""}


if __name__ == "__main__":  # kleiner Selbsttest der Parser ohne Tools
    sample = ("WPA*02*deadbeef*a1b2c3d4e5f6*001122334455*47344d454f564552*0000\n"
              "WPA*01*cafef00d*aabbccddeeff*665544332211*4c696e6b737973*0001")
    for n in parse_hc22000(sample):
        print(n)
    print("detect:", detect())
