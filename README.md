# DellTemp

DellTemp is a lightweight Ubuntu desktop app for monitoring CPU/GPU temperatures, fans, and other sensors. It includes a tray icon, configurable alerts, and CSV logging.

## Run from source

`PYTHONPATH=src` is relative to the **project directory**, not your home folder. From any directory:

```bash
sudo apt install python3-psutil python3-pyqt6 lm-sensors python3-pyqt6.qtcharts
sudo sensors-detect --auto
~/projects/delltemp/scripts/run.sh
```

Or `cd` into the repo first:

```bash
cd ~/projects/delltemp
PYTHONPATH=src python3 -m delltemp
```

Start minimized to the tray (also used by the “start on login” option):

```bash
~/projects/delltemp/scripts/run.sh --minimized
```

Settings live in `~/.config/delltemp/settings.json`. CSV logs, when enabled, go to `~/.local/share/delltemp/logs/`.

## Tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src python3 -m pytest tests
```

## Install (user launcher)

This puts the new UI on the GNOME/Ubuntu app grid without `sudo`. It also installs `~/.local/bin/delltemp`, which is ahead of the old `/usr/bin/delltemp` on PATH:

```bash
~/projects/delltemp/scripts/install_user.sh
```

To replace the system package instead:

```bash
./scripts/build_deb.sh
sudo dpkg -i build/delltemp_0.2.0_all.deb
```

## Build a .deb

```bash
./scripts/build_deb.sh
sudo dpkg -i build/delltemp_0.2.0_all.deb
```

The installer registers the desktop launcher in GNOME/Ubuntu (search for “DellTemp” in the app grid).
Graphs require `python3-pyqt6.qtcharts` (recommended). NVIDIA GPU rows require `nvidia-smi`.

## License

DellTemp is free software under the [GNU General Public License v3.0 or later](LICENSE) (`GPL-3.0-or-later`).

Copyright (C) 2026 XRFlow. Contact: support@xrflows.com.

PyQt6 is also GPL, so this license is the one that matches the UI toolkit when you distribute the app.

