# SPDX-License-Identifier: GPL-3.0-or-later
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

import psutil


@dataclass(frozen=True)
class SensorReading:
    category: str
    name: str
    value: float
    unit: str
    source: str
    group: str
    identity: str = ""


_NON_JSON_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_+-])[+-]?(?:NaN|Infinity|Inf)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def collect_readings() -> List[SensorReading]:
    psutil_temps = _safe_collect(_from_psutil_temps)
    psutil_fans = _safe_collect(_from_psutil_fans)
    lm_readings = _safe_collect(_from_lm_sensors)
    nvidia_readings = _safe_collect(_from_nvidia_smi)

    readings: List[SensorReading] = []
    lm_categories = {reading.category for reading in lm_readings}
    if "Temperature" not in lm_categories:
        readings.extend(psutil_temps)
    if "Fan" not in lm_categories:
        readings.extend(psutil_fans)
    readings.extend(lm_readings)
    readings.extend(nvidia_readings)
    return [_normalize_reading(reading) for reading in _dedupe(readings)]


def reading_key(reading: SensorReading) -> str:
    identity = (reading.identity or "").strip()
    base = f"{reading.source}|{reading.group}|{reading.category}|{reading.name}"
    if identity:
        return f"{base}|{identity}"
    return base


def celsius_to_fahrenheit(celsius: float) -> float:
    return (float(celsius) * 9 / 5) + 32


def format_sensor_value(value: float, unit: str) -> tuple[str, str]:
    value = float(value)
    if unit == "°C":
        fahrenheit = celsius_to_fahrenheit(value)
        return (f"{value:.1f} / {fahrenheit:.1f}", "°C/°F")
    if value.is_integer():
        return f"{int(value)}", unit
    return f"{value:.1f}", unit


def sanitize_lm_sensors_json(text: str) -> str:
    return _NON_JSON_NUMBER.sub("null", text)


def parse_lm_sensors_payload(payload: dict) -> List[SensorReading]:
    readings: List[SensorReading] = []
    if not isinstance(payload, dict):
        return readings
    for chip, features in payload.items():
        if not isinstance(features, dict):
            continue
        for feature_name, feature in features.items():
            if not isinstance(feature, dict):
                continue
            label = feature.get(f"{feature_name}_label")
            for key, value in feature.items():
                if not _looks_like_input(key, value):
                    continue
                current = _finite_float(value)
                if current is None:
                    continue
                category, unit = _category_for_key(key)
                display = label or feature_name
                readings.append(
                    SensorReading(
                        category=category,
                        name=humanize(display),
                        value=current,
                        unit=unit,
                        source="lm-sensors",
                        group=humanize(chip),
                        identity=str(key),
                    )
                )
    return readings


def parse_nvidia_smi_csv(text: str) -> List[SensorReading]:
    readings: List[SensorReading] = []
    for index, line in enumerate((text or "").strip().splitlines()):
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3:
            continue
        fan = parts[-1]
        temp = parts[-2]
        name = ", ".join(parts[:-2]).strip()
        if temp and temp.upper() != "N/A":
            current = _finite_float(temp)
            if current is not None:
                readings.append(
                    SensorReading(
                        category="GPU Temperature",
                        name=humanize(name),
                        value=current,
                        unit="°C",
                        source="nvidia-smi",
                        group=f"GPU {index}",
                        identity="temperature.gpu",
                    )
                )
        if fan and fan.upper() != "N/A":
            current = _finite_float(fan)
            if current is not None:
                readings.append(
                    SensorReading(
                        category="GPU Fan",
                        name=humanize(name),
                        value=current,
                        unit="%",
                        source="nvidia-smi",
                        group=f"GPU {index}",
                        identity="fan.speed",
                    )
                )
    return readings


def _safe_collect(
    collector: Callable[[], Iterable[SensorReading]],
) -> List[SensorReading]:
    try:
        return list(collector())
    except Exception:
        return []


def _normalize_reading(reading: SensorReading) -> SensorReading:
    category = reading.category.strip() if isinstance(reading.category, str) else ""
    name = reading.name.strip() if isinstance(reading.name, str) else ""
    unit = reading.unit.strip() if isinstance(reading.unit, str) else ""
    source = reading.source.strip() if isinstance(reading.source, str) else ""
    group = reading.group.strip() if isinstance(reading.group, str) else ""
    identity = reading.identity.strip() if isinstance(reading.identity, str) else ""
    if not category:
        category = "Sensor"
    if not name:
        name = category
    if not source:
        source = "unknown"
    return SensorReading(
        category=category,
        name=name,
        value=reading.value,
        unit=unit,
        source=source,
        group=group,
        identity=identity,
    )


def _from_psutil_temps() -> Iterable[SensorReading]:
    try:
        temps = psutil.sensors_temperatures(fahrenheit=False) or {}
    except (OSError, AttributeError, TypeError):
        return []

    readings: List[SensorReading] = []
    for group, entries in temps.items():
        for index, entry in enumerate(entries or []):
            current = _finite_float(getattr(entry, "current", None))
            if current is None:
                continue
            label = getattr(entry, "label", None) or "Temperature"
            readings.append(
                SensorReading(
                    category="Temperature",
                    name=humanize(label),
                    value=current,
                    unit="°C",
                    source="psutil",
                    group=humanize(group),
                    identity=str(index),
                )
            )
    return readings


def _from_psutil_fans() -> Iterable[SensorReading]:
    try:
        fans = psutil.sensors_fans() or {}
    except (OSError, AttributeError, TypeError):
        return []

    readings: List[SensorReading] = []
    for group, entries in fans.items():
        for index, entry in enumerate(entries or []):
            current = _finite_float(getattr(entry, "current", None))
            if current is None:
                continue
            label = getattr(entry, "label", None) or "Fan"
            readings.append(
                SensorReading(
                    category="Fan",
                    name=humanize(label),
                    value=current,
                    unit="RPM",
                    source="psutil",
                    group=humanize(group),
                    identity=str(index),
                )
            )
    return readings


def _from_lm_sensors() -> Iterable[SensorReading]:
    if not shutil.which("sensors"):
        return []

    try:
        result = subprocess.run(
            ["sensors", "-j"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    stdout = (result.stdout or "").strip()
    if not stdout:
        return []

    try:
        payload = json.loads(sanitize_lm_sensors_json(stdout))
    except json.JSONDecodeError:
        return []
    return parse_lm_sensors_payload(payload)


def _looks_like_input(key: str, value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(float(value)):
        return False
    return key.endswith("_input")


def _finite_float(value: object) -> Optional[float]:
    try:
        current = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(current):
        return None
    return current


def _category_for_key(key: str) -> tuple[str, str]:
    if key.startswith("temp"):
        return "Temperature", "°C"
    if key.startswith("fan"):
        return "Fan", "RPM"
    if key.startswith("power"):
        return "Power", "W"
    if key.startswith("intrusion"):
        return "Sensor", ""
    if key.startswith("in"):
        return "Voltage", "V"
    if key.startswith("curr"):
        return "Current", "A"
    if key.startswith("humidity"):
        return "Humidity", "%"
    return "Sensor", ""


def _from_nvidia_smi() -> Iterable[SensorReading]:
    if not shutil.which("nvidia-smi"):
        return []

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,fan.speed",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    stdout = (result.stdout or "").strip()
    if not stdout:
        return []
    return parse_nvidia_smi_csv(stdout)


def _dedupe(readings: List[SensorReading]) -> List[SensorReading]:
    seen = set()
    unique: List[SensorReading] = []
    for reading in readings:
        key = reading_key(reading)
        if key in seen:
            continue
        seen.add(key)
        unique.append(reading)
    return unique


def humanize(text: str) -> str:
    raw = "" if text is None else str(text)
    cleaned = re.sub(r"[_\\-]+", " ", raw).strip()
    if not cleaned:
        return raw.strip()
    return " ".join(word.capitalize() for word in cleaned.split())
