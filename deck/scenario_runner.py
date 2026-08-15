#!/usr/bin/env python3
"""G4MEOVER Deck — Szenario-Runner.

Fährt reproduzierbare Pentest-Szenarien über den Geräte-/Funk-Router und protokolliert
jede Aktion als {action, device, radio, status, ts} — die Grundlage des Labors, in dem
viele Leute bekannte Szenarien fahren, verbessern und re-testen.

Szenario-Format (JSON, `scenarios/<name>.json`):
  {
    "name": "...", "description": "...",
    "requires": ["ESP32-WROOM (Relay)", "Heltec LoRa v3"],
    "watch": "Heltec LoRa v3",
    "steps": [
      {"type":"precheck"},
      {"type":"sat","action":"ping","expect":"ESPNOW OK","repeat":3},
      {"type":"sat","action":"trigger","id":0,"expect":"cmd=0x02"},
      {"type":"wait","seconds":1},
      {"type":"note","text":"..."}
    ]
  }

Transport (Dev-Box/Labor): treibt die WROOM-CLI über deren USB-Port (auto-erkannt) und
beobachtet den Satelliten. Auf dem Pi ersetzt satellite_link den UART-Weg (gleiche Frames).
"""
from __future__ import annotations
import glob
import json
import os
import time

import device_discovery as dd
import ukfe_rf

SCEN_DIR = os.environ.get(
    "DECK_SCENARIOS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenarios"))


def _ts() -> str:
    return time.strftime("%H:%M:%S")


def envelope(action, device, radio, status, **extra) -> dict:
    return {"action": action, "device": device, "radio": radio, "status": status,
            "ts": _ts(), **extra}


def list_scenarios() -> list[str]:
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(SCEN_DIR, "*.json")))


def load(name: str) -> dict:
    path = os.path.join(SCEN_DIR, name + ".json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _drain(s, secs: float) -> None:
    end = time.time() + secs
    while time.time() < end:
        s.readline()


def _watch(h, needle: str, secs: float) -> bool:
    if not h:
        return False
    end = time.time() + secs
    while time.time() < end:
        line = h.readline()
        if line and needle.encode() in line:
            return True
    return False


def run(scenario: dict, dry_run: bool = False):
    """Führt ein Szenario aus. Gibt (report, passed) zurück."""
    report: list[dict] = []
    requires = scenario.get("requires", [])
    watch_dev = scenario.get("watch")
    present = {d["device"] for d in dd.discover()}
    missing = [r for r in requires if r not in present]

    report.append(envelope("precheck", "Deck", "USB", "ok" if not missing else "fail",
                            requires=requires, missing=missing))
    if missing and not dry_run:
        return report, False

    wroom_port = dd.find_port("ESP32-WROOM (Relay)")
    watch_port = dd.find_port(watch_dev) if watch_dev else None
    w = h = None
    passed = True
    counter = 5000  # > Satelliten-enowCounter (nach Reset 0); monoton im Lauf

    try:
        if not dry_run:
            if wroom_port:
                w = dd.open_safe(wroom_port); _drain(w, 0.3)
            if watch_port:
                h = dd.open_safe(watch_port); _drain(h, 0.3)

        for step in scenario.get("steps", []):
            t = step.get("type")
            if t == "precheck":
                continue  # schon oben erledigt
            elif t == "note":
                report.append(envelope("note", "—", "—", "ok", text=step.get("text", "")))
            elif t == "wait":
                sec = step.get("seconds", 1)
                if not dry_run:
                    time.sleep(sec)
                report.append(envelope("wait", "—", "—", "ok", seconds=sec))
            elif t == "sat":
                for _ in range(step.get("repeat", 1)):
                    counter += 1
                    ok = _run_sat(step, w, h, dry_run, counter, report)
                    passed = passed and ok
            elif t == "flipper":
                _run_flipper(step, dry_run, report)
            elif t == "zigbee":
                passed = _run_zigbee(step, dry_run, report) and passed
            elif t == "sdr":
                passed = _run_sdr(step, dry_run, report) and passed
            else:
                report.append(envelope(t or "?", "—", "—", "skipped"))
    finally:
        for s in (w, h):
            if s:
                s.close()
    return report, passed


def _run_sat(step, w, h, dry_run, counter, report) -> bool:
    action = step.get("action", "ping")
    expect = step.get("expect")               # optionaler String am watch-Gerät
    want_ack = step.get("ack", not expect)    # Default: Ergebnis via WROOM-ACK prüfen
    if dry_run:
        report.append(envelope(f"sat:{action}", "Satelliten", "ESP-NOW", "planned",
                               counter=counter, verify="ack" if want_ack else "watch"))
        return True
    if not w:
        report.append(envelope(f"sat:{action}", "Satelliten", "ESP-NOW", "error",
                               error="WROOM-Relay nicht erreichbar"))
        return False
    if h:
        h.reset_input_buffer()
    w.reset_input_buffer()   # für den zurückkommenden ACK
    # Befehl an WROOM-CLI: 'ping' (STATUS) oder ukfe_rf-Frame via 'hex'
    if action in ("ping", "status"):
        w.write(b"ping\n")
    elif action == "trigger":
        frame = ukfe_rf.make_trigger(ukfe_rf.DEFAULT_SECRET, counter, int(step.get("id", 0)))
        w.write(b"hex " + " ".join(f"{b:02X}" for b in frame).encode() + b"\n")
    else:
        report.append(envelope(f"sat:{action}", "Satelliten", "ESP-NOW", "skipped"))
        return True
    time.sleep(0.4)
    ok = True
    detail = {"counter": counter}
    if expect:
        ok = _watch(h, expect, 1.2) and ok
        detail["expect"] = expect
    if want_ack:
        # Der WROOM leitet den signierten Satelliten-ACK auf USB weiter ("resp=").
        got = _watch(w, "resp=", 1.6)
        detail["ack"] = got
        ok = ok and got
    report.append(envelope(f"sat:{action}", "Satelliten", "ESP-NOW",
                           "ok" if ok else "fail", **detail))
    return ok


def _run_flipper(step, dry_run, report) -> None:
    cmd = step.get("cmd", "device_info")
    if dry_run:
        report.append(envelope(f"flipper:{cmd}", "Flipper Zero", "USB-RPC", "planned"))
        return
    try:
        import flipper_link
        with flipper_link.FlipperLink() as fl:
            out = fl.raw(cmd)
        report.append(envelope(f"flipper:{cmd}", "Flipper Zero", "USB-RPC", "ok",
                               output=out[:200]))
    except Exception as e:  # noqa: BLE001
        report.append(envelope(f"flipper:{cmd}", "Flipper Zero", "USB-RPC", "error", error=str(e)))


def _run_zigbee(step, dry_run, report) -> bool:
    action = step.get("action", "info")
    if dry_run:
        report.append(envelope(f"zigbee:{action}", "CC2531", "802.15.4", "planned"))
        return True
    port = dd.find_port("CC2531 Zigbee")
    if not port:
        report.append(envelope(f"zigbee:{action}", "CC2531", "802.15.4", "error",
                               error="CC2531 nicht erreichbar"))
        return False
    try:
        import zigbee_link
        with zigbee_link.ZigbeeLink(port) as z:
            info = z.info()
        ok = info["reachable"]
        report.append(envelope(f"zigbee:{action}", "CC2531", "802.15.4",
                               "ok" if ok else "fail",
                               capabilities=info["capabilities"], version=info["version"]))
        return ok
    except Exception as e:  # noqa: BLE001
        report.append(envelope(f"zigbee:{action}", "CC2531", "802.15.4", "error", error=str(e)))
        return False


def _run_sdr(step, dry_run, report) -> bool:
    action = step.get("action", "detect")
    if dry_run:
        report.append(envelope(f"sdr:{action}", "HackRF", "1MHz-6GHz", "planned"))
        return True
    try:
        import hackrf_link
        if action == "detect":
            d = hackrf_link.detect()
            report.append(envelope("sdr:detect", "HackRF", "1MHz-6GHz",
                                   "ok" if d.get("present") else "offline",
                                   serial=d.get("serial"), error=d.get("error")))
            return d.get("present", False)
        if action == "sweep":
            peaks = hackrf_link.sweep(int(step.get("start_mhz", 300)),
                                      int(step.get("stop_mhz", 930)))
            report.append(envelope("sdr:sweep", "HackRF", "1MHz-6GHz", "ok",
                                   found=len(peaks), top=peaks[:3]))
            return True
        report.append(envelope(f"sdr:{action}", "HackRF", "1MHz-6GHz", "skipped"))
        return True
    except Exception as e:  # noqa: BLE001
        report.append(envelope(f"sdr:{action}", "HackRF", "1MHz-6GHz", "error", error=str(e)))
        return False


def print_report(report, passed) -> None:
    print(f"\n{'ACTION':<20}{'DEVICE':<18}{'RADIO':<12}STATUS")
    print("-" * 62)
    for e in report:
        print(f"{e['action']:<20}{e['device']:<18}{e['radio']:<12}{e['status']}"
              + (f"  {e.get('error','')}" if e['status'] in ('fail', 'error') else ""))
    print("-" * 62)
    print("ERGEBNIS:", "BESTANDEN ✓" if passed else "FEHLGESCHLAGEN ✗")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Szenarien:", ", ".join(list_scenarios()) or "(keine)")
        sys.exit(0)
    dry = "--dry-run" in sys.argv
    rep, ok = run(load(sys.argv[1]), dry_run=dry)
    print_report(rep, ok)
    sys.exit(0 if ok else 1)
