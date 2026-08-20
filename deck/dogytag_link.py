#!/usr/bin/env python3
"""G4MEOVER Deck — DogyTag-Link (LoRaWAN/TTN-Telemetrie, read-only).

Bindet das bestehende DogyTag-Ökosystem **additiv** ans Deck an: abonniert den lokalen
mosquitto-Broker (der von der TTN-Bridge gespeist wird) als ZUSÄTZLICHER read-only
Subscriber. MQTT ist pub/sub — das berührt die Produktions-Pipeline (LORIX→TTN→Bridge→
mosquitto→WebUI) in KEINER Weise. Es wird nichts published, nichts umkonfiguriert.

Datenfluss (siehe project_dogytag_ttn_infra):
    DogyTag → LoRaWAN → LORIX One → TTN(dogytag-v1) → ttn_bridge → mosquitto → [hier lesen]

Topics: dogytag/<device>/{status,telemetry,lora,433,wifi_seen,event}

Nur eigene Infrastruktur. Broker-Zugang via Env überschreibbar.
"""
from __future__ import annotations
import json
import os
import time

BROKER_HOST = os.getenv("DOGYTAG_MQTT_HOST", "192.168.0.80")
BROKER_PORT = int(os.getenv("DOGYTAG_MQTT_PORT", "1883"))
BROKER_USER = os.getenv("DOGYTAG_MQTT_USER", "yanis")
BROKER_PASS = os.getenv("DOGYTAG_MQTT_PASS", "12345678")
TOPIC = os.getenv("DOGYTAG_TOPIC", "dogytag/#")


def _client():
    import paho.mqtt.client as mqtt
    try:  # paho v2 API
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except (AttributeError, TypeError):  # paho v1
        c = mqtt.Client()
    if BROKER_USER:
        c.username_pw_set(BROKER_USER, BROKER_PASS)
    return c


def detect() -> dict:
    """Broker erreichbar + paho da? Liefert {ready, error}."""
    try:
        import paho.mqtt.client  # noqa: F401
    except ImportError:
        return {"ready": False, "error": "paho-mqtt fehlt (pip install paho-mqtt)"}
    try:
        c = _client()
        c.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
        c.disconnect()
        return {"ready": True, "broker": f"{BROKER_HOST}:{BROKER_PORT}", "error": ""}
    except Exception as e:  # noqa: BLE001
        return {"ready": False, "error": f"Broker {BROKER_HOST}:{BROKER_PORT} nicht erreichbar: {e}"}


def snapshot(seconds: float = 8.0) -> dict:
    """Hört `seconds` mit und aggregiert je Gerät den letzten Stand.
    Liefert {devices: {id: {status,telemetry,...}}, messages, error}."""
    try:
        import paho.mqtt.client  # noqa: F401
    except ImportError:
        return {"devices": {}, "messages": 0, "error": "paho-mqtt fehlt"}
    devices: dict[str, dict] = {}
    count = [0]

    def on_message(client, userdata, msg):
        count[0] += 1
        parts = msg.topic.split("/")
        if len(parts) < 3:
            return
        dev, kind = parts[1], parts[2]
        try:
            payload = json.loads(msg.payload.decode("utf-8", "replace"))
        except (ValueError, UnicodeDecodeError):
            payload = {"_raw": msg.payload[:80].hex()}
        devices.setdefault(dev, {})[kind] = payload

    try:
        c = _client()
        c.on_message = on_message
        c.connect(BROKER_HOST, BROKER_PORT, keepalive=10)
        c.subscribe(TOPIC, qos=0)
        c.loop_start()
        time.sleep(seconds)
        c.loop_stop()
        c.disconnect()
    except Exception as e:  # noqa: BLE001
        return {"devices": devices, "messages": count[0], "error": str(e)}
    return {"devices": devices, "messages": count[0], "error": ""}


def summarize(snap: dict) -> list[dict]:
    """Verdichtet snapshot() zu einer Geräte-Kachelliste (fürs Dashboard/Lagebild)."""
    out = []
    for dev, kinds in sorted(snap.get("devices", {}).items()):
        st = kinds.get("status", {})
        tel = kinds.get("telemetry", {})
        out.append({
            "device": dev,
            "online": st.get("online"),
            "state": st.get("state") or tel.get("state"),
            "joined": st.get("joined", tel.get("joined")),
            "bat_pct": st.get("bat_pct"),
            "bat_mv": st.get("bat_mv") or tel.get("bat_mv"),
            "gw_rssi": st.get("gw_rssi") or tel.get("gw_rssi"),
            "mode": st.get("mode") or tel.get("mode"),
            "fw": st.get("fw"),
            "radio": "LoRaWAN/Mesh",
        })
    return out


if __name__ == "__main__":
    d = detect()
    print("detect:", d)
    if d["ready"]:
        print("Snapshot (8s)...")
        snap = snapshot(8)
        print(f"{snap['messages']} Nachrichten, {len(snap['devices'])} Geräte")
        for row in summarize(snap):
            print(f"  {row['device']:12} state={row['state']} joined={row['joined']} "
                  f"bat={row['bat_pct']}% gw_rssi={row['gw_rssi']} mode={row['mode']}")
