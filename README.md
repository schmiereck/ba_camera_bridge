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

## Calibration

- Print out a chessboard pattern (9×7 squares, 8×6 inner corners, 25mm square size).

Necessary for later coordinate calculation (fx, fy, cx, cy):
```bash
# Auf Laptop
sudo apt install ros-humble-camera-calibration

ros2 run camera_calibration cameracalibrator \
  --size 8x6 \
  --square 0.025 \
  image:=/ba_overview_camera/image_raw \
  camera:=/ba_overview_camera
```

- Hold the pattern in front of the camera at different positions/angles
- When everything is "green": Calibrate, Save

```bash
cd /tmp
tar -xzf calibrationdata.tar.gz
```
- Result: `ost.yaml` with camera matrix

### In ROS2 `camera_info` Topic einbinden

Die `ost.yaml` wird im Paket unter `config/overview_camera_info.yaml` abgelegt und
vom `v4l2_camera_node` über `camera_info_url` geladen. `setup.py` installiert
automatisch alle `config/*.yaml` — an `setup.py` muss nichts angefasst werden.

1. **Datei ins Repo kopieren** (aus der WSL-Shell, in der die Kalibrierung lief):
   ```bash
   cp /tmp/ost.yaml \
      /mnt/c/Users/thomas/Projekte/ba_camera_bridge/config/overview_camera_info.yaml
   ```

2. **`camera_name` im YAML anpassen.** `cameracalibrator` speichert per Default
   `camera_name: narrow_stereo`. `v4l2_camera_node` (0.6.x) **hat keinen
   `camera_name`-Parameter** — der Name wird aus dem USB-Produkt-String abgeleitet
   und ist bei der C930e `logitech_webcam_c930e`. Passen YAML und Device-Name
   nicht zusammen, loggt `camera_info_manager` bei jedem Start einen
   `[<device>] does not match <yaml>` Warn. Die Intrinsics werden trotzdem
   geladen — nur der Log ist laut. Also:
   ```yaml
   # config/overview_camera_info.yaml — Kopfzeilen
   image_width: 640
   image_height: 480
   camera_name: logitech_webcam_c930e
   ```
   Bei einer anderen Kamera: den tatsächlichen Device-Namen aus dem Service-Log
   nach einem Restart ablesen:
   ```bash
   ssh ubuntu@ubuntu1 'journalctl -u ba-camera-bridge -n 100 --no-pager' \
     | grep -E "camera calibration URL|does not match"
   ```

3. **`config/overview_camera.yaml`** um die URL ergänzen (einmalig, existiert
   bereits — bei Re-Kalibrierung derselben Kamera überspringen):
   ```yaml
   camera_info_url: "package://ba_camera_bridge/config/overview_camera_info.yaml"
   ```

4. **Commit + push + deploy**:
   ```bash
   git add config/overview_camera.yaml config/overview_camera_info.yaml
   git commit -m "Update overview camera intrinsic calibration"
   git push
   ssh ubuntu@ubuntu1 '~/ros2_ws/src/ba_camera_bridge/scripts/deploy_ubuntu1.sh'
   ```

5. **Verifizieren**, dass `/ba_overview_camera/camera_info` echte Werte statt
   Null-Matrizen publiziert. Aus einer frischen WSL-Shell (ROS-Env muss komplett
   sein, `.bashrc` wird bei `bash -c` *nicht* gesourced):
   ```bash
   source /opt/ros/humble/setup.bash
   export ROS_DOMAIN_ID=1
   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
   export CYCLONEDDS_URI=file:///home/$USER/cyclonedds.xml
   ros2 topic echo --once /ba_overview_camera/camera_info
   ```
   `k` darf nicht nur Nullen enthalten, `d` sollte 5 Koeffizienten haben
   (plumb_bob). Im Service-Log darf **kein** `does not match` mehr auftauchen:
   ```bash
   ssh ubuntu@ubuntu1 \
     'journalctl -u ba-camera-bridge -n 50 --no-pager | grep "does not match"'
   # (keine Ausgabe = alles sauber)
   ```

**Bei erneuter Kalibrierung derselben Kamera** reicht es, Schritt 1 + 2 (nur den
`camera_name` in der neu kopierten Datei wieder auf `logitech_webcam_c930e`
setzen) + 4 + 5 zu durchlaufen. Schritt 3 ist schon erledigt.
