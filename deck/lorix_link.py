#!/usr/bin/env python3
"""G4MEOVER Deck — LORIX-One / TTN-LoRaWAN-Link (read-only).

Bindet das LoRaWAN-Weitverkehrs-Ohr des Ökosystems ans Deck: die LORIX-One-Gateway
(8-Kanal-Concentrator) + die TTN-Application, in der die DogyTag-Tracker registriert sind.
Während `dogytag_link.py` die Geräte-Telemetrie aus dem lokalen mosquitto liest (was die
Tracker melden), liefert dieses Modul die **Netz-Sicht** über die TTN-HTTP-API:
Gateway-Verbindung + registrierte Geräte-Flotte + deren Join/Session-Status.

Zusammen ergeben beide das LoRa/TTN-Lagebild im Deck (analog hackrf_link/zigbee_link).

TTN-API-Key kommt aus der Umgebung (`DOGYTAG_TTN_KEY`) oder gitignored `secret_local.py`
(Variable `TTN_KEY`) — NIE hardcoden (Repo ist public). Nur eigene Infrastruktur, read-only.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request

BASE = os.getenv("TTN_BASE", "https://eu1.cloud.thethings.network")
APP = os.getenv("DOGYTAG_TTN_APP", "dogytag-v1")
GATEWAY = os.getenv("DOGYTAG_TTN_GATEWAY", "dogytag-lorix-one")


def _key() -> str | None:
    k = os.getenv("DOGYTAG_TTN_KEY")
    if k:
        return k
    try:  # gitignored lokaler Override (deck/secret_local.py)
        from secret_local import TTN_KEY  # type: ignore
        return TTN_KEY
    except Exception:
        return None


def _get(path: str, key: str) -> tuple[int, dict | str]:
    req = urllib.request.Request(BASE + path)
    req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def detect() -> dict:
    """TTN erreichbar + Key gültig? Liefert {ready, app, error}."""
    key = _key()
    if not key:
        return {"ready": False, "error": "kein TTN-Key (env DOGYTAG_TTN_KEY / secret_local.TTN_KEY)"}
    st, body = _get(f"/api/v3/applications/{APP}", key)
    if st == 200:
        return {"ready": True, "app": APP, "error": ""}
    return {"ready": False, "error": f"TTN {st}: {str(body)[:120]}"}


def gateway_status() -> dict:
    """LORIX-Gateway-Verbindung (Gateway Server stats). Liefert {connected, ...} oder {error}."""
    key = _key()
    if not key:
        return {"error": "kein TTN-Key"}
    st, body = _get(f"/api/v3/gs/gateways/{GATEWAY}/connection/stats", key)
    if st == 200 and isinstance(body, dict):
        return {"gateway": GATEWAY, "connected": True,
                "last_uplink": body.get("last_uplink_received_at"),
                "uplink_count": body.get("uplink_count"),
                "downlink_count": body.get("downlink_count"),
                "protocol": body.get("protocol")}
    if st == 404:
        return {"gateway": GATEWAY, "connected": False, "note": "aktuell nicht verbunden (404)"}
    return {"gateway": GATEWAY, "error": f"TTN {st}: {str(body)[:100]}"}


def device_fleet() -> dict:
    """Registrierte Geräte in der App + je Gerät Join/Session-Status (NS).
    Liefert {devices:[{id, dev_eui, joined, dev_addr}], count, error}."""
    key = _key()
    if not key:
        return {"devices": [], "count": 0, "error": "kein TTN-Key"}
    st, body = _get(f"/api/v3/applications/{APP}/devices?field_mask=ids", key)
    if st != 200 or not isinstance(body, dict):
        return {"devices": [], "count": 0, "error": f"TTN {st}: {str(body)[:100]}"}
    out = []
    for d in body.get("end_devices", []):
        dev_id = d.get("ids", {}).get("device_id")
        sst, sbody = _get(
            f"/api/v3/ns/applications/{APP}/devices/{dev_id}?field_mask=session.dev_addr", key)
        dev_addr = None
        if sst == 200 and isinstance(sbody, dict):
            dev_addr = sbody.get("session", {}).get("dev_addr")
        out.append({"id": dev_id, "dev_eui": d.get("ids", {}).get("dev_eui"),
                    "joined": bool(dev_addr), "dev_addr": dev_addr})
    return {"devices": out, "count": len(out), "error": ""}


if __name__ == "__main__":
    print("detect:", detect())
    print("gateway:", gateway_status())
    fleet = device_fleet()
    print(f"fleet: {fleet['count']} Geräte" + (f" (err {fleet['error']})" if fleet["error"] else ""))
    for d in fleet["devices"]:
        j = "JOINED" if d["joined"] else "—"
        print(f"  {d['id']:22} {d['dev_eui'] or '':16} {j} {d['dev_addr'] or ''}")
