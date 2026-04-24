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
Intrinsische Kalibrierung der Kamera mit einem Schachbrettmuster.

Der Solver (PnP) "projiziert" die 3D-Modellpunkte durch eine mathematische Linse auf das Bild. Wenn diese virtuelle Linse (fx, fy, cx, cy) nicht exakt der echten Linse Ihrer Pi-Kamera
entspricht, kann der Solver die Punkte niemals perfekt zur Deckung bringen. Er muss dann "schummeln" und die Kamera-Position leicht versetzen, was den Fehler in der Tiefe (Z) massiv erhöht.

Zur Strategie (Schachbrett-Bewegung):

Nur auf der Arbeitsfläche verschieben reicht leider nicht aus, um eine wirklich präzise Kalibrierung zu erhalten.

Hier ist das Profi-Rezept für gute Intrinsics:

1. Alle Bereiche abdecken (X/Y): Fahren Sie mit dem Schachbrett in alle vier Ecken des Bildes und in die Mitte. Die Linse verzerrt am Rand am stärksten, deshalb muss das Muster dort unbedingt
   gesehen werden.
2. Verschiedene Abstände (Size): Halten Sie das Muster mal so nah an die Kamera, dass es fast das ganze Bild füllt, und mal so weit weg, dass es nur noch ca. 1/4 des Bildes einnimmt.
3. Kippen ist extrem wichtig (Skew): Das ist der Punkt, den viele vergessen. Kippen Sie das Schachbrett leicht nach vorne/hinten und links/rechts (ca. 20-30 Grad). Nur durch diese
   perspektivische Verzerrung kann das Tool die Brennweite (fx, fy) exakt berechnen.
4. Drehen: Drehen Sie das Muster auch mal um 45 Grad (wie eine Raute), das hilft ebenfalls.

Wann aufhören?
Rechts im Tool sehen Sie vier Balken (X, Y, Size, Skew). Diese müssen alle grün werden.
* X/Y werden grün, wenn Sie alle Ecken besucht haben.
* Size wird grün, wenn nah und fern abgedeckt sind.
* Skew wird grün, wenn Sie das Muster ausreichend gekippt haben.

Sobald der Button "Calibrate" (der aktuell noch grau ist) klickbar wird, haben Sie genug Daten. Klicken Sie dann darauf und warten Sie (das Bild friert dann kurz ein), bis der Button "Save"
aktiv wird.


- Print out a chessboard pattern (9×7 squares, 8×6 inner corners, 25mm square size).

Necessary for later coordinate calculation (fx, fy, cx, cy):

### Kamera am Pi angeschlossen:
Sie können die Kamera auf der Pi lassen (wo sie hingehört) und das Rechenzentrum sowie die grafische Oberfläche (GUI) auf dem Laptop nutzen. Die Bilder werden einfach über das Netzwerk gestreamt.

So machen Sie die Kalibrierung über das Netzwerk:

Da der Datenstrom von der Pi zum Laptop meistens komprimiert ist (compressed), müssen wir ihn auf dem Laptop kurz "entpacken", damit das Kalibrier-Tool damit arbeiten kann.

Führen Sie diese Schritte auf dem Laptop aus:

1. Den Stream auf dem Laptop dekomprimieren (Terminal 1):

```bash
ros2 run image_transport republish compressed raw \
  --ros-args -r in/compressed:=/ba_overview_camera/image_raw/compressed \
  -r out:=/ba_overview_camera/image_raw
```

2. Drosseln auf 4 Hz (NEU):
Dieser Befehl nimmt das schnelle Bild und leitet nur 4 Bilder pro Sekunde an ein neues Topic weiter.

```bash
# Einmalig:
sudo apt update
sudo apt install ros-humble-topic-tools

ros2 run topic_tools throttle messages /ba_overview_camera/image_raw 4.0
```

3. Das Kalibrier-Tool (auf dem gedrosselten Topic) auf dem Laptop starten (Terminal 2):

```bash
# Auf Laptop

# (only onece):
sudo apt install ros-humble-camera-calibration

# Mit "Drosselung":
ros2 run camera_calibration cameracalibrator \
  --size 8x6 \
  --square 0.025 \
  image:=/ba_overview_camera/image_raw_throttle \
  camera:=/ba_overview_camera

# Ohne "Drosselung":
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
