# SPDX-License-Identifier: GPL-3.0-or-later
from delltemp.app import _autostart_command, _desktop_quote, ensure_autostart


def test_autostart_uses_installed_binary(monkeypatch, tmp_path) -> None:
    binary = tmp_path / "delltemp"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setattr("delltemp.app.sys.platform", "linux")
    monkeypatch.setattr("delltemp.app.shutil.which", lambda name: str(binary) if name == "delltemp" else None)
    assert _autostart_command() == str(binary)


def test_desktop_quote_uses_desktop_spec() -> None:
    assert _desktop_quote("/usr/bin/delltemp") == "/usr/bin/delltemp"
    assert _desktop_quote("/home/user/My Src") == '"/home/user/My Src"'
    assert _desktop_quote('/tmp/say"hi') == '"/tmp/say\\"hi"'


def test_autostart_quotes_paths_with_spaces(monkeypatch, tmp_path) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr("delltemp.app.sys.platform", "linux")
    monkeypatch.setattr("delltemp.app.Path.home", lambda: home)
    monkeypatch.setattr(
        "delltemp.app.shutil.which",
        lambda name: "/opt/My Apps/delltemp" if name == "delltemp" else None,
    )
    ensure_autostart(True, minimized=True)
    text = (home / ".config" / "autostart" / "delltemp.desktop").read_text(
        encoding="utf-8"
    )
    assert 'Exec="/opt/My Apps/delltemp" --minimized' in text


def test_windows_autostart_writes_startup_bat(monkeypatch, tmp_path) -> None:
    from delltemp.app import _ensure_autostart_windows, _windows_startup_path

    roaming = tmp_path / "Roaming"
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setattr("delltemp.app.sys.executable", str(tmp_path / "python.exe"))
    _ensure_autostart_windows(True, minimized=True)
    path = _windows_startup_path()
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "--minimized" in text
    _ensure_autostart_windows(False, minimized=True)
    assert not path.exists()


def test_ensure_autostart_honors_minimized(monkeypatch, tmp_path) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr("delltemp.app.sys.platform", "linux")
    monkeypatch.setattr("delltemp.app.Path.home", lambda: home)
    monkeypatch.setattr("delltemp.app.shutil.which", lambda name: "/usr/bin/delltemp")

    ensure_autostart(True, minimized=True)
    path = home / ".config" / "autostart" / "delltemp.desktop"
    text = path.read_text(encoding="utf-8")
    assert "Exec=/usr/bin/delltemp --minimized" in text

    ensure_autostart(True, minimized=False)
    text = path.read_text(encoding="utf-8")
    assert "Exec=/usr/bin/delltemp\n" in text
    assert "--minimized" not in text

    ensure_autostart(False, minimized=True)
    assert not path.exists()
