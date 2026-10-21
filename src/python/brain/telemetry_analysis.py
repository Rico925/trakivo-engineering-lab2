"""CSV telemetry ingestion and lap comparison for educational analysis.

This module normalizes common channel names but never infers units or claims a
simulation/measurement is validated. Distance alignment is linear interpolation
onto a shared distance grid, not a full motorsport-grade synchronization engine.
"""
from __future__ import annotations

import csv
import io
import math
import re
from typing import Any

MAX_ROWS = 250_000
ALIASES = {
    "time_s": {"time", "time_s", "time (s)", "timestamp", "elapsed_time", "elapsed time", "session_time"},
    "distance_m": {"distance", "distance_m", "distance (m)", "lap_distance", "lap distance", "dist"},
    "speed_kmh": {"speed", "speed_kmh", "speed (km/h)", "speed_kph", "velocity_kmh", "vehicle_speed"},
    "throttle_pct": {"throttle", "throttle_pct", "throttle (%)", "accelerator", "accelerator_pedal", "throttle_position"},
    "brake_pct": {"brake", "brake_pct", "brake (%)", "brake_pressure_pct", "brake_position"},
    "lap": {"lap", "lap_number", "lap number", "lapno", "lap_no", "lapindex"},
    "latitude": {"latitude", "lat", "gps_latitude", "gps_lat"},
    "longitude": {"longitude", "lon", "long", "gps_longitude", "gps_lon"},
}


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower().replace("_", " "))


def _number(value: str, field: str, row_num: int) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        number = float(value.strip())
    except ValueError as exc:
        raise ValueError(f"Row {row_num}: '{value}' is not numeric for {field}.") from exc
    if not math.isfinite(number):
        raise ValueError(f"Row {row_num}: non-finite value in {field}.")
    return number


def parse_telemetry_csv(csv_text: str) -> dict[str, Any]:
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV file is empty.")
    if len(csv_text.encode("utf-8")) > 10 * 1024 * 1024:
        raise ValueError("CSV exceeds the 10 MB prototype import limit.")
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValueError("CSV must include a header row.")
    original_headers = [h.strip() for h in reader.fieldnames if h and h.strip()]
    normalized: dict[str, str] = {}
    for header in original_headers:
        candidate = _key(header)
        for canonical, aliases in ALIASES.items():
            if candidate in {_key(alias) for alias in aliases}:
                normalized[canonical] = header
                break
    if "speed_kmh" not in normalized:
        raise ValueError("Could not identify a speed column. Use a header such as speed_kmh or speed_kph.")
    if "distance_m" not in normalized and "time_s" not in normalized:
        raise ValueError("CSV must include a distance column (recommended) or a time column.")

    rows: list[dict[str, float | None]] = []
    for row_num, raw in enumerate(reader, start=2):
        if not any((value or "").strip() for value in raw.values()):
            continue
        if len(rows) >= MAX_ROWS:
            raise ValueError(f"CSV exceeds the {MAX_ROWS:,}-row prototype limit.")
        item: dict[str, float | None] = {}
        for canonical, header in normalized.items():
            item[canonical] = _number(raw.get(header, "") or "", canonical, row_num)
        if item.get("speed_kmh") is None:
            raise ValueError(f"Row {row_num}: speed is missing.")
        if item.get("distance_m") is None and item.get("time_s") is None:
            raise ValueError(f"Row {row_num}: both distance and time are missing.")
        rows.append(item)
    if len(rows) < 2:
        raise ValueError("At least two valid telemetry rows are required.")

    # Infer lap boundaries only from a distance reset; never pretend this is a timing-system lap marker.
    lap_source = "provided lap column" if "lap" in normalized else "distance resets (inferred)"
    lap_id = 1
    previous_distance: float | None = None
    for item in rows:
        distance = item.get("distance_m")
        if "lap" in normalized:
            raw_lap = item.get("lap")
            if raw_lap is None:
                raise ValueError("Lap column contains a missing value.")
            item["lap_id"] = raw_lap
        else:
            if distance is not None and previous_distance is not None and distance < previous_distance - 1.0:
                lap_id += 1
            item["lap_id"] = float(lap_id)
        if distance is not None:
            previous_distance = distance

    lap_groups: dict[str, list[dict[str, float | None]]] = {}
    for item in rows:
        lap_groups.setdefault(str(item["lap_id"]), []).append(item)
    # Stable numeric-ish sorting where possible; retain input order otherwise.
    lap_ids = list(lap_groups)
    try:
        lap_ids.sort(key=float)
    except ValueError:
        pass

    laps = []
    for lap_id_value in lap_ids:
        lap_rows = lap_groups[lap_id_value]
        distances = [r["distance_m"] for r in lap_rows if r.get("distance_m") is not None]
        speeds = [r["speed_kmh"] for r in lap_rows if r.get("speed_kmh") is not None]
        laps.append({
            "lap_id": lap_id_value,
            "samples": len(lap_rows),
            "distance_start_m": round(min(distances), 3) if distances else None,
            "distance_end_m": round(max(distances), 3) if distances else None,
            "mean_speed_kmh": round(sum(speeds) / len(speeds), 3),
            "max_speed_kmh": round(max(speeds), 3),
        })
    channels = [name for name in ("time_s", "distance_m", "speed_kmh", "throttle_pct", "brake_pct", "latitude", "longitude") if name in normalized]
    return {
        "schema_version": "trakivo-telemetry-1.0",
        "evidence_label": "MEASURED (user-imported; source not independently verified)",
        "lap_detection": lap_source,
        "source_headers": original_headers,
        "normalized_channels": channels,
        "row_count": len(rows),
        "lap_count": len(laps),
        "laps": laps,
        "rows": rows,
    }


def _interpolate(points: list[tuple[float, float]], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    lo, hi = 0, len(points) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if points[mid][0] <= x:
            lo = mid
        else:
            hi = mid
    x0, y0 = points[lo]
    x1, y1 = points[hi]
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def compare_laps(parsed: dict[str, Any], reference_lap: str, comparison_lap: str, grid_points: int = 101) -> dict[str, Any]:
    if reference_lap == comparison_lap:
        raise ValueError("Choose two different laps to compare.")
    rows = parsed["rows"]
    def points_for(lap_id: str, channel: str) -> list[tuple[float, float]]:
        points = [(float(r["distance_m"]), float(r[channel])) for r in rows
                  if str(r["lap_id"]) == lap_id and r.get("distance_m") is not None and r.get(channel) is not None]
        points.sort(key=lambda p: p[0])
        deduped: list[tuple[float, float]] = []
        for point in points:
            if deduped and point[0] == deduped[-1][0]:
                deduped[-1] = point
            else:
                deduped.append(point)
        return deduped

    ref_speed = points_for(reference_lap, "speed_kmh")
    cmp_speed = points_for(comparison_lap, "speed_kmh")
    if len(ref_speed) < 2 or len(cmp_speed) < 2:
        raise ValueError("Distance-aligned comparison needs at least two distance/speed samples per lap.")
    start = max(ref_speed[0][0], cmp_speed[0][0])
    end = min(ref_speed[-1][0], cmp_speed[-1][0])
    if end <= start:
        raise ValueError("The selected laps do not share an overlapping distance range.")
    grid = [start + (end - start) * i / (grid_points - 1) for i in range(grid_points)]
    ref_values = [_interpolate(ref_speed, x) for x in grid]
    cmp_values = [_interpolate(cmp_speed, x) for x in grid]
    deltas = [b - a for a, b in zip(ref_values, cmp_values)]
    output: dict[str, Any] = {
        "schema_version": parsed["schema_version"],
        "evidence_label": "CALCULATED from user-imported telemetry",
        "alignment": "linear interpolation on shared distance grid",
        "reference_lap": reference_lap,
        "comparison_lap": comparison_lap,
        "overlap_distance_m": {"start": round(start, 3), "end": round(end, 3)},
        "sample_count": grid_points,
        "summary": {
            "reference_mean_speed_kmh": round(sum(ref_values) / len(ref_values), 3),
            "comparison_mean_speed_kmh": round(sum(cmp_values) / len(cmp_values), 3),
            "mean_speed_delta_kmh": round(sum(deltas) / len(deltas), 3),
            "max_positive_speed_delta_kmh": round(max(deltas), 3),
            "max_negative_speed_delta_kmh": round(min(deltas), 3),
        },
        "trace": [{"distance_m": round(x, 3), "reference_speed_kmh": round(a, 3), "comparison_speed_kmh": round(b, 3), "delta_speed_kmh": round(d, 3)} for x, a, b, d in zip(grid, ref_values, cmp_values, deltas)],
        "limitations": "Distance alignment uses linear interpolation and only compares overlapping distance. Lap detection, units, sensor calibration, vehicle identity and source authenticity are not independently verified. No lap-time or setup recommendation is inferred.",
    }
    for channel in ("throttle_pct", "brake_pct"):
        ref = points_for(reference_lap, channel)
        cmp = points_for(comparison_lap, channel)
        if len(ref) >= 2 and len(cmp) >= 2:
            a = [_interpolate(ref, x) for x in grid if ref[0][0] <= x <= ref[-1][0] and cmp[0][0] <= x <= cmp[-1][0]]
            b = [_interpolate(cmp, x) for x in grid if ref[0][0] <= x <= ref[-1][0] and cmp[0][0] <= x <= cmp[-1][0]]
            if a and b:
                output["summary"][f"reference_mean_{channel}"] = round(sum(a) / len(a), 3)
                output["summary"][f"comparison_mean_{channel}"] = round(sum(b) / len(b), 3)
    return output
