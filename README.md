# DellTemp

DellTemp is a desktop app for monitoring CPU/GPU temperatures, fans, and other sensors on Linux and Windows. It includes a tray icon, configurable alerts, and CSV logging.

Copyright (C) 2026 XRFlow. Contact: support@xrflows.com.

## Linux (from source)

`PYTHONPATH=src` is relative to the **project directory**, not your home folder.

```bash
sudo apt install python3-psutil python3-pyqt6 lm-sensors python3-pyqt6.qtcharts
sudo sensors-detect --auto
~/projects/delltemp/scripts/run.sh
```

Or:

```bash
cd ~/projects/delltemp
PYTHONPATH=src python3 -m delltemp
```

User launcher (app grid, no sudo):

```bash
~/projects/delltemp/scripts/install_user.sh
```

Settings: `~/.config/delltemp/settings.json`. Logs: `~/.local/share/delltemp/logs/`.

## Linux .deb

Self-contained amd64 installer (bundles Python and Qt, no `python3-pyqt6` needed):

```bash
./scripts/build_deb_bundle.sh
sudo dpkg -i build/delltemp_0.3.0_amd64.deb
```

Thin package that uses system Python (smaller, needs `python3-pyqt6`):

```bash
./scripts/build_deb.sh
sudo dpkg -i build/delltemp_0.3.0_all.deb
```

GitHub Actions on `main` publishes the self-contained `.deb` plus Windows Setup.exe, MSI, and a portable zip.

## Windows

The app reads NVIDIA GPU sensors via `nvidia-smi` when present, ACPI thermal zones via WMI, and Libre Hardware Monitor / Open Hardware Monitor if one of those is installed.

Run from source (PowerShell):

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m delltemp
```

Settings: `%APPDATA%\DellTemp\settings.json`. Logs: `%LOCALAPPDATA%\DellTemp\logs`.

### Installers

GitHub Actions on `main` publishes:

- `DellTemp-<version>-Setup.exe` — Inno Setup installer (Start Menu, desktop shortcut, optional login start)
- `DellTemp-<version>.msi` — per-machine MSI
- `DellTemp-<version>-windows-portable.zip` — portable folder with `DellTemp.exe`

Build locally on a Windows machine:

```powershell
.\scripts\build_windows.ps1
```

That requires Python 3.12+, and optionally [Inno Setup 6](https://jrsoftware.org/isinfo.php) and [WiX Toolset v3](https://wixtoolset.org/) for the installers. The Windows app icon is `packaging/delltemp.ico`.

## Tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src python3 -m pytest tests
```

## License

DellTemp is free software under the [GNU General Public License v3.0 or later](LICENSE) (`GPL-3.0-or-later`).

PyQt6 is also GPL, so this license is the one that matches the UI toolkit when you distribute the app.
