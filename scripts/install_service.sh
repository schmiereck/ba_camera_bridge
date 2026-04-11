#!/usr/bin/env bash
# Install (or refresh) the ba-camera-bridge systemd service on ubuntu1.
#
# Usage (run on the Pi):
#     cd ~/ros2_ws/src/ba_camera_bridge
#     ./scripts/install_service.sh
#
# The script is idempotent — safe to run after every pull/build.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
UNIT_SRC="${REPO_DIR}/systemd/ba-camera-bridge.service"
UNIT_DST="/etc/systemd/system/ba-camera-bridge.service"

if [[ ! -f "${UNIT_SRC}" ]]; then
    echo "ERROR: unit file not found at ${UNIT_SRC}" >&2
    exit 1
fi

echo ">> Installing ${UNIT_DST}"
sudo install -m 0644 "${UNIT_SRC}" "${UNIT_DST}"

echo ">> systemctl daemon-reload"
sudo systemctl daemon-reload

echo ">> systemctl enable ba-camera-bridge.service"
sudo systemctl enable ba-camera-bridge.service

echo
echo "Service installed. Use:"
echo "    sudo systemctl start   ba-camera-bridge"
echo "    sudo systemctl stop    ba-camera-bridge"
echo "    sudo systemctl restart ba-camera-bridge"
echo "    systemctl status       ba-camera-bridge"
echo "    journalctl -u ba-camera-bridge -f"
