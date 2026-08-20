#!/usr/bin/env python3
"""G4MEOVER Deck — WPA-Cracker-CLI.

Frontend für deck/wpa_crack.py. Nimmt ein .pcap (z.B. aus einem 0x25-Handshake-Capture),
konvertiert es und knackt per Wörterliste oder Maske.

  python wpa_crack.py detect
  python wpa_crack.py info   capture.pcap
  python wpa_crack.py dict   capture.pcap rockyou.txt
  python wpa_crack.py mask   capture.pcap "?d?d?d?d?d?d?d?d"
  python wpa_crack.py show   capture.hc22000

Nur für autorisierte Sicherheitstests an eigenen Netzen.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # deck/ importierbar
import wpa_crack as wc  # noqa: E402


def _print_networks(nets):
    if not nets:
        print("  (keine Netze/Handshakes)")
        return
    for n in nets:
        print(f"  [{n.get('kind','?'):5}] {n['bssid']}  SSID={n['ssid']!r}")


def _print_cracked(res):
    if res.get("error"):
        print(f"  Hinweis: {res['error']}")
    cracked = res.get("cracked", [])
    if not cracked:
        print("  Noch nichts geknackt.")
        return
    print("  GEKNACKT:")
    for c in cracked:
        print(f"    {c['bssid']}  SSID={c['ssid']!r}  ->  PW={c['password']!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description="WPA/WPA2-Handshake-Cracker (Deck).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("detect", help="Pipeline-Tools prüfen")
    p_info = sub.add_parser("info", help=".pcap -> Handshakes/Netze auflisten")
    p_info.add_argument("pcap")
    p_dict = sub.add_parser("dict", help="Dictionary-Angriff")
    p_dict.add_argument("pcap"); p_dict.add_argument("wordlist")
    p_dict.add_argument("--timeout", type=int, default=3600)
    p_mask = sub.add_parser("mask", help="Bruteforce per Maske")
    p_mask.add_argument("pcap"); p_mask.add_argument("mask")
    p_mask.add_argument("--timeout", type=int, default=3600)
    p_show = sub.add_parser("show", help="Bereits geknackte (Potfile) anzeigen")
    p_show.add_argument("hc22000")
    args = ap.parse_args()

    if args.cmd == "detect":
        d = wc.detect()
        print("Pipeline:", "BEREIT" if d["ready"] else "NICHT bereit")
        print(f"  hcxpcapngtool: {'ok' if d['hcxpcapngtool'] else 'FEHLT'}")
        print(f"  hashcat:       {'ok' if d['hashcat'] else 'FEHLT'}")
        if d["error"]:
            print("  ->", d["error"])
        return 0 if d["ready"] else 1

    if args.cmd == "show":
        _print_cracked({"cracked": wc.show_cracked(args.hc22000)})
        return 0

    # info/dict/mask: erst konvertieren
    conv = wc.pcap_to_hc22000(args.pcap)
    if conv.get("error") and not conv.get("hc22000"):
        print("Fehler:", conv["error"]); return 1
    print(f"Handshakes/PMKID gefunden: {conv['count']} -> {conv.get('hc22000')}")
    _print_networks(conv["networks"])
    if args.cmd == "info":
        return 0
    if conv["count"] == 0:
        print("Nichts zu knacken."); return 1

    if args.cmd == "dict":
        print(f"\nDictionary-Angriff mit {args.wordlist} ...")
        _print_cracked(wc.crack_dictionary(conv["hc22000"], args.wordlist, timeout=args.timeout))
    elif args.cmd == "mask":
        print(f"\nBruteforce mit Maske {args.mask} ...")
        _print_cracked(wc.crack_mask(conv["hc22000"], args.mask, timeout=args.timeout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
