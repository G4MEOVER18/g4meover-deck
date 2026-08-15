#!/usr/bin/env bash
# G4MEOVER Deck — Provisioning für Raspberry Pi OS (Bookworm, Pi 4).
# Verwandelt ein frisches Raspberry Pi OS Lite in das Ökosystem-"Gehirn":
# Satelliten-Funk (ukfe_rf/UART) + Flipper (USB-RPC) hinter Daemon + CLI.
#
#   sudo bash install.sh
#
# Idempotent — mehrfach ausführbar.
set -euo pipefail

PREFIX=/opt/g4meover-deck
CFGDIR=/etc/g4meover-deck
STATEDIR=/var/lib/g4meover-deck
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> G4MEOVER Deck-Installation"
[ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo ausführen."; exit 1; }

echo "==> Pakete"
apt-get update -qq
apt-get install -y --no-install-recommends python3 python3-venv python3-serial git
# HackRF-One-Tools (Wide-Band-SDR, optional aber empfohlen)
apt-get install -y --no-install-recommends hackrf 2>/dev/null || echo '   (hackrf-Paket optional)'

echo "==> UART freischalten (GPIO14/15 für Satelliten-Link)"
CONFIG_TXT=/boot/firmware/config.txt
[ -f "$CONFIG_TXT" ] || CONFIG_TXT=/boot/config.txt
grep -q "^enable_uart=1" "$CONFIG_TXT" || echo "enable_uart=1" >> "$CONFIG_TXT"
# serielle Login-Konsole abschalten (sonst belegt sie die UART)
systemctl disable --now serial-getty@ttyAMA0.service 2>/dev/null || true
systemctl disable --now serial-getty@ttyS0.service 2>/dev/null || true
sed -i 's/console=serial0,[0-9]* //' /boot/firmware/cmdline.txt 2>/dev/null || \
  sed -i 's/console=serial0,[0-9]* //' /boot/cmdline.txt 2>/dev/null || true

echo "==> Dateien nach $PREFIX"
mkdir -p "$PREFIX" "$CFGDIR" "$STATEDIR"
cp -r "$REPO_DIR/deck" "$PREFIX/"

echo "==> flipperbridge vendoren (g4meover-companion)"
mkdir -p "$PREFIX/vendor"
if [ ! -f "$PREFIX/vendor/flipperbridge.py" ]; then
  TMP=$(mktemp -d)
  if git clone --depth 1 https://github.com/G4MEOVER18/g4meover-companion "$TMP" 2>/dev/null; then
    cp "$TMP/flipperbridge/flipperbridge.py" "$PREFIX/vendor/" 2>/dev/null || \
      echo "   (flipperbridge nicht gefunden — Flipper-Funktionen später nachrüsten)"
  else
    echo "   (companion-Repo nicht erreichbar — Flipper-Funktionen optional)"
  fi
  rm -rf "$TMP"
fi

echo "==> venv + pyserial"
python3 -m venv "$PREFIX/venv"
"$PREFIX/venv/bin/pip" install -q --upgrade pip pyserial

echo "==> Konfiguration"
if [ ! -f "$CFGDIR/deck.conf" ]; then
  cp "$REPO_DIR/config/deck.conf.example" "$CFGDIR/deck.conf"
fi

echo "==> deck-ctl in PATH"
cat > /usr/local/bin/deck-ctl <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$PREFIX/deck:$PREFIX/vendor"
exec "$PREFIX/venv/bin/python" "$PREFIX/deck/deck_ctl.py" "\$@"
EOF
chmod +x /usr/local/bin/deck-ctl

echo "==> systemd-Dienst"
cp "$REPO_DIR/systemd/g4meover-deck.service" /etc/systemd/system/
sed -i "s#@PREFIX@#$PREFIX#g" /etc/systemd/system/g4meover-deck.service
systemctl daemon-reload
systemctl enable g4meover-deck.service

echo
echo "==> FERTIG. Nach einem Reboot (UART aktiv):"
echo "     deck-ctl status"
echo "     deck-ctl sat ping"
echo "     systemctl status g4meover-deck   # HTTP-API auf :8712"
