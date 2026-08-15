#!/usr/bin/env python3
"""G4MEOVER Deck — Kontroll-CLI.

Ein Werkzeug fuer beide Ebenen des Decks:
  * Satelliten (WROOM/LilyGo/Heltec) ueber die Pi-UART + ukfe_rf
  * Flipper Zero ueber USB-RPC (flipperbridge)

Beispiele:
  deck-ctl status
  deck-ctl sat ping
  deck-ctl sat trigger 1
  deck-ctl sat deauth AA:BB:CC:DD:EE:FF 6
  deck-ctl flipper info
  deck-ctl flipper ls /ext/apps/Sub-GHz
"""
from __future__ import annotations
import argparse
import configparser
import os
import sys

import satellite_link

CONFIG = "/etc/g4meover-deck/deck.conf"


def load_cfg() -> dict:
    cfg = {"uart_port": "/dev/serial0", "uart_baud": "115200",
           "counter_file": "/var/lib/g4meover-deck/counter"}
    p = configparser.ConfigParser()
    if os.path.exists(CONFIG):
        p.read(CONFIG)
        if p.has_section("satellites"):
            cfg.update({k: v for k, v in p.items("satellites")})
    return cfg


def make_link() -> satellite_link.SatelliteLink:
    c = load_cfg()
    return satellite_link.SatelliteLink(
        port=c["uart_port"], baud=int(c["uart_baud"]), counter_file=c["counter_file"])


def parse_mac(s: str) -> bytes:
    parts = s.replace("-", ":").split(":")
    if len(parts) != 6:
        raise argparse.ArgumentTypeError("BSSID muss 6 Hex-Oktette sein")
    return bytes(int(x, 16) for x in parts)


def cmd_sat(args) -> int:
    link = make_link()
    if args.action in ("ping", "status"):
        c = link.status()
    elif args.action == "trigger":
        c = link.trigger(args.id, args.delay)
    elif args.action == "deauth":
        c = link.wifi_deauth(parse_mac(args.bssid), args.channel)
    elif args.action == "evilportal":
        c = link.evil_portal(args.id)
    elif args.action == "beacon":
        c = link.beacon_spam(args.mode)
    elif args.action == "abort":
        c = link.abort()
    else:
        print("unbekannte sat-Aktion"); return 2
    print(f"gesendet: {args.action} (counter={c}) -> Satelliten")
    return 0


def cmd_flipper(args) -> int:
    try:
        import flipper_link
    except Exception as e:  # noqa: BLE001
        print(f"Flipper-Link nicht verfuegbar: {e}"); return 1
    try:
        with flipper_link.FlipperLink() as fl:
            if args.action == "info":
                for k, v in fl.info().items():
                    print(f"{k:28}: {v}")
            elif args.action == "ls":
                print(fl.storage_list(args.path))
            elif args.action == "raw":
                print(fl.raw(args.command))
            elif args.action == "launch":
                print(fl.launch(args.name) or "gestartet")
    except Exception as e:  # noqa: BLE001
        print(f"Fehler: {e}"); return 1
    return 0


def cmd_scenario(args) -> int:
    import scenario_runner as sr
    if args.action == "list":
        names = sr.list_scenarios()
        print("Szenarien:", ", ".join(names) if names else "(keine)")
        return 0
    if args.action == "run":
        try:
            scenario = sr.load(args.name)
        except FileNotFoundError:
            print(f"Szenario '{args.name}' nicht gefunden."); return 2
        print(f"Szenario: {scenario['name']} — {scenario.get('description','')}")
        report, passed = sr.run(scenario, dry_run=args.dry_run)
        sr.print_report(report, passed)
        return 0 if passed else 1
    return 2


def cmd_status(_args) -> int:
    print("=== G4MEOVER Deck ===")
    c = load_cfg()
    print(f"Satelliten-UART : {c['uart_port']} @ {c['uart_baud']}")
    # Rolling-Counter
    try:
        with open(c["counter_file"]) as f:
            print(f"Rolling-Counter : {f.read().strip()}")
    except OSError:
        print("Rolling-Counter : 0 (neu)")
    # Auto-erkannte Geraete
    try:
        import device_discovery as dd
        print("\nErkannte Geräte:")
        for d in dd.discover():
            if d.get("ignore"):
                continue
            acc = " · ".join(d.get("access", [])) or "—"
            print(f"  {d['port']:<10} {d['device']:<22} [{acc}]")
        miss = dd.missing()
        if miss:
            print("  nicht angeschlossen:", ", ".join(miss))
    except Exception as e:  # noqa: BLE001
        print(f"  (Discovery nicht verfügbar: {e})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="deck-ctl", description="G4MEOVER Deck Kontroll-CLI")
    sub = ap.add_subparsers(dest="group", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)

    s = sub.add_parser("sat", help="Satelliten kommandieren (ukfe_rf ueber UART)")
    ssub = s.add_subparsers(dest="action", required=True)
    ssub.add_parser("ping"); ssub.add_parser("status"); ssub.add_parser("abort")
    t = ssub.add_parser("trigger"); t.add_argument("id", type=int); t.add_argument("delay", type=int, nargs="?", default=0)
    d = ssub.add_parser("deauth"); d.add_argument("bssid"); d.add_argument("channel", type=int)
    e = ssub.add_parser("evilportal"); e.add_argument("id", type=int, nargs="?", default=0)
    b = ssub.add_parser("beacon"); b.add_argument("mode", type=int, nargs="?", default=0)
    s.set_defaults(func=cmd_sat)

    sc = sub.add_parser("scenario", help="Labor-Szenarien fahren (test->verbessern->re-test)")
    scsub = sc.add_subparsers(dest="action", required=True)
    scsub.add_parser("list")
    scr = scsub.add_parser("run"); scr.add_argument("name")
    scr.add_argument("--dry-run", action="store_true")
    sc.set_defaults(func=cmd_scenario)

    f = sub.add_parser("flipper", help="Flipper ueber USB-RPC")
    fsub = f.add_subparsers(dest="action", required=True)
    fsub.add_parser("info")
    fl = fsub.add_parser("ls"); fl.add_argument("path", nargs="?", default="/ext")
    fr = fsub.add_parser("raw"); fr.add_argument("command")
    fla = fsub.add_parser("launch"); fla.add_argument("name")
    f.set_defaults(func=cmd_flipper)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
