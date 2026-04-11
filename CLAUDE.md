# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A ROS2 `ament_python` package that publishes the overview USB camera of the BA robot arm as a compressed image topic. The package itself contains **no custom node** — it is a thin wrapper (launch file + YAML + systemd unit) around the upstream `v4l2_camera_node` from `ros-humble-v4l2-camera`. Keep it that way unless there is a real reason to write Python node code: the goal is "standard-mittel", not reinvention.

A second camera (gripper cam) will likely be added to this same package later as an additional launch file under the same namespace scheme.

## Topic contract (stable — do not rename casually)

The launch file starts the node inside the namespace **`/ba_overview_camera`**, so consumers see:

- `/ba_overview_camera/image_raw` — raw `sensor_msgs/Image`, intended for local/Pi-side use only
- `/ba_overview_camera/image_raw/compressed` — JPEG `sensor_msgs/CompressedImage`, **this is what the WSL2 laptop subscribes to**
- `/ba_overview_camera/camera_info` — `sensor_msgs/CameraInfo` (empty intrinsics until calibration is run)

The `ba_` prefix is the robot prefix. When the gripper cam is added it will live under `/ba_gripper_camera/*` in the same package.

## Environment (must match across all hosts)

- `ROS_DISTRO=humble`
- `ROS_DOMAIN_ID=1`
- `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`

These are hard-coded in the systemd unit (`systemd/ba-camera-bridge.service`). The WSL2 laptop and the `BAArduinoController` Pi node use the same values — any deviation breaks discovery silently.

## Hosts and their roles

| Host | Role | ROS2 workspace |
|---|---|---|
| `ubuntu1.local` (Raspberry Pi, Ubuntu 22.04 arm64) | Runs the camera publisher as systemd service. Camera is a Logitech C930e on `/dev/video0`. Also runs `BAArduinoController` ROS2 bridge. | `~/ros2_ws` (this repo lives under `~/ros2_ws/src/ba_camera_bridge`) |
| WSL2 `Ubuntu-22.04` on the Windows dev laptop | Consumer (RViz, MoveIt, VLM + Depth Anything V2). ROS2 is installed but **not** auto-sourced in `~/.bashrc` — source it manually or in scripts. | N/A for this repo |
| Windows host (this working directory) | Edit + commit + push only. No ROS2 here. | N/A |

The `ubuntu1-ssh-login` skill is available: `ssh ubuntu@ubuntu1` works key-based, `sudo` is passwordless.

## Standard dev loop (edit → deploy → test)

1. **Edit** files on the Windows host (this directory).
2. **Commit + push** to `origin` (`github.com/schmiereck/ba_camera_bridge`). The local credential manager has push rights.
3. **Deploy on the Pi** with one command from the Windows/WSL side:
   ```bash
   ssh ubuntu@ubuntu1 '~/ros2_ws/src/ba_camera_bridge/scripts/deploy_ubuntu1.sh'
   ```
   That script does `git pull --ff-only`, `colcon build --packages-select ba_camera_bridge --symlink-install`, reinstalls the systemd unit if it changed, and `systemctl restart ba-camera-bridge`.
4. **Observe** with `journalctl -u ba-camera-bridge -f` on the Pi, or `ros2 topic hz /ba_overview_camera/image_raw/compressed` from WSL2.

Never edit files directly on the Pi — they would be overwritten by the next `git pull`. The Pi is a pure deploy target.

## Service control on the Pi

```bash
sudo systemctl start   ba-camera-bridge
sudo systemctl stop    ba-camera-bridge
sudo systemctl restart ba-camera-bridge
systemctl status       ba-camera-bridge
journalctl -u ba-camera-bridge -f
```

First-time install (once per fresh Pi): `~/ros2_ws/src/ba_camera_bridge/scripts/install_service.sh`.

## Build / run without the service (for debugging)

```bash
# on ubuntu1
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select ba_camera_bridge --symlink-install
source install/setup.bash
ROS_DOMAIN_ID=1 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  ros2 launch ba_camera_bridge overview_camera.launch.py
```

Stop any running systemd instance first (`sudo systemctl stop ba-camera-bridge`) — `/dev/video0` cannot be opened twice.

## Testing from the WSL2 laptop

ROS2 is **not** auto-sourced in the WSL shell, so:

```bash
wsl.exe -d Ubuntu-22.04 -- bash -c '
  source /opt/ros/humble/setup.bash
  export ROS_DOMAIN_ID=1
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  ros2 topic list | grep ba_overview_camera
  ros2 topic hz /ba_overview_camera/image_raw/compressed
'
```

## Files that matter

- `launch/overview_camera.launch.py` — the only entry point; loads `config/overview_camera.yaml`
- `config/overview_camera.yaml` — uses `/**` wildcard so it stays valid if node name/namespace changes
- `systemd/ba-camera-bridge.service` — sets env (domain 1 + cyclonedds) and sources both `/opt/ros/humble` and the overlay workspace
- `scripts/deploy_ubuntu1.sh` — the canonical deploy path; prefer it over running raw git/colcon commands
- `scripts/install_service.sh` — idempotent unit installer

## Related repositories (outside this repo)

These form the full arm-control stack and share the same ROS2 domain (`1` + CycloneDDS):

- `C:\Users\thomas\Projekte\BAArduinoController\` — Arduino servo bridge, also running on `ubuntu1`
- `C:\Users\thomas\Projekte\ba_arduino_controller_moveit_config\` — MoveIt config (runs on the WSL2 laptop)

See `Docs/PLAN_ROS2_CAMERA-Claude.md` for the full pipeline diagram and the rationale behind keeping the WLAN stream JPEG-compressed.
