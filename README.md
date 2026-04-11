# Service on Pi

sudo systemctl start/stop/restart/status ba-camera-bridge
journalctl -u ba-camera-bridge -f

# Deploy-Loop after Edit

The deployment script automatically detects changes to the systemd unit and reinstalls it:
```bash
# local
git commit -am "…" && git push
# Pi
ssh ubuntu@ubuntu1 '~/ros2_ws/src/ba_camera_bridge/scripts/deploy_ubuntu1.sh'
```

Your one-liner to verify it yourself in a fresh WSL shell:
```bash
ros2 topic hz /ba_overview_camera/image_raw/compressed
# or visual
rviz2  # → Add → Image → Topic: /ba_overview_camera/image_raw/compressed
```