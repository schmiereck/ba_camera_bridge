#!/usr/bin/env bash
# Pull latest sources on ubuntu1, rebuild the package, and restart the service.
#
# Usage (run on the Pi):
#     ~/ros2_ws/src/ba_camera_bridge/scripts/deploy_ubuntu1.sh
#
# Or remotely from the Windows/WSL host:
#     ssh ubuntu@ubuntu1 '~/ros2_ws/src/ba_camera_bridge/scripts/deploy_ubuntu1.sh'

set -euo pipefail

REPO_DIR="${HOME}/ros2_ws/src/ba_camera_bridge"
WS_DIR="${HOME}/ros2_ws"

echo ">> git pull in ${REPO_DIR}"
git -C "${REPO_DIR}" pull --ff-only

echo ">> colcon build --packages-select ba_camera_bridge"
cd "${WS_DIR}"
# shellcheck disable=SC1091
source /opt/ros/humble/setup.bash
colcon build --packages-select ba_camera_bridge --symlink-install

# Reinstall the unit only if it changed since last install.
UNIT_SRC="${REPO_DIR}/systemd/ba-camera-bridge.service"
UNIT_DST="/etc/systemd/system/ba-camera-bridge.service"
if ! sudo cmp -s "${UNIT_SRC}" "${UNIT_DST}"; then
    echo ">> unit file changed -- reinstalling"
    "${REPO_DIR}/scripts/install_service.sh"
fi

echo ">> restarting ba-camera-bridge"
sudo systemctl restart ba-camera-bridge.service
sleep 1
systemctl --no-pager --full status ba-camera-bridge.service || true
