#!/usr/bin/env python3
"""G4MEOVER Deck — Control-Daemon (HTTP-API).

Das Backend, an das die einheitliche Ökosystem-UI andockt ("alles an einem Punkt").
Bündelt Satelliten-Funk (ukfe_rf über Pi-UART) und Flipper (USB-RPC) hinter einer
schlanken lokalen HTTP-API — stdlib-only, keine Fremd-Deps, läuft als systemd-Dienst.

Endpunkte (GET/POST, JSON):
  GET  /status               -> Geräte, Funktechnologien, Counter
  POST /sat/ping             -> STATUS an Satelliten
  POST /sat/trigger  {id,delay}
  POST /sat/deauth   {bssid,channel}
  POST /sat/send     {cmd,args_hex?,label?}  -> generischer ukfe_rf-Befehl vom UI
  GET  /flipper/info
  GET  /lorawan              -> LoRa/TTN-Lagebild: LORIX-Gateway + TTN-Flotte + DogyTag-Telemetrie
Jede Antwort trägt {action, device, radio, status} — genau die Felder, die die UI zeigt.
"""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import satellite_link

HOST, PORT = "0.0.0.0", 8712
import os as _os
_link = satellite_link.SatelliteLink(
    port=_os.getenv("DECK_SAT_PORT", "/dev/serial0"),
    counter_file=_os.getenv("DECK_COUNTER_FILE",
                            "/var/lib/g4meover-deck/counter"))
DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")


def _envelope(action, device, radio, status, **extra):
    """Einheitliche Antwort — spiegelt die UI-Felder (Aktion/Gerät/Funk/Status)."""
    return {"action": action, "device": device, "radio": radio, "status": status, **extra}


def _flipper_port():
    try:
        import flipper_link
        return flipper_link.find_flipper()
    except Exception:  # noqa: BLE001
        return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return {}

    def log_message(self, *a):  # stiller Betrieb
        pass

    def _send_html(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self._send({"error": "dashboard.html fehlt"}, 404); return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_html(DASHBOARD)
        elif self.path == "/scenarios":
            try:
                import scenario_runner as sr
                self._send({"scenarios": sr.list_scenarios()})
            except Exception as e:  # noqa: BLE001
                self._send({"scenarios": [], "error": str(e)})
        elif self.path == "/status":
            devices = []
            try:
                import device_discovery as dd
                devices = [{"port": d["port"], "device": d["device"], "role": d.get("role"),
                            "access": d.get("access", [])}
                           for d in dd.discover() if not d.get("ignore")]
            except Exception:  # noqa: BLE001
                pass
            self._send({
                "deck": "G4MEOVER",
                "satellites_uart": _link.port,
                "flipper": _flipper_port() or "offline",
                "counter": _link._counter,
                "devices": devices,
                "radios": ["868-FSK", "ESP-NOW(2.4G)", "SubGHz-OOK", "NFC", "RFID", "IR", "BLE", "LoRaWAN/TTN"],
            })
        elif self.path == "/lorawan":
            # LoRa/TTN-Lagebild: Gateway (LORIX) + Flotte (TTN) + DogyTag-Telemetrie (mosquitto)
            out = _envelope("lorawan", "LORIX/TTN", "LoRaWAN", "ok")
            try:
                import lorix_link
                out["gateway"] = lorix_link.gateway_status()
                out["fleet"] = lorix_link.device_fleet()
            except Exception as e:  # noqa: BLE001
                out["status"] = "error"; out["error"] = str(e)
            try:
                import dogytag_link
                out["telemetry"] = dogytag_link.summarize(dogytag_link.snapshot(4))
            except Exception:  # noqa: BLE001
                pass
            self._send(out)
        elif self.path == "/flipper/info":
            try:
                import flipper_link
                with flipper_link.FlipperLink() as fl:
                    self._send(_envelope("info", "Flipper Zero", "USB-RPC", "ok", data=fl.info()))
            except Exception as e:  # noqa: BLE001
                self._send(_envelope("info", "Flipper Zero", "USB-RPC", "error", error=str(e)), 503)
        else:
            self._send({"error": "unknown endpoint"}, 404)

    def do_POST(self):
        b = self._body()
        try:
            if self.path == "/scenario/run":
                import scenario_runner as sr
                name = b.get("name", "")
                try:
                    scenario = sr.load(name)
                except FileNotFoundError:
                    self._send({"error": f"Szenario '{name}' nicht gefunden"}, 404); return
                report, passed = sr.run(scenario, dry_run=bool(b.get("dry_run", False)))
                self._send({"name": name, "passed": passed, "report": report})
            elif self.path == "/sat/ping":
                c = _link.status()
                self._send(_envelope("ping", "Satelliten", "ESP-NOW/868", "sent", counter=c))
            elif self.path == "/sat/trigger":
                c = _link.trigger(int(b.get("id", 0)), int(b.get("delay", 0)))
                self._send(_envelope("trigger", "Satelliten", "ESP-NOW/868", "sent",
                                     counter=c, id=b.get("id", 0)))
            elif self.path == "/sat/deauth":
                bssid = bytes(int(x, 16) for x in str(b["bssid"]).replace("-", ":").split(":"))
                c = _link.wifi_deauth(bssid, int(b.get("channel", 1)))
                self._send(_envelope("wifi_deauth", "ESP32-Satellit", "WiFi", "sent", counter=c))
            elif self.path == "/sat/send":
                # Generischer ukfe_rf-Befehl vom UI: {cmd:int, args_hex?:str} -> ueber Kette an Satelliten
                cmd = int(b.get("cmd"))
                args = bytes.fromhex(b["args_hex"]) if b.get("args_hex") else b""
                c = _link.send(cmd, args)
                self._send(_envelope("send", "Satelliten", "ESP-NOW/868", "sent",
                                     counter=c, cmd=f"0x{cmd:02X}", label=b.get("label", "")))
            else:
                self._send({"error": "unknown endpoint"}, 404)
        except Exception as e:  # noqa: BLE001
            self._send(_envelope(self.path, "Satelliten", "?", "error", error=str(e)), 500)


def main():
    print(f"G4MEOVER Deck-Daemon auf http://{HOST}:{PORT}  (UART {_link.port})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
